"""Generate OpenTelemetry-shaped NDJSON documents (logs, traces or metrics).

Writes document bytes only (no bulk action lines), one JSON document per line,
until the target number of bytes has been written. Deterministic for a given
seed and base time.

Usage:
  python3 gen_otel.py logs    --out data/logs.ndjson    --target-gib 100 --base-ms 1760000000000 --seed 1
"""
import argparse
import json
import os
import random
import sys
import time
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import (  # noqa: E402
    LOG_SEVERITY, METRIC_STREAMS, STREAM_FIELDS, SPAN_KINDS, STATUS_CODES,
)

DOMAINS = ["cart", "checkout", "payment", "catalog", "search", "auth", "inventory", "shipping", "notification", "gateway"]
TIERS = ["api", "worker", "proxy", "batch"]
NAMESPACES = ["shop-prod", "shop-staging", "platform", "observability", "data", "batch"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
ROUTES = ["/api/v1/cart", "/api/v1/checkout", "/api/v1/orders/{id}", "/api/v1/catalog/items", "/api/v1/search", "/api/v1/auth/token", "/healthz", "/api/v1/shipping/quote"]
METHODS = ["GET", "POST", "PUT", "DELETE"]
DB_TABLES = ["carts", "orders", "inventory", "customers", "payments"]
EXC_TYPES = ["java.net.SocketTimeoutException", "io.grpc.StatusRuntimeException", "java.lang.IllegalStateException", "TimeoutError", "ValueError"]
EXC_MESSAGES = [
    "upstream connect timeout after 3000ms",
    "payment provider returned 503 Service Unavailable",
    "connection reset by peer while reading response",
    "inventory reservation conflict for sku",
    "deadline exceeded calling catalog.GetItem",
]
LOG_TEMPLATES = {
    "INFO": [
        "Request {m} {p} completed with {s} in {l}ms",
        "Order {o} persisted for customer {c}",
        "Cache refreshed for {p} entries={n}",
        "Heartbeat ok, active_connections={n}",
    ],
    "DEBUG": [
        "Resolved route {p} to handler {h}",
        "Query plan cached key={o} hits={n}",
    ],
    "WARN": [
        "Retrying upstream {h} attempt={n} after timeout",
        "Slow response from {h}: {l}ms exceeds budget",
    ],
    "ERROR": [
        "Failed to process {m} {p} for order {o}",
        "Unhandled exception while handling {m} {p} request_id={c}",
    ],
}
SEV_WEIGHTS = [("DEBUG", 15), ("INFO", 65), ("WARN", 12), ("ERROR", 8)]


@lru_cache(maxsize=200000)
def _sec_prefix(sec):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(sec))


def ts(ms):
    sec, rem = divmod(ms, 1000)
    return "%s.%03dZ" % (_sec_prefix(sec), rem)


def hex_id(rng, nbytes):
    while True:
        v = rng.getrandbits(nbytes * 8)
        if v:
            return ("%0" + str(nbytes * 2) + "x") % v


def build_pods(rng, n_pods=2000, n_hosts=200):
    services = ["%s-%s" % (d, t) for d in DOMAINS for t in TIERS]
    svc_version = {s: "1.%d.%d" % (rng.randint(0, 20), rng.randint(0, 9)) for s in services}
    pods = []
    for i in range(n_pods):
        svc = services[i % len(services)]
        host_idx = i % n_hosts
        ns = NAMESPACES[i % len(NAMESPACES)]
        pods.append({
            "service.name": svc,
            "service.version": svc_version[svc],
            "host.name": "node-%04d" % host_idx,
            "k8s.pod.name": "%s-%x-%05x" % (svc, i, rng.getrandbits(20)),
            "k8s.namespace.name": ns,
            "cloud.region": REGIONS[host_idx % len(REGIONS)],
            "deployment.environment.name": "production" if ns.endswith("prod") else "staging",
        })
    return pods


def resource_of(pod):
    return {"attributes": {k: pod[k] for k in (
        "service.name", "service.version", "host.name", "k8s.pod.name",
        "k8s.namespace.name", "cloud.region", "deployment.environment.name")}}


def weighted_sev(rng):
    r = rng.randint(1, 100)
    acc = 0
    for name, w in SEV_WEIGHTS:
        acc += w
        if r <= acc:
            return name
    return "INFO"


def gen_logs(fh, target, base_ms, rng):
    pods = build_pods(rng)
    scopes = [("io.opentelemetry.http", "1.32.0"), ("io.opentelemetry.jdbc", "1.32.0"), ("app.logger", "2.4.1")]
    t = base_ms
    written = 0
    count = 0
    dumps = json.dumps
    while written < target:
        count += 1
        t += rng.randint(0, 2)
        pod = pods[rng.randrange(len(pods))]
        sev = weighted_sev(rng)
        fields = {
            "m": METHODS[rng.randrange(4)], "p": ROUTES[rng.randrange(len(ROUTES))],
            "s": rng.choice([200, 201, 204, 400, 404, 500, 503]), "l": rng.randint(1, 2500),
            "o": "ord-%010d" % rng.randrange(10 ** 10), "c": "cust-%08d" % rng.randrange(10 ** 8),
            "n": rng.randint(0, 999), "h": "%s:%d" % (rng.choice(DOMAINS) + "-api", rng.choice([8080, 8443, 9090])),
        }
        text = rng.choice(LOG_TEMPLATES[sev]).format(**fields)
        scope = scopes[rng.randrange(len(scopes))]
        doc = {
            "@timestamp": ts(t),
            "observed_timestamp": ts(t + rng.randint(0, 40)),
            "severity_text": sev,
            "severity_number": LOG_SEVERITY[sev],
            "body": {"text": text},
            "resource": resource_of(pod),
            "scope": {"name": scope[0], "version": scope[1]},
            "attributes": {},
        }
        if rng.random() < 0.6:
            doc["trace_id"] = hex_id(rng, 16)
            doc["span_id"] = hex_id(rng, 8)
        attrs = doc["attributes"]
        attrs["thread.name"] = "http-nio-%d-exec-%d" % (8080, rng.randint(1, 200))
        if sev == "ERROR":
            attrs["exception.type"] = rng.choice(EXC_TYPES)
            attrs["exception.message"] = rng.choice(EXC_MESSAGES)
        else:
            attrs["http.request.method"] = fields["m"]
            attrs["http.response.status_code"] = fields["s"]
            attrs["url.path"] = fields["p"].replace("{id}", str(rng.randrange(10 ** 6)))
        if rng.random() < 0.3:
            attrs["app.order.id"] = fields["o"]
            attrs["app.cart.items"] = rng.randint(1, 40)
        line = dumps(doc, separators=(",", ":")) + "\n"
        fh.write(line)
        written += len(line)
    return count, written, base_ms, t


def gen_traces(fh, target, base_ms, rng):
    pods = build_pods(rng)
    scopes = [("io.opentelemetry.http", "1.32.0"), ("io.opentelemetry.jdbc", "1.32.0")]
    t = base_ms
    written = 0
    count = 0
    dumps = json.dumps
    while written < target:
        t += rng.randint(2, 4)
        trace_id = hex_id(rng, 16)
        n_spans = rng.randint(3, 9)
        root_pod = pods[rng.randrange(len(pods))]
        root_span = hex_id(rng, 8)
        root_dur = rng.randint(5, 800) * 1000000
        route = rng.choice(ROUTES).replace("{id}", str(rng.randrange(10 ** 6)))
        root_status = "STATUS_CODE_ERROR" if rng.random() < 0.04 else rng.choice(["STATUS_CODE_UNSET", "STATUS_CODE_OK"])
        spans = [{
            "span_id": root_span, "parent": None, "start": t, "dur": root_dur,
            "pod": root_pod, "kind": "SPAN_KIND_SERVER", "name": "%s %s" % (rng.choice(METHODS), route),
            "status": root_status, "scope": scopes[0],
        }]
        for _ in range(n_spans - 1):
            parent = spans[rng.randrange(len(spans))]
            pod = pods[rng.randrange(len(pods))]
            is_db = rng.random() < 0.3
            child_start = parent["start"] + rng.randint(0, max(1, parent["dur"] // 2000000))
            dur = max(1000, parent["dur"] // rng.randint(2, 6))
            spans.append({
                "span_id": hex_id(rng, 8), "parent": parent["span_id"], "start": child_start, "dur": dur,
                "pod": pod, "kind": "SPAN_KIND_CLIENT" if is_db else rng.choice(SPAN_KINDS[:3]),
                "name": ("SELECT %s" % rng.choice(DB_TABLES)) if is_db else "%s %s" % (rng.choice(METHODS), route),
                "status": "STATUS_CODE_ERROR" if rng.random() < 0.03 else "STATUS_CODE_UNSET",
                "scope": scopes[1] if is_db else scopes[0],
            })
        for sp in spans:
            doc = {
                "@timestamp": ts(sp["start"]),
                "trace_id": trace_id,
                "span_id": sp["span_id"],
            }
            if sp["parent"]:
                doc["parent_span_id"] = sp["parent"]
            doc["name"] = sp["name"]
            doc["kind"] = sp["kind"]
            doc["duration"] = sp["dur"]
            status = {"code": sp["status"]}
            if sp["status"] == "STATUS_CODE_ERROR":
                status["message"] = rng.choice(EXC_MESSAGES)
            doc["status"] = status
            doc["resource"] = resource_of(sp["pod"])
            doc["scope"] = {"name": sp["scope"][0], "version": sp["scope"][1]}
            attrs = {}
            if sp["scope"] is scopes[1]:
                attrs["db.system"] = "postgresql"
            else:
                attrs["http.request.method"] = sp["name"].split(" ")[0]
                attrs["http.route"] = route
                attrs["http.response.status_code"] = rng.choice([200, 200, 201, 404, 500])
                attrs["server.address"] = "%s-api" % sp["pod"]["service.name"]
            if sp["status"] == "STATUS_CODE_ERROR":
                attrs["exception.type"] = rng.choice(EXC_TYPES)
                attrs["exception.message"] = rng.choice(EXC_MESSAGES)
            doc["attributes"] = attrs
            line = dumps(doc, separators=(",", ":")) + "\n"
            fh.write(line)
            written += len(line)
            count += 1
    return count, written, base_ms, t


def gen_metrics(fh, target, base_ms, rng):
    pods = build_pods(rng)
    series = [(pod, s) for pod in pods for s in METRIC_STREAMS]
    n = len(series)
    counters = {}
    gauges = {}
    for idx in range(n):
        for f in STREAM_FIELDS[series[idx][1]]:
            counters[(idx, f)] = rng.randint(10 ** 6, 10 ** 9)
            gauges[(idx, f)] = rng.uniform(0.1, 0.9)
    tick_ms = 10000
    t = base_ms
    written = 0
    count = 0
    dumps = json.dumps
    while written < target:
        for idx in range(n):
            pod, stream = series[idx]
            metrics = {}
            for f in STREAM_FIELDS[stream]:
                if f.endswith("utilization"):
                    v = min(1.0, max(0.0, gauges[(idx, f)] + rng.uniform(-0.05, 0.05)))
                    gauges[(idx, f)] = v
                    metrics[f] = round(v, 4)
                elif f.endswith("usage"):
                    metrics[f] = rng.randint(200 * 10 ** 6, 4 * 10 ** 9)
                elif f.endswith("p95"):
                    metrics[f] = round(rng.uniform(5.0, 900.0), 2)
                else:
                    counters[(idx, f)] += rng.randint(0, 5000)
                    metrics[f] = counters[(idx, f)]
            doc = {"@timestamp": ts(t), "resource": resource_of(pod), "attributes": {"stream": stream}, "metrics": _nest(metrics)}
            line = dumps(doc, separators=(",", ":")) + "\n"
            fh.write(line)
            written += len(line)
            count += 1
        t += tick_ms
    return count, written, base_ms, t


def _nest(flat):
    root = {}
    for dotted, v in flat.items():
        parts = dotted[len("metrics."):].split(".")
        node = root
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("signal", choices=["logs", "traces", "metrics"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--target-gib", type=float, default=100.0)
    ap.add_argument("--base-ms", type=int, required=True)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    target = int(args.target_gib * 1024 ** 3)
    rng = random.Random(args.seed)
    fn = {"logs": gen_logs, "traces": gen_traces, "metrics": gen_metrics}[args.signal]
    tmp = args.out + ".partial"
    started = time.time()
    with open(tmp, "w", buffering=8 * 1024 * 1024) as fh:
        count, written, first_ms, last_ms = fn(fh, target, args.base_ms, rng)
    os.rename(tmp, args.out)
    elapsed = time.time() - started
    meta = {
        "signal": args.signal, "file": os.path.basename(args.out), "docs": count,
        "bytes": written, "target_bytes": target, "seed": args.seed,
        "first_timestamp": ts(first_ms), "last_timestamp": ts(last_ms),
        "generation_seconds": round(elapsed, 1), "docs_per_second": round(count / elapsed, 1),
    }
    with open(args.out + ".meta.json", "w") as mf:
        json.dump(meta, mf, indent=2)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
