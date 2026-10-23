"""Build results/summary.md from the generation, validation, load and verification outputs."""
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "data")


def load(path):
    with open(path) as fh:
        return json.load(fh)


def gib(n):
    return "%.2f GiB" % (n / 1024 ** 3)


def main():
    lines = []
    add = lines.append
    add("# OpenTelemetry compression benchmark: Elasticsearch 9.5.5")
    add("")
    add("Generated: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    add("")

    es = load(os.path.join(RES, "es_report.json")) if os.path.exists(os.path.join(RES, "es_report.json")) else None
    add("## Cluster")
    add("")
    if es:
        add("- Elasticsearch version: %s" % es["cluster"]["version"])
        add("- License: %s" % es["cluster"]["license"])
        add("- Overall verification: %s" % ("PASSED" if es.get("all_passed") else "FAILED"))
    add("")

    add("## 1. Generated data (raw NDJSON, one document per line)")
    add("")
    add("| Signal | Documents | Raw bytes | Bytes/doc | First timestamp | Last timestamp |")
    add("|---|---:|---:|---:|---|---|")
    for sig in ("logs", "traces", "metrics"):
        mp = os.path.join(DATA, sig + ".ndjson.meta.json")
        if os.path.exists(mp):
            m = load(mp)
            add("| %s | %s | %s | %.1f | %s | %s |" % (sig, format(m["docs"], ","), gib(m["bytes"]), m["bytes"] / m["docs"], m["first_timestamp"], m["last_timestamp"]))
    add("")

    add("## 2. Validation (full content, every document)")
    add("")
    add("| Signal | Docs checked | Docs with errors | Errors | Result |")
    add("|---|---:|---:|---:|---|")
    for sig in ("logs", "traces", "metrics"):
        p = os.path.join(RES, "validation_%s.json" % sig)
        if os.path.exists(p):
            v = load(p)
            add("| %s | %s | %d | %d | %s |" % (sig, format(v["docs_checked"], ","), v["docs_with_errors"], v["error_count"], "PASS" if v["passed"] else "FAIL"))
    add("")

    add("## 3. Ingestion")
    add("")
    add("| Data stream | Mode | Docs indexed | Failed | Seconds | Docs/s | MB/s (raw) |")
    add("|---|---|---:|---:|---:|---:|---:|")
    for name in sorted(f for f in os.listdir(RES) if f.startswith("load_") and f.endswith(".json")):
        l = load(os.path.join(RES, name))
        mode = "time_series" if "tsds" in l["data_stream"] else ("logsdb_columnar" if "columnar" in l["data_stream"] else "logsdb")
        add("| %s | %s | %s | %d | %.0f | %.0f | %.1f |" % (l["data_stream"], mode, format(l["docs_indexed"], ","), l["docs_failed"], l["seconds"], l["docs_per_second"], l["mb_per_second"]))
    add("")

    if es:
        add("## 4. Storage and compression (after refresh + force-merge to 1 segment)")
        add("")
        add("Compression ratio = raw NDJSON bytes / primary store bytes.")
        add("")
        add("| Data stream | Docs | Raw size | Store size (primary) | Compression ratio | Bytes/doc on disk | Round-trip identical |")
        add("|---|---:|---:|---:|---:|---:|---|")
        for d in es["data_streams"]:
            rt = d.get("round_trip", {})
            add("| %s | %s | %s | %s | %.2fx | %.1f | %s |" % (
                d["data_stream"], format(d["es_doc_count"], ","), gib(d["raw_bytes"]), gib(d["primary_store_bytes"]),
                d["compression_ratio"] or 0, d["bytes_per_doc_on_disk"] or 0,
                "yes" if rt.get("docs_identical") else "no"))
        add("")
        add("### Checks per data stream")
        add("")
        for d in es["data_streams"]:
            status = "PASS" if d["passed"] else "FAIL"
            add("- **%s**: %s (mode %s, %s docs)" % (d["data_stream"], status, d["expected_mode"], format(d["es_doc_count"], ",")))
            for p in d.get("problems", []):
                add("  - problem: %s" % p)
        add("")
        add("### Storage comparison (logs and traces, same raw data)")
        add("")
        by = {d["data_stream"]: d for d in es["data_streams"]}
        for a, b, label in (("logs-otel.logsdb-bench", "logs-otel.columnar-bench", "logs"),
                            ("traces-otel.logsdb-bench", "traces-otel.columnar-bench", "traces")):
            if a in by and b in by and by[a]["primary_store_bytes"] and by[b]["primary_store_bytes"]:
                ratio = by[a]["primary_store_bytes"] / by[b]["primary_store_bytes"]
                add("- %s: logsdb_columnar is %.2fx smaller than logsdb (%s vs %s)" % (
                    label, ratio, gib(by[b]["primary_store_bytes"]), gib(by[a]["primary_store_bytes"])))
        add("")

    add("## Sample documents (reference)")
    add("")
    add("Two documents per signal, taken from the generated files (first line and one line from the middle of the file). All 15 samples pass the schema validation. Full samples are in `samples/`.")
    add("")
    for sig in ("logs", "traces", "metrics"):
        p = os.path.join(ROOT, "samples", sig + ".sample.ndjson")
        if os.path.exists(p):
            with open(p) as fh:
                rows = [l for l in fh if l.strip()]
            for idx in (0, 3):
                if idx < len(rows):
                    add("### %s sample %d" % (sig, idx + 1 if idx == 0 else 2))
                    add("")
                    add("```json")
                    add(json.dumps(json.loads(rows[idx]), indent=2))
                    add("```")
                    add("")
    add("## Detailed reports")
    add("")
    add("- `field_size_report.md`: field-by-field storage comparison, logsdb vs logsdb_columnar")
    add("- `config_report.md`: index templates, settings, effective settings and mappings for every data stream")
    add("- `../README.md`: how the benchmark was built and how to re-run it, with caveats")
    add("")

    add("## Notes")
    add("")
    add("- 100 GiB = raw NDJSON document bytes (no bulk action lines), per the agreed definition.")
    add("- Mappings: `body.text`, `status.message` and `attributes.exception.message` are `match_only_text` with no keyword subfield.")
    add("- Logs and traces use synthetic `_source` in both logsdb and logsdb_columnar.")
    add("- Metrics use a time series data stream (TSDS) with 10k series at a 10 s interval.")
    add("- ES maps dotted OTel attribute names (for example `service.name`) as nested objects. The round-trip check normalizes both sides the same way.")

    out = os.path.join(RES, "summary.md")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
