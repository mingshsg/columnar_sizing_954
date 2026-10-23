"""Full-content validation of generated NDJSON files.

Checks every document against the OTel-shaped schema used by the benchmark:
required fields present, value types/formats correct, enum values valid,
trace/span id lengths, severity mapping, metric dimensions and value domains,
and counter monotonicity per series (including across chunk boundaries).

Usage:
  python3 validate_files.py logs data/logs.ndjson --workers 4 --out results/validation_logs.json
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import (  # noqa: E402
    LOG_SEVERITY, METRIC_STREAMS, STREAM_FIELDS, SPAN_KINDS, STATUS_CODES,
    METRIC_COUNTERS, METRIC_GAUGES,
)

TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
HEX32 = re.compile(r"^[0-9a-f]{32}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
ZERO32 = "0" * 32
ZERO16 = "0" * 16
RESOURCE_REQUIRED = ["service.name", "service.version", "host.name", "k8s.pod.name", "k8s.namespace.name", "cloud.region", "deployment.environment.name"]
MAX_SAMPLES = 5


class Acc:
    def __init__(self):
        self.docs = 0
        self.bad_docs = 0
        self.errors = Counter()
        self.samples = defaultdict(list)
        self.ts_min = None
        self.ts_max = None
        self.values = Counter()

    def err(self, rule, line_no, detail):
        self.errors[rule] += 1
        if len(self.samples[rule]) < MAX_SAMPLES:
            self.samples[rule].append({"line": line_no, "detail": detail[:300]})

    def ts(self, s):
        if self.ts_min is None or s < self.ts_min:
            self.ts_min = s
        if self.ts_max is None or s > self.ts_max:
            self.ts_max = s


def _nonempty_str(v):
    return isinstance(v, str) and len(v) > 0


def check_resource(doc, acc, ln):
    res = doc.get("resource")
    if not isinstance(res, dict) or not isinstance(res.get("attributes"), dict):
        acc.err("resource.attributes.missing", ln, "resource.attributes object missing")
        return
    attrs = res["attributes"]
    for k in RESOURCE_REQUIRED:
        if not _nonempty_str(attrs.get(k)):
            acc.err("resource.%s.missing" % k, ln, "resource attribute %s missing or empty" % k)
    if set(res.keys()) != {"attributes"}:
        acc.err("resource.unexpected_keys", ln, str(sorted(res.keys())))


def check_common(doc, acc, ln):
    t = doc.get("@timestamp")
    if not isinstance(t, str) or not TS_RE.match(t):
        acc.err("timestamp.format", ln, "invalid @timestamp: %r" % (t,))
    else:
        acc.ts(t)
    check_resource(doc, acc, ln)


def validate_log(doc, acc, ln):
    check_common(doc, acc, ln)
    sev = doc.get("severity_text")
    if sev not in LOG_SEVERITY:
        acc.err("severity_text.invalid", ln, repr(sev))
    elif doc.get("severity_number") != LOG_SEVERITY[sev]:
        acc.err("severity_number.mismatch", ln, "%r vs %r" % (sev, doc.get("severity_number")))
    else:
        acc.values["severity." + sev] += 1
    body = doc.get("body")
    if not isinstance(body, dict) or not _nonempty_str(body.get("text")):
        acc.err("body.text.missing", ln, "body.text missing or empty")
    ot = doc.get("observed_timestamp")
    if not isinstance(ot, str) or not TS_RE.match(ot):
        acc.err("observed_timestamp.format", ln, repr(ot))
    scope = doc.get("scope")
    if not isinstance(scope, dict) or not _nonempty_str(scope.get("name")) or not _nonempty_str(scope.get("version")):
        acc.err("scope.missing", ln, "scope.name/scope.version missing")
    has_tid, has_sid = "trace_id" in doc, "span_id" in doc
    if has_tid != has_sid:
        acc.err("trace_span_pair.incomplete", ln, "trace_id/span_id must both be present or both absent")
    if has_tid:
        tid, sid = doc["trace_id"], doc["span_id"]
        if not isinstance(tid, str) or not HEX32.match(tid) or tid == ZERO32:
            acc.err("trace_id.format", ln, repr(tid))
        if not isinstance(sid, str) or not HEX16.match(sid) or sid == ZERO16:
            acc.err("span_id.format", ln, repr(sid))
    attrs = doc.get("attributes")
    if not isinstance(attrs, dict):
        acc.err("attributes.missing", ln, "attributes object missing")
    else:
        code = attrs.get("http.response.status_code")
        if code is not None and (not isinstance(code, int) or not 100 <= code <= 599):
            acc.err("http.status_code.range", ln, repr(code))
        if sev == "ERROR" and not _nonempty_str(attrs.get("exception.type")):
            acc.err("exception.type.missing", ln, "ERROR log without exception.type")


def validate_span(doc, acc, ln):
    check_common(doc, acc, ln)
    tid, sid = doc.get("trace_id"), doc.get("span_id")
    if not isinstance(tid, str) or not HEX32.match(tid) or tid == ZERO32:
        acc.err("trace_id.format", ln, repr(tid))
    if not isinstance(sid, str) or not HEX16.match(sid) or sid == ZERO16:
        acc.err("span_id.format", ln, repr(sid))
    pid = doc.get("parent_span_id")
    if pid is not None:
        if not isinstance(pid, str) or not HEX16.match(pid) or pid == sid:
            acc.err("parent_span_id.format", ln, repr(pid))
    if not _nonempty_str(doc.get("name")):
        acc.err("name.missing", ln, "span name missing")
    if doc.get("kind") not in SPAN_KINDS:
        acc.err("kind.invalid", ln, repr(doc.get("kind")))
    dur = doc.get("duration")
    if not isinstance(dur, int) or isinstance(dur, bool) or dur < 0:
        acc.err("duration.invalid", ln, repr(dur))
    status = doc.get("status")
    if not isinstance(status, dict) or status.get("code") not in STATUS_CODES:
        acc.err("status.code.invalid", ln, repr(status))
    else:
        msg = status.get("message")
        if status["code"] == "STATUS_CODE_ERROR":
            if not _nonempty_str(msg):
                acc.err("status.message.missing", ln, "ERROR span without status.message")
        elif msg is not None:
            acc.err("status.message.unexpected", ln, "status.message on non-error span")
    scope = doc.get("scope")
    if not isinstance(scope, dict) or not _nonempty_str(scope.get("name")):
        acc.err("scope.missing", ln, "scope.name missing")
    attrs = doc.get("attributes")
    if not isinstance(attrs, dict):
        acc.err("attributes.missing", ln, "attributes object missing")
    else:
        code = attrs.get("http.response.status_code")
        if code is not None and (not isinstance(code, int) or not 100 <= code <= 599):
            acc.err("http.status_code.range", ln, repr(code))
    acc.values["kind." + str(doc.get("kind"))] += 1


def validate_metric(doc, acc, ln, last_counter):
    check_common(doc, acc, ln)
    attrs = doc.get("attributes")
    stream = attrs.get("stream") if isinstance(attrs, dict) else None
    if stream not in METRIC_STREAMS:
        acc.err("stream.invalid", ln, repr(stream))
        return
    pod = ((doc.get("resource") or {}).get("attributes") or {}).get("k8s.pod.name", "")
    metrics = doc.get("metrics")
    if not isinstance(metrics, dict):
        acc.err("metrics.missing", ln, "metrics object missing")
        return
    flat = {}
    for k, v in metrics.items():
        if not isinstance(v, dict):
            flat["metrics." + k] = v
            continue
        stack = [("metrics." + k, v)]
        while stack:
            prefix, node = stack.pop()
            for kk, vv in node.items():
                full = prefix + "." + kk
                if isinstance(vv, dict):
                    stack.append((full, vv))
                else:
                    flat[full] = vv
    expected = set(STREAM_FIELDS[stream])
    if set(flat.keys()) != expected:
        acc.err("metrics.fields.mismatch", ln, "stream=%s got=%s expected=%s" % (stream, sorted(flat), sorted(expected)))
        return
    for name, v in flat.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)):
            acc.err("metrics.value.type", ln, "%s=%r" % (name, v))
            continue
        if name.endswith("utilization") and not 0.0 <= v <= 1.0:
            acc.err("metrics.utilization.range", ln, "%s=%r" % (name, v))
        if name in METRIC_COUNTERS:
            if not isinstance(v, int) or v < 0:
                acc.err("metrics.counter.type", ln, "%s=%r" % (name, v))
                continue
            key = (pod, stream, name)
            prev = last_counter.get(key)
            if prev is not None and v < prev[1]:
                acc.err("metrics.counter.decreased", ln, "%s %r -> %r" % (key, prev[1], v))
            if prev is None:
                last_counter[key] = [v, v]
            else:
                prev[1] = v
        if name in METRIC_GAUGES and name.endswith("p95") and v < 0:
            acc.err("metrics.gauge.negative", ln, "%s=%r" % (name, v))
    acc.values["stream." + stream] += 1


def chunk_ranges(path, workers):
    size = os.path.getsize(path)
    bounds = []
    with open(path, "rb") as fh:
        for i in range(workers + 1):
            pos = size * i // workers
            if i in (0, workers):
                bounds.append(pos if i == 0 else size)
                continue
            fh.seek(pos)
            fh.readline()
            bounds.append(fh.tell())
    return [(bounds[i], bounds[i + 1]) for i in range(workers)]


def validate_chunk(args):
    path, signal, start, end = args
    acc = Acc()
    last_counter = {}
    first_counter = {}
    with open(path, "rb") as fh:
        fh.seek(start)
        pos = start
        ln = 0
        for raw in fh:
            ln += 1
            pos += len(raw)
            if pos > end and start != end:
                break
            acc.docs += 1
            try:
                doc = json.loads(raw)
                if not isinstance(doc, dict):
                    raise ValueError("not an object")
            except Exception as e:  # noqa: BLE001
                acc.bad_docs += 1
                acc.err("json.parse", ln, str(e))
                continue
            before = sum(acc.errors.values())
            if signal == "logs":
                validate_log(doc, acc, ln)
            elif signal == "traces":
                validate_span(doc, acc, ln)
            else:
                validate_metric(doc, acc, ln, last_counter)
            if sum(acc.errors.values()) > before:
                acc.bad_docs += 1
    for k, v in last_counter.items():
        first_counter[k] = v[0]
    return {
        "docs": acc.docs, "bad_docs": acc.bad_docs, "errors": dict(acc.errors),
        "samples": {k: v for k, v in acc.samples.items()}, "ts_min": acc.ts_min, "ts_max": acc.ts_max,
        "values": dict(acc.values), "first_counter": {repr(k): v for k, v in first_counter.items()},
        "last_counter": {repr(k): v[1] for k, v in last_counter.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("signal", choices=["logs", "traces", "metrics"])
    ap.add_argument("path")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    started = time.time()
    ranges = chunk_ranges(args.path, args.workers)
    tasks = [(args.path, args.signal, s, e) for s, e in ranges]
    with mp.Pool(args.workers) as pool:
        parts = pool.map(validate_chunk, tasks)

    total = {"docs": 0, "bad_docs": 0, "errors": Counter(), "values": Counter(), "samples": {}}
    ts_min = ts_max = None
    for p in parts:
        total["docs"] += p["docs"]
        total["bad_docs"] += p["bad_docs"]
        total["errors"].update(p["errors"])
        total["values"].update(p["values"])
        for rule, s in p["samples"].items():
            total["samples"].setdefault(rule, [])
            if len(total["samples"][rule]) < MAX_SAMPLES:
                total["samples"][rule].extend(s[: MAX_SAMPLES - len(total["samples"][rule])])
        if p["ts_min"] and (ts_min is None or p["ts_min"] < ts_min):
            ts_min = p["ts_min"]
        if p["ts_max"] and (ts_max is None or p["ts_max"] > ts_max):
            ts_max = p["ts_max"]

    cross_chunk_violations = 0
    if args.signal == "metrics":
        for i in range(len(parts) - 1):
            last = parts[i]["last_counter"]
            first = parts[i + 1]["first_counter"]
            for key, lv in last.items():
                if key in first and first[key] < lv:
                    cross_chunk_violations += 1
        if cross_chunk_violations:
            total["errors"]["metrics.counter.decreased_across_chunks"] = cross_chunk_violations
            total["samples"]["metrics.counter.decreased_across_chunks"] = [{"detail": "%d series" % cross_chunk_violations}]

    n_errors = sum(total["errors"].values())
    result = {
        "signal": args.signal, "file": os.path.basename(args.path),
        "file_bytes": os.path.getsize(args.path), "docs_checked": total["docs"],
        "docs_with_errors": total["bad_docs"], "error_count": n_errors,
        "errors_by_rule": dict(total["errors"]), "error_samples": total["samples"],
        "timestamp_min": ts_min, "timestamp_max": ts_max, "value_distribution": dict(total["values"]),
        "passed": n_errors == 0 and total["docs"] > 0,
        "validation_seconds": round(time.time() - started, 1), "workers": args.workers,
    }
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(json.dumps({k: result[k] for k in ("signal", "docs_checked", "docs_with_errors", "error_count", "passed", "validation_seconds")}))


if __name__ == "__main__":
    main()
