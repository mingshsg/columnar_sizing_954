"""Generate EVIDENCE_INDEX.md: an index of every configuration, sizing, validation,
ingestion and run-record file in the project, with links and JSON checks.

The index is built from the files on disk. A file that has no description is
listed as "(undescribed)" so it is never left out silently.

Usage: python3 scripts/build_evidence_index.py
"""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STREAMS = {
    "logs-otel.logsdb-bench": ("logs", "logsdb"),
    "logs-otel.columnar-bench": ("logs", "logsdb_columnar"),
    "traces-otel.logsdb-bench": ("traces", "logsdb"),
    "traces-otel.columnar-bench": ("traces", "logsdb_columnar"),
    "metrics-otel.tsds-bench": ("metrics", "time_series (TSDS)"),
}

CONFIG_KINDS = {
    "data_stream": "Data stream definition as returned by the cluster",
    "index_template": "Index template the benchmark created (`bench-<data stream>`)",
    "settings": "Settings set on the backing index (user-set only)",
    "effective_settings": "Effective settings including defaults that apply",
    "mapping": "Field mapping of the backing index",
}


def size_of(path):
    n = os.path.getsize(path)
    for unit, size in (("GiB", 1024 ** 3), ("MiB", 1024 ** 2), ("KiB", 1024)):
        if n >= size:
            return "%.2f %s" % (n / size, unit)
    return "%d B" % n


def json_status(path):
    if not path.endswith(".json"):
        return "-"
    try:
        with open(path, encoding="utf-8") as fh:
            json.load(fh)
        return "valid"
    except Exception as e:  # noqa: BLE001
        return "INVALID: %s" % e


def row(rel, description):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return "| `%s` | %s | - | MISSING |" % (rel, description)
    return "| [`%s`](%s) | %s | %s | %s |" % (rel, rel, description, size_of(path), json_status(path))


def listed(rel_dir, predicate=lambda n: True):
    base = os.path.join(ROOT, rel_dir)
    if not os.path.isdir(base):
        return []
    return sorted(n for n in os.listdir(base) if os.path.isfile(os.path.join(base, n)) and predicate(n))


def section(title, intro, rows):
    out = ["## " + title, ""]
    if intro:
        out += [intro, ""]
    out += ["| File | What it contains | Size | JSON check |", "|---|---|---:|---|"]
    out += rows
    out.append("")
    return out


def main():
    lines = ["# Evidence index: Elasticsearch 9.5.5 OTel storage benchmark", ""]
    lines.append("Generated: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    lines.append("")
    lines.append("Every file below was produced by the benchmark scripts or captured from the cluster. JSON files are pretty-printed and checked to parse. Start with the sizing summary, then use the configuration files to confirm what was applied.")
    lines.append("")

    lines += ["## Start here", ""]
    lines += [
        "- [`results/sizing_summary.json`](results/sizing_summary.json): readable sizing summary (logsdb vs logsdb_columnar vs TSDS)",
        "- [`results/summary.md`](results/summary.md): full results report with samples",
        "- [`results/field_size_report.md`](results/field_size_report.md): field-by-field storage comparison",
        "- [`results/config_report.md`](results/config_report.md): settings and mappings in one document",
        "- [`README.md`](README.md): how the benchmark was built, how to re-run it, and caveats",
        "",
    ]

    lines += ["## 1. Configuration applied to the cluster", ""]
    lines += ["Captured from the live cluster after load. One set of files per data stream.", ""]
    lines += ["| Data stream | Signal | Mode | Files |", "|---|---|---|---|"]
    for ds, (signal, mode) in STREAMS.items():
        links = ", ".join("[%s](results/config/%s.%s.json)" % (k, ds, k) for k in CONFIG_KINDS)
        lines.append("| `%s` | %s | %s | %s |" % (ds, signal, mode, links))
    lines.append("")
    rows = []
    for ds in STREAMS:
        for kind, desc in CONFIG_KINDS.items():
            rel = "results/config/%s.%s.json" % (ds, kind)
            rows.append(row(rel, "%s: %s" % (ds, desc)))
    lines += section("1a. Configuration files", "", rows)

    lines += section("2. Sizing", "Storage numbers and their breakdown.", [
        row("results/sizing_summary.json", "Readable sizing summary with human-readable sizes, field types, per-structure breakdown, per-field comparison (logs, traces) and per-field metrics, plus the store reconciliation"),
        row("results/es_report.json", "Verification results per data stream: counts, field coverage, round-trip, store size, compression, mapping and settings checks"),
        row("results/field_size_report.md", "Field-by-field disk usage report (markdown)"),
    ] + [
        row("results/field_usage/%s.disk_usage.json" % ds, "Raw index disk usage output from Elasticsearch (`_disk_usage`) for %s" % ds)
        for ds in ("logs-otel.logsdb-bench", "logs-otel.columnar-bench", "traces-otel.logsdb-bench", "traces-otel.columnar-bench", "metrics-otel.tsds-bench")
    ])

    lines += section("3. Validation of the generated data", "Full-content checks on every generated document. Pass/fail is in each file.", [
        row("results/validation_%s.json" % s, "Full-file validation result for %s (%s)" % (s, desc))
        for s, desc in (("logs", "149,147,666 documents"), ("traces", "154,100,082 spans"), ("metrics", "274,280,000 documents"))
    ] + [
        row("samples/validation_%s.sample.json" % s, "Validation of the 5 sample documents for %s" % s)
        for s in ("logs", "traces", "metrics")
    ])

    lines += section("4. Sample documents", "Real documents from the generated files. `.json` is the readable form; `.ndjson` is the original one-per-line form.", [
        row("samples/%s.sample.json" % s, "Five sample %s documents, pretty-printed" % s) for s in ("logs", "traces", "metrics")
    ] + [
        row("samples/%s.sample.ndjson" % s, "Five sample %s documents, one per line (original form)" % s) for s in ("logs", "traces", "metrics")
    ])

    load_rows = []
    for ds in STREAMS:
        rel = "results/load_%s.json" % ds
        if os.path.exists(os.path.join(ROOT, rel)):
            load_rows.append(row(rel, "Ingestion result for %s: documents indexed, failures, rate" % ds))
    lines += section("5. Ingestion", "", load_rows)

    run_rows = [
        row("results/status.json", "Pipeline completion status"),
        row("logs/pipeline.log", "Full log of the pipeline run (generate, validate, setup, load, verify, report)"),
        row("logs/gen_logs.out", "Generator output for logs (document count, bytes, timestamps)"),
        row("logs/gen_traces.out", "Generator output for traces"),
        row("logs/gen_metrics.out", "Generator output for metrics"),
        row("logs/pull_es956.log", "Record of the failed pull of Elasticsearch 9.5.6 (not in the registry), which led to using 9.5.5"),
    ]
    lines += section("6. Run records", "", run_rows)

    script_rows = []
    for name in listed("scripts", lambda n: n.endswith((".py", ".sh"))):
        script_rows.append(row("scripts/" + name, SCRIPT_DESC.get(name, "(undescribed)")))
    lines += section("7. Scripts", "", script_rows)

    lines += ["## Reproducing the evidence", ""]
    lines += [
        "1. Run `scripts/run_pipeline.sh` (see README).",
        "2. Capture disk usage for the four logs and traces indices with `POST <index>/_disk_usage?run_expensive_tasks=true`, saving each response as `results/field_usage/<data stream>.disk_usage.json`.",
        "3. Run `scripts/field_report.py`, `scripts/sizing_summary.py`, `scripts/config_report.py`, `scripts/format_json.py` and `scripts/build_evidence_index.py`.",
        "",
    ]
    out = os.path.join(ROOT, "EVIDENCE_INDEX.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


SCRIPT_DESC = {
    "schema.py": "OTel field definitions, index mappings and data stream names",
    "gen_otel.py": "Deterministic generator for logs, traces and metrics (NDJSON)",
    "validate_files.py": "Full-content validator: schema, formats, enums, counters",
    "setup_es.py": "Creates index templates and data streams; verifies settings",
    "load_bulk.py": "Bulk loader that writes the generated documents to a data stream",
    "verify_es.py": "Post-load checks: counts, mappings, settings, field coverage, round-trip, store size",
    "field_report.py": "Field-by-field storage comparison (markdown)",
    "field_types.py": "Field types from the captured mappings; used by the field and sizing reports",
    "verify_field_report.py": "Independent check that every number in field_size_report.md matches the raw disk usage output",
    "sizing_summary.py": "Readable sizing summary (JSON)",
    "config_report.py": "Configuration reference (markdown with embedded JSON)",
    "report.py": "Main results report (summary.md)",
    "format_json.py": "Pretty-prints every JSON file and checks it is unchanged",
    "build_evidence_index.py": "Builds this index",
    "run_pipeline.sh": "End-to-end pipeline with checkpoints",
    "common.py": "Shared helpers: .env loading and authenticated session",
}


if __name__ == "__main__":
    sys.exit(main())
