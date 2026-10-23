"""Build results/sizing_summary.json: a readable sizing summary for the benchmark.

Combines the verification output (results/es_report.json) with the index disk
usage output (results/field_usage/*.disk_usage.json). Every size is given in
bytes and as a human-readable string.

Usage: python3 scripts/sizing_summary.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FU = os.path.join(RES, "field_usage")

TEXT_FIELDS = ["body.text", "attributes.exception.message", "status.message"]


def human(n):
    if n is None:
        return None
    sign = "-" if n < 0 else ""
    n = abs(n)
    for unit, size in (("GiB", 1024 ** 3), ("MiB", 1024 ** 2), ("KiB", 1024)):
        if n >= size:
            return "%s%.2f %s" % (sign, n / size, unit)
    return "%s%d B" % (sign, n)


def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def disk_usage(ds):
    body = load_json(os.path.join(FU, "%s.disk_usage.json" % ds))
    index = next(v for k, v in body.items() if k != "_shards")
    return index


def structures(index):
    a = index["all_fields"]
    return {
        "store_size": index["store_size_in_bytes"],
        "all_fields_total": a["total_in_bytes"],
        "inverted_index": a["inverted_index"]["total_in_bytes"],
        "doc_values": a["doc_values_in_bytes"],
        "stored_fields": a["stored_fields_in_bytes"],
        "points": a["points_in_bytes"],
    }


def per_field(index):
    out = {}
    for name, f in index.get("fields", {}).items():
        out[name] = {
            "total": f.get("total_in_bytes", 0),
            "inverted_index": f.get("inverted_index", {}).get("total_in_bytes", 0),
            "doc_values": f.get("doc_values_in_bytes", 0),
            "stored_fields": f.get("stored_fields_in_bytes", 0),
        }
    return out


def with_human(d):
    return {k: {"bytes": v, "human": human(v)} for k, v in d.items()}


def signal_block(signal, ds_a, ds_b):
    ia, ib = disk_usage(ds_a), disk_usage(ds_b)
    sa, sb = structures(ia), structures(ib)
    saving = (1 - sb["store_size"] / sa["store_size"]) * 100

    fa, fb = per_field(ia), per_field(ib)
    fields = []
    for name in sorted(set(fa) | set(fb), key=lambda n: -(fa.get(n, {}).get("total", 0) + fb.get(n, {}).get("total", 0))):
        ta, tb = fa.get(name, {}).get("total", 0), fb.get(name, {}).get("total", 0)
        fields.append({
            "field": name,
            "logsdb_bytes": ta,
            "logsdb_human": human(ta),
            "columnar_bytes": tb,
            "columnar_human": human(tb),
            "difference_bytes": tb - ta,
            "difference_human": human(tb - ta),
        })

    text = []
    for name in TEXT_FIELDS:
        if name not in fa and name not in fb:
            continue
        va = fa.get(name, {}).get("total", 0) + fa.get(name + "._original", {}).get("total", 0)
        vb = fb.get(name, {}).get("total", 0)
        text.append({
            "field": name,
            "logsdb_bytes_including_original_copy": va,
            "logsdb_human": human(va),
            "columnar_bytes": vb,
            "columnar_human": human(vb),
        })

    return {
        "logsdb": {"data_stream": ds_a, "structures": with_human(sa)},
        "logsdb_columnar": {"data_stream": ds_b, "structures": with_human(sb)},
        "columnar_saving_percent": round(saving, 1),
        "text_fields": text,
        "fields_sorted_by_combined_size": fields,
    }


def main():
    report = load_json(os.path.join(RES, "es_report.json"))
    by_ds = {d["data_stream"]: d for d in report["data_streams"]}

    data_streams = []
    for d in report["data_streams"]:
        data_streams.append({
            "data_stream": d["data_stream"],
            "kind": d["kind"],
            "expected_mode": d["expected_mode"],
            "documents": d["es_doc_count"],
            "raw_bytes": d["raw_bytes"],
            "raw_human": human(d["raw_bytes"]),
            "primary_store_bytes": d["primary_store_bytes"],
            "primary_store_human": human(d["primary_store_bytes"]),
            "compression_ratio": d["compression_ratio"],
            "bytes_per_document_on_disk": d["bytes_per_doc_on_disk"],
            "checks_passed": d["passed"],
        })

    summary = {
        "title": "Sizing summary: Elasticsearch 9.5.5, logsdb vs logsdb_columnar vs TSDS",
        "how_to_read": {
            "raw_bytes": "Raw NDJSON bytes of the generated documents (bulk action lines excluded). This is the 100 GiB reference.",
            "primary_store_bytes": "Primary shard store size after refresh and force-merge to one segment per shard.",
            "compression_ratio": "raw_bytes / primary_store_bytes.",
            "structures": "On-disk structures from the index disk usage API. A field's bytes are its share of each structure.",
            "columnar_saving_percent": "How much smaller logsdb_columnar is than logsdb, as a percentage of the logsdb size.",
            "original_copy": "logsdb keeps a copy of match_only_text values (`<field>._original`) for synthetic _source. Columnar stores the text in doc values instead.",
        },
        "cluster": report["cluster"],
        "all_data_streams_passed": report.get("all_passed"),
        "data_streams": data_streams,
        "comparison": {
            "logs": signal_block("logs", "logs-otel.logsdb-bench", "logs-otel.columnar-bench"),
            "traces": signal_block("traces", "traces-otel.logsdb-bench", "traces-otel.columnar-bench"),
        },
        "metrics_tsds": {
            "data_stream": "metrics-otel.tsds-bench",
            "primary_store_bytes": by_ds["metrics-otel.tsds-bench"]["primary_store_bytes"],
            "primary_store_human": human(by_ds["metrics-otel.tsds-bench"]["primary_store_bytes"]),
            "compression_ratio": by_ds["metrics-otel.tsds-bench"]["compression_ratio"],
        },
    }

    out = os.path.join(RES, "sizing_summary.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
