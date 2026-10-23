"""Field-by-field storage report.

- logs and traces: logsdb vs logsdb_columnar, per field, with the field type.
- metrics: TSDS only (there is no columnar counterpart), per field, with the field type.

Reads results/field_usage/*.disk_usage.json (Elasticsearch index disk usage) and
the mappings in results/config/*.mapping.json. Writes results/field_size_report.md.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import field_types as ft  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FU = os.path.join(RES, "field_usage")

PAIRS = [
    ("logs", "logs-otel.logsdb-bench", "logs-otel.columnar-bench"),
    ("traces", "traces-otel.logsdb-bench", "traces-otel.columnar-bench"),
]
METRICS = "metrics-otel.tsds-bench"
TEXT_FIELDS = ["body.text", "attributes.exception.message", "status.message"]


def fmt(n):
    if n is None:
        return "-"
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1024 ** 2:
        return "%s%.2f MiB" % (sign, n / 1024 ** 2)
    if n >= 1024:
        return "%s%.1f KiB" % (sign, n / 1024)
    return "%s%d B" % (sign, n)


def pct(new, base):
    if not base:
        return "-"
    return "%+.1f%%" % ((new - base) / base * 100)


def load_index(ds):
    with open(os.path.join(FU, "%s.disk_usage.json" % ds), encoding="utf-8") as fh:
        body = json.load(fh)
    return next(v for k, v in body.items() if k != "_shards")


def field_bytes(entry, key):
    if key == "total":
        return entry.get("total_in_bytes", 0)
    if key == "inverted":
        return entry.get("inverted_index", {}).get("total_in_bytes", 0)
    if key == "points":
        return entry.get("points_in_bytes", 0)
    return entry.get(key + "_in_bytes", 0)


def component_rows(a, b):
    rows = [
        ("Store size (primary, on disk)", a["store_size_in_bytes"], b["store_size_in_bytes"]),
        ("All fields total", a["all_fields"]["total_in_bytes"], b["all_fields"]["total_in_bytes"]),
        ("Inverted index", a["all_fields"]["inverted_index"]["total_in_bytes"], b["all_fields"]["inverted_index"]["total_in_bytes"]),
        ("Doc values", a["all_fields"]["doc_values_in_bytes"], b["all_fields"]["doc_values_in_bytes"]),
        ("Stored fields", a["all_fields"]["stored_fields_in_bytes"], b["all_fields"]["stored_fields_in_bytes"]),
        ("Points (BKD)", a["all_fields"]["points_in_bytes"], b["all_fields"]["points_in_bytes"]),
    ]
    out = ["| Component | logsdb | logsdb_columnar | Difference | Columnar vs logsdb |", "|---|---:|---:|---:|---:|"]
    for name, x, y in rows:
        out.append("| %s | %s | %s | %s | %s |" % (name, fmt(x), fmt(y), fmt(y - x), pct(y, x)))
    return out


def mapping_for(signal):
    return ft.load_mapping({"logs": "logs-otel.logsdb-bench", "traces": "traces-otel.logsdb-bench", "metrics": METRICS}[signal])


def field_rows(a, b, mapped):
    fa, fb = a.get("fields", {}), b.get("fields", {})
    names = sorted(set(fa) | set(fb), key=lambda n: -(field_bytes(fa.get(n, {}), "total") + field_bytes(fb.get(n, {}), "total")))
    out = [
        "| Field | Type | logsdb total | columnar total | Difference | Columnar vs logsdb | logsdb inverted | columnar inverted | logsdb doc values | columnar doc values | logsdb stored | columnar stored |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tot = [0, 0, 0, 0, 0, 0]
    for n in names:
        ea, eb = fa.get(n, {}), fb.get(n, {})
        ta, tb = field_bytes(ea, "total"), field_bytes(eb, "total")
        ia, ib = field_bytes(ea, "inverted"), field_bytes(eb, "inverted")
        da, db = field_bytes(ea, "doc_values"), field_bytes(eb, "doc_values")
        sa, sb = field_bytes(ea, "stored_fields"), field_bytes(eb, "stored_fields")
        for i, v in enumerate([ta, tb, ia, ib, da, db]):
            tot[i] += v
        out.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            n, ft.type_of(n, mapped), fmt(ta), fmt(tb), fmt(tb - ta), pct(tb, ta), fmt(ia), fmt(ib), fmt(da), fmt(db), fmt(sa), fmt(sb)))
    out.append("| **Total (fields)** | | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | | |" % (
        fmt(tot[0]), fmt(tot[1]), fmt(tot[1] - tot[0]), pct(tot[1], tot[0]), fmt(tot[2]), fmt(tot[3]), fmt(tot[4]), fmt(tot[5])))
    return out


def text_rows(a, b, mapped):
    fa, fb = a.get("fields", {}), b.get("fields", {})
    out = [
        "| Text field | Type | logsdb (field + `._original`) | columnar (field) | Difference | Columnar vs logsdb |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name in TEXT_FIELDS:
        if name not in fa and name not in fb:
            continue
        va = field_bytes(fa.get(name, {}), "total") + field_bytes(fa.get(name + "._original", {}), "total")
        vb = field_bytes(fb.get(name, {}), "total")
        out.append("| `%s` | %s | %s | %s | %s | %s |" % (name, ft.type_of(name, mapped), fmt(va), fmt(vb), fmt(vb - va), pct(vb, va)))
    return out


def metrics_section(idx, mapped):
    a = idx["all_fields"]
    lines = [
        "## Metrics (TSDS)",
        "",
        "Index: `%s`. There is no columnar counterpart for metrics, so this section shows one storage mode only." % METRICS,
        "",
        "| Component | Size |",
        "|---|---:|",
        "| Store size (primary, on disk) | %s |" % fmt(idx["store_size_in_bytes"]),
        "| All fields total | %s |" % fmt(a["total_in_bytes"]),
        "| Inverted index | %s |" % fmt(a["inverted_index"]["total_in_bytes"]),
        "| Doc values | %s |" % fmt(a["doc_values_in_bytes"]),
        "| Stored fields | %s |" % fmt(a["stored_fields_in_bytes"]),
        "| Points (BKD) | %s |" % fmt(a["points_in_bytes"]),
        "",
        "> **Store size note:** the verification report (`results/es_report.json`, 22 Oct) recorded a metrics store of 1,903,391,531 bytes (1.77 GiB). The current store is %s and stays the same after flush and force-merge. The cause of the earlier value is not determined. See `results/sizing_summary.json` (`store_reconciliation`)." % fmt(idx["store_size_in_bytes"]),
        "",
        "### Per-field breakdown (sorted by size)",
        "",
        "| Field | Type | Total | Share of all fields | Inverted index | Doc values | Stored fields | Points |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    fields = idx.get("fields", {})
    total_all = a["total_in_bytes"] or 1
    tot = [0, 0, 0, 0, 0]
    for n in sorted(fields, key=lambda n: -field_bytes(fields[n], "total")):
        e = fields[n]
        t = field_bytes(e, "total")
        vals = [t, field_bytes(e, "inverted"), field_bytes(e, "doc_values"), field_bytes(e, "stored_fields"), field_bytes(e, "points")]
        for i, v in enumerate(vals):
            tot[i] += v
        lines.append("| `%s` | %s | %s | %.2f%% | %s | %s | %s | %s |" % (
            n, ft.type_of(n, mapped), fmt(t), t / total_all * 100, fmt(vals[1]), fmt(vals[2]), fmt(vals[3]), fmt(vals[4])))
    lines.append("| **Total (fields)** | | **%s** | **%.2f%%** | **%s** | **%s** | **%s** | **%s** |" % (
        fmt(tot[0]), tot[0] / total_all * 100, fmt(tot[1]), fmt(tot[2]), fmt(tot[3]), fmt(tot[4])))
    lines.append("")
    return lines


def main():
    lines = ["# Field-level storage report: Elasticsearch 9.5.5", ""]
    lines.append("Source: index disk usage API (`_disk_usage?run_expensive_tasks=true`) on the primary shards after force-merge to one segment per shard, and the mappings captured from the cluster (`results/config/`).")
    lines.append("")
    lines.append("Both logs and traces use the same raw data (100 GiB per signal), the same mappings, 2 shards, 0 replicas, default sort (`host.name`, `@timestamp`) and the default `best_compression` codec.")
    lines.append("")
    lines.append("**Field type** is the mapped type from the cluster. Entries in parentheses are dimensions or metric types for TSDS, and the Elasticsearch-internal entries.")
    lines.append("")
    lines.append("Per-field bytes are the field's share of each on-disk structure. Synthetic `_source` is rebuilt from doc values and stored fields, so the doc values and stored fields columns show what the source costs. Fields that are absent in one mode show as `-` in that column.")
    lines.append("")
    lines.append("Internal fields that appear in the per-field tables:")
    lines.append("")
    lines.append("- `<field>._original` (logsdb only): logsdb keeps the original text of each `match_only_text` field so synthetic `_source` can be rebuilt. Columnar mode stores the same text in doc values instead, so compare the text fields in the text table rather than the `._original` rows alone.")
    lines.append("- `<field>.counts` (columnar only): per-field value counts stored as separate columns.")
    lines.append("- `_field_names` (logsdb only): Elasticsearch's field-name metadata.")
    lines.append("")

    for signal, ds_a, ds_b in PAIRS:
        a, b = load_index(ds_a), load_index(ds_b)
        mapped = mapping_for(signal)
        lines.append("## %s" % signal.capitalize())
        lines.append("")
        lines.append("Index: `%s` (logsdb) and `%s` (logsdb_columnar)." % (ds_a, ds_b))
        lines.append("")
        lines.extend(component_rows(a, b))
        saving = (1 - b["store_size_in_bytes"] / a["store_size_in_bytes"]) * 100
        lines.append("")
        lines.append("logsdb_columnar uses %.1f%% less disk than logsdb for %s." % (saving, signal))
        lines.append("")
        lines.append("### Text fields (`match_only_text`), including their `._original` copy")
        lines.append("")
        lines.extend(text_rows(a, b, mapped))
        lines.append("")
        lines.append("### Per-field breakdown (sorted by combined size)")
        lines.append("")
        lines.extend(field_rows(a, b, mapped))
        lines.append("")

    lines.extend(metrics_section(load_index(METRICS), mapping_for("metrics")))

    out = os.path.join(RES, "field_size_report.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
