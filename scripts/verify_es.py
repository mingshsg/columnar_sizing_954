"""Verify the loaded data on Elasticsearch and measure storage.

For each data stream:
  1. refresh + force-merge to 1 segment (same end state for every index)
  2. verify index settings (index.mode, synthetic source, shards, TSDS window)
  3. verify mapping (match_only_text without subfields, TSDS dimensions/metrics)
  4. verify document count == generated count, and failed docs == 0
  5. verify required fields exist on every document (ES-side field checks)
  6. round-trip check: documents in a time window read back via synthetic
     _source must equal the generated documents (canonical JSON comparison)
  7. measure primary store size and compression ratio (raw NDJSON bytes / store)

Usage:
  python3 verify_es.py --results results/es_report.json [--skip-forcemerge] [--window-seconds 5]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import es_session  # noqa: E402
import schema as S  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

TARGETS = [
    {"ds": S.LOGS_LOGSDB, "file": "logs.ndjson", "kind": "logs", "mode": "logsdb", "required": [
        "@timestamp", "body.text", "severity_text", "severity_number", "resource.attributes.service.name",
        "resource.attributes.host.name", "resource.attributes.k8s.pod.name", "scope.name", "scope.version"]},
    {"ds": S.LOGS_COLUMNAR, "file": "logs.ndjson", "kind": "logs", "mode": "logsdb_columnar", "required": [
        "@timestamp", "body.text", "severity_text", "severity_number", "resource.attributes.service.name",
        "resource.attributes.host.name", "resource.attributes.k8s.pod.name", "scope.name", "scope.version"]},
    {"ds": S.TRACES_LOGSDB, "file": "traces.ndjson", "kind": "traces", "mode": "logsdb", "required": [
        "@timestamp", "trace_id", "span_id", "name", "kind", "duration", "status.code", "scope.name",
        "resource.attributes.service.name"]},
    {"ds": S.TRACES_COLUMNAR, "file": "traces.ndjson", "kind": "traces", "mode": "logsdb_columnar", "required": [
        "@timestamp", "trace_id", "span_id", "name", "kind", "duration", "status.code", "scope.name",
        "resource.attributes.service.name"]},
    {"ds": S.METRICS_TSDS, "file": "metrics.ndjson", "kind": "metrics", "mode": "time_series", "required": [
        "@timestamp", "attributes.stream", "resource.attributes.service.name", "resource.attributes.host.name",
        "resource.attributes.k8s.pod.name", "resource.attributes.k8s.namespace.name", "resource.attributes.cloud.region"]},
]


def canon(doc):
    return json.dumps(expand_dots(doc), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def expand_dots(node):
    """ES maps dotted field names (service.name) as nested objects (service: {name: ...}).
    Expand dotted keys the same way so generated and retrieved documents compare equal."""
    if isinstance(node, list):
        return [expand_dots(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        v = expand_dots(v)
        parts = k.split(".")
        cur = out
        for p in parts[:-1]:
            nxt = cur.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[p] = nxt
            cur = nxt
        leaf = parts[-1]
        if isinstance(v, dict) and isinstance(cur.get(leaf), dict):
            cur[leaf].update(v)
        else:
            cur[leaf] = v
    return out


def digest(s):
    return hashlib.md5(s.encode("utf-8")).digest()


def iso_to_dt(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc) if "." in s else datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def dt_to_iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (d.microsecond // 1000)


def get_meta(file):
    with open(os.path.join(DATA_DIR, file + ".meta.json")) as fh:
        return json.load(fh)


def field_exists_count(s, base, ds, field):
    r = s.post(base + "/%s/_count" % ds, data=json.dumps({"query": {"exists": {"field": field}}}))
    r.raise_for_status()
    return r.json()["count"]


def check_settings(s, base, ds, expect):
    settings = s.get(base + "/%s/_settings?include_defaults=true&flat_settings=false" % ds).json()
    out = {}
    problems = []
    for idx, body in settings.items():
        st = body["settings"]["index"]
        d = body["defaults"]["index"]
        mode = st.get("mode") or d.get("mode")
        src = (st.get("mapping", {}).get("source", {}) or {}).get("mode") or (d.get("mapping", {}).get("source", {}) or {}).get("mode")
        shards = st.get("number_of_shards")
        out[idx] = {"mode": mode, "source_mode": src, "shards": shards, "replicas": st.get("number_of_replicas")}
        if mode != expect["mode"]:
            problems.append("%s: mode %s != %s" % (idx, mode, expect["mode"]))
        if str(shards) != str(S.SHARDS):
            problems.append("%s: shards %s != %s" % (idx, shards, S.SHARDS))
        if str(src).lower() != "synthetic":
            problems.append("%s: source.mode %s != synthetic" % (idx, src))
        if expect["kind"] == "metrics":
            ts = st.get("time_series", {})
            out[idx]["time_series"] = ts
            out[idx]["routing_path"] = st.get("routing_path")
            if not ts:
                problems.append("%s: no time_series window" % idx)
    return out, problems


def check_mapping(s, base, ds, kind):
    m = s.get(base + "/%s/_mapping" % ds).json()
    props = next(iter(m.values()))["mappings"]
    problems = []
    flat = {}

    def walk(node, prefix):
        for k, v in (node.get("properties") or {}).items():
            path = prefix + k
            if "type" in v:
                flat[path] = v
            if "properties" in v:
                walk(v, path + ".")
    walk(props, "")
    text_fields = ["body.text", "attributes.exception.message", "status.message"]
    for f in text_fields:
        spec = flat.get(f)
        if spec is None:
            continue
        if spec.get("type") != "match_only_text":
            problems.append("%s type %s != match_only_text" % (f, spec.get("type")))
        if "fields" in spec:
            problems.append("%s has subfields %s (must be none)" % (f, list(spec["fields"].keys())))
    if kind == "metrics":
        for f in ["attributes.stream", "resource.attributes.service.name", "resource.attributes.host.name", "resource.attributes.k8s.pod.name"]:
            if not flat.get(f, {}).get("time_series_dimension"):
                problems.append("%s is not a time_series_dimension" % f)
        for f in S.METRIC_GAUGES | S.METRIC_COUNTERS:
            spec = flat.get(f, {})
            want = "gauge" if f in S.METRIC_GAUGES else "counter"
            if spec.get("time_series_metric") != want:
                problems.append("%s time_series_metric %s != %s" % (f, spec.get("time_series_metric"), want))
    return {"text_fields": {f: flat.get(f, {}).get("type") for f in text_fields if f in flat}}, problems


def round_trip(s, base, ds, file_path, window_seconds, kind):
    with open(file_path, "rb") as fh:
        first = json.loads(fh.readline())
    t0 = iso_to_dt(first["@timestamp"])
    t1 = t0 + timedelta(seconds=window_seconds)
    es_hashes = Counter()
    scroll_body = {"size": 5000, "query": {"range": {"@timestamp": {"gte": dt_to_iso(t0), "lte": dt_to_iso(t1), "format": "strict_date_optional_time"}}}, "sort": ["_doc"]}
    r = s.post(base + "/%s/_search?scroll=5m" % ds, data=json.dumps(scroll_body))
    r.raise_for_status()
    body = r.json()
    scroll_id = body.get("_scroll_id")
    es_total = 0
    while True:
        hits = body["hits"]["hits"]
        if not hits:
            break
        for h in hits:
            es_hashes[digest(canon(h["_source"]))] += 1
            es_total += 1
        r = s.post(base + "/_search/scroll", data=json.dumps({"scroll": "5m", "scroll_id": scroll_id}))
        r.raise_for_status()
        body = r.json()
        scroll_id = body.get("_scroll_id", scroll_id)
    s.delete(base + "/_search/scroll", data=json.dumps({"scroll_id": scroll_id}))

    file_hashes = Counter()
    file_docs = 0
    scan_until = t1 + timedelta(seconds=2)
    with open(file_path, "rb") as fh:
        for raw in fh:
            doc = json.loads(raw)
            ts = iso_to_dt(doc["@timestamp"])
            if ts > scan_until:
                break
            if t0 <= ts <= t1:
                file_hashes[digest(canon(doc))] += 1
                file_docs += 1
    missing = sum((file_hashes - es_hashes).values())
    extra = sum((es_hashes - file_hashes).values())
    return {
        "window_start": dt_to_iso(t0), "window_end": dt_to_iso(t1),
        "es_docs_in_window": es_total, "file_docs_in_window": file_docs,
        "docs_identical": es_total == file_docs and missing == 0 and extra == 0,
        "missing_in_es": missing, "unexpected_in_es": extra,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--skip-forcemerge", action="store_true")
    ap.add_argument("--window-seconds", type=float, default=5.0)
    ap.add_argument("--skip-round-trip", action="store_true")
    args = ap.parse_args()

    s, base = es_session()
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "cluster": {}, "data_streams": []}
    report["cluster"]["version"] = s.get(base + "/").json()["version"]["number"]
    report["cluster"]["license"] = s.get(base + "/_license").json()["license"]["type"]
    all_ok = True

    for t in TARGETS:
        ds, file_path = t["ds"], os.path.join(DATA_DIR, t["file"])
        meta = get_meta(t["file"])
        entry = {"data_stream": ds, "kind": t["kind"], "expected_mode": t["mode"], "raw_file": t["file"],
                 "raw_bytes": meta["bytes"], "generated_docs": meta["docs"], "problems": []}
        print("==", ds, flush=True)
        s.post(base + "/%s/_refresh" % ds)
        if not args.skip_forcemerge:
            t0 = time.time()
            r = s.post(base + "/%s/_forcemerge?max_num_segments=1" % ds, params={"wait_for_completion": "true"})
            entry["forcemerge_seconds"] = round(time.time() - t0, 1)
            entry["forcemerge_status"] = r.status_code
            s.post(base + "/%s/_refresh" % ds)

        settings, problems = check_settings(s, base, ds, t)
        entry["settings"] = settings
        entry["problems"] += problems
        mapping_info, problems = check_mapping(s, base, ds, t["kind"])
        entry["mapping"] = mapping_info
        entry["problems"] += problems

        count = s.get(base + "/%s/_count" % ds).json()["count"]
        entry["es_doc_count"] = count
        if count != meta["docs"]:
            entry["problems"].append("doc count %d != generated %d" % (count, meta["docs"]))

        required = {f: field_exists_count(s, base, ds, f) for f in t["required"]}
        entry["required_field_coverage"] = {f: {"docs_with_field": c, "complete": c == count} for f, c in required.items()}
        for f, c in required.items():
            if c != count:
                entry["problems"].append("required field %s present on %d of %d docs" % (f, c, count))

        stats = s.get(base + "/%s/_stats/store" % ds).json()["_all"]["primaries"]
        store = stats["store"]["size_in_bytes"]
        entry["primary_store_bytes"] = store
        entry["compression_ratio"] = round(meta["bytes"] / store, 3) if store else None
        entry["bytes_per_doc_on_disk"] = round(store / count, 2) if count else None
        entry["raw_bytes_per_doc"] = round(meta["bytes"] / meta["docs"], 2)

        if t["kind"] == "logs":
            hits = s.post(base + "/%s/_search" % ds, data=json.dumps({"size": 0, "query": {"match": {"body.text": {"query": "persisted for customer", "operator": "and"}}}, "track_total_hits": True})).json()
            entry["text_search_match_hits"] = hits["hits"]["total"]["value"]
            if hits["hits"]["total"]["value"] == 0:
                entry["problems"].append("match_only_text search returned no hits")

        if not args.skip_round_trip:
            entry["round_trip"] = round_trip(s, base, ds, file_path, args.window_seconds, t["kind"])
            if not entry["round_trip"]["docs_identical"]:
                entry["problems"].append("round-trip mismatch: %s" % json.dumps(entry["round_trip"]))

        entry["passed"] = not entry["problems"]
        all_ok = all_ok and entry["passed"]
        report["data_streams"].append(entry)
        print(json.dumps({k: entry[k] for k in ("data_stream", "es_doc_count", "compression_ratio", "bytes_per_doc_on_disk", "passed")}), flush=True)
        with open(args.results, "w") as fh:
            json.dump(report, fh, indent=2)

    report["all_passed"] = all_ok
    with open(args.results, "w") as fh:
        json.dump(report, fh, indent=2)
    print("ALL PASSED" if all_ok else "SOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
