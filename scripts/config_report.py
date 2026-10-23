"""Config reference: data streams, index templates, settings and mappings.

Reads results/config/*.json (captured from the live cluster) and writes
results/config_report.md with a comparison table and the full JSON for each
data stream.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
CFG = os.path.join(RES, "config")

DATA_STREAMS = [
    "logs-otel.logsdb-bench",
    "logs-otel.columnar-bench",
    "traces-otel.logsdb-bench",
    "traces-otel.columnar-bench",
    "metrics-otel.tsds-bench",
]


def read(name):
    with open(os.path.join(CFG, name)) as fh:
        return json.load(fh)


def effective(ds):
    body = read("%s.effective_settings.json" % ds)
    idx = next(iter(body.values()))
    s = idx.get("settings", {}).get("index", {})
    d = idx.get("defaults", {}).get("index", {})
    sort = s.get("sort") or d.get("sort") or {}
    fields = sort.get("field", [])
    if isinstance(fields, str):
        fields = [fields]
    return {
        "index.mode": s.get("mode") or d.get("mode") or "-",
        "source.mode": (s.get("mapping", {}).get("source", {}) or {}).get("mode", "-"),
        "shards": s.get("number_of_shards", "-"),
        "codec": s.get("codec") or d.get("codec", "-"),
        "sort": ", ".join(fields) if fields else "-",
        "routing_path": ", ".join(s.get("routing_path") or d.get("routing_path") or []) or "-",
        "look_back_time": s.get("look_back_time") or d.get("look_back_time", "-"),
    }


def user_settings(ds):
    body = read("%s.settings.json" % ds)
    idx = next(iter(body.values()))
    return idx.get("settings", {})


def main():
    lines = ["# Configuration reference: Elasticsearch 9.5.5 benchmark", ""]
    lines.append("Captured from the live cluster after the load and verify stages. Effective values come from `GET <data stream>/_settings?include_defaults=true`. Full JSON for every data stream is in the collapsible sections below.")
    lines.append("")

    lines.append("## Comparison of effective settings")
    lines.append("")
    keys = ["index.mode", "source.mode", "shards", "codec", "sort", "routing_path", "look_back_time"]
    lines.append("| Setting | " + " | ".join("`%s`" % d for d in DATA_STREAMS) + " |")
    lines.append("|---|" + "---|" * len(DATA_STREAMS))
    eff = {d: effective(d) for d in DATA_STREAMS}
    for k in keys:
        lines.append("| %s | " % k + " | ".join(str(eff[d][k]) for d in DATA_STREAMS) + " |")
    lines.append("")
    lines.append("Replicas: 0 for all data streams. The logs and traces columnar streams use `index.mode: logsdb_columnar`; the logsdb streams use `logsdb`; metrics uses `time_series`.")
    lines.append("")

    for ds in DATA_STREAMS:
        lines.append("## `%s`" % ds)
        lines.append("")
        lines.append("### Index template (`bench-%s`)" % ds)
        lines.append("")
        lines.append("<details><summary>JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(read("%s.index_template.json" % ds), indent=2, sort_keys=True))
        lines.append("```")
        lines.append("</details>")
        lines.append("")
        lines.append("### Settings set by the benchmark (user-set, from `_settings`)")
        lines.append("")
        lines.append("<details><summary>JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(read("%s.settings.json" % ds), indent=2, sort_keys=True))
        lines.append("```")
        lines.append("</details>")
        lines.append("")
        lines.append("### Effective settings (with defaults that apply)")
        lines.append("")
        lines.append("<details><summary>JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(read("%s.effective_settings.json" % ds), indent=2, sort_keys=True))
        lines.append("```")
        lines.append("</details>")
        lines.append("")
        lines.append("### Mapping")
        lines.append("")
        lines.append("<details><summary>JSON</summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(read("%s.mapping.json" % ds), indent=2, sort_keys=True))
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    out = os.path.join(RES, "config_report.md")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
