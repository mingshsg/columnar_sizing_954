"""Field-by-field storage comparison: logsdb vs logsdb_columnar.

Reads the index disk usage output (POST <index>/_disk_usage?run_expensive_tasks=true)
saved under results/field_usage/ and writes results/field_size_report.md.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FU = os.path.join(RES, "field_usage")

PAIRS = [
    ("logs", "logs-otel.logsdb-bench", "logs-otel.columnar-bench"),
    ("traces", "traces-otel.logsdb-bench", "traces-otel.columnar-bench"),
]


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
    path = os.path.join(FU, ".ds-%s-2026.10.22-000001.json" % ds)
    with open(path) as fh:
        body = json.load(fh)
    for k, v in body.items():
        if k != "_shards":
            return v
    raise SystemExit("no index entry in %s" % path)


def field_bytes(entry, key):
    if key == "total":
        return entry.get("total_in_bytes", 0)
    if key == "inverted":
        return entry.get("inverted_index", {}).get("total_in_bytes", 0)
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


def field_rows(a, b):
    fa, fb = a.get("fields", {}), b.get("fields", {})
    names = sorted(set(fa) | set(fb), key=lambda n: -(field_bytes(fa.get(n, {}), "total") + field_bytes(fb.get(n, {}), "total")))
    out = [
        "| Field | logsdb total | columnar total | Difference | Columnar vs logsdb | logsdb inverted | columnar inverted | logsdb doc values | columnar doc values | logsdb stored | columnar stored |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
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
        out.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            n, fmt(ta), fmt(tb), fmt(tb - ta), pct(tb, ta), fmt(ia), fmt(ib), fmt(da), fmt(db), fmt(sa), fmt(sb)))
    out.append("| **Total (fields)** | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | **%s** | | |" % (
        fmt(tot[0]), fmt(tot[1]), fmt(tot[1] - tot[0]), pct(tot[1], tot[0]), fmt(tot[2]), fmt(tot[3]), fmt(tot[4]), fmt(tot[5])))
    return out


def main():
    lines = ["# Field-level storage comparison: logsdb vs logsdb_columnar", ""]
    lines.append("Source: Elasticsearch 9.5.5, index disk usage API (`_disk_usage?run_expensive_tasks=true`) on the primary shards after force-merge to one segment per shard.")
    lines.append("Both modes use the same raw data (100 GiB per signal), the same mappings, 2 shards, 0 replicas, default sort (`host.name`, `@timestamp`) and the default `best_compression` codec.")
    lines.append("")
    lines.append("Per-field bytes are the field's share of each on-disk structure. Synthetic `_source` is rebuilt from doc values and stored fields, so the doc values and stored fields columns show what the source costs. Fields that are absent in one mode show as `-` in that column.")
    lines.append("")

    for signal, ds_a, ds_b in PAIRS:
        a, b = load_index(ds_a), load_index(ds_b)
        lines.append("## %s" % signal.capitalize())
        lines.append("")
        lines.append("Index: `%s` (logsdb) and `%s` (logsdb_columnar)." % (ds_a, ds_b))
        lines.append("")
        lines.extend(component_rows(a, b))
        saving = (1 - b["store_size_in_bytes"] / a["store_size_in_bytes"]) * 100
        lines.append("")
        lines.append("logsdb_columnar uses %.1f%% less disk than logsdb for %s." % (saving, signal))
        lines.append("")
        lines.append("### Per-field breakdown (sorted by combined size)")
        lines.append("")
        lines.extend(field_rows(a, b))
        lines.append("")

    out = os.path.join(RES, "field_size_report.md")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
