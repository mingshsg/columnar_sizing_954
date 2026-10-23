"""Shared OpenTelemetry schema for the benchmark: data stream names, index
mappings (used by setup_es.py) and value domains (used by gen_otel.py and
validate_files.py)."""

RESOURCE_KEYS = [
    "service.name",
    "service.version",
    "host.name",
    "k8s.pod.name",
    "k8s.namespace.name",
    "cloud.region",
    "deployment.environment.name",
]

LOG_SEVERITY = {"DEBUG": 5, "INFO": 9, "WARN": 13, "ERROR": 17}
SPAN_KINDS = ["SPAN_KIND_SERVER", "SPAN_KIND_CLIENT", "SPAN_KIND_INTERNAL"]
STATUS_CODES = ["STATUS_CODE_UNSET", "STATUS_CODE_OK", "STATUS_CODE_ERROR"]
METRIC_STREAMS = ["cpu", "memory", "network", "disk", "http"]
STREAM_FIELDS = {
    "cpu": ["metrics.system.cpu.utilization"],
    "memory": ["metrics.system.memory.usage"],
    "network": ["metrics.system.network.io.receive", "metrics.system.network.io.transmit"],
    "disk": ["metrics.system.disk.io.read"],
    "http": ["metrics.http.server.request.count", "metrics.http.server.duration.p95"],
}
METRIC_GAUGES = {
    "metrics.system.cpu.utilization",
    "metrics.system.memory.usage",
    "metrics.http.server.duration.p95",
}
METRIC_COUNTERS = {
    "metrics.system.network.io.receive",
    "metrics.system.network.io.transmit",
    "metrics.system.disk.io.read",
    "metrics.http.server.request.count",
}

LOGS_LOGSDB = "logs-otel.logsdb-bench"
LOGS_COLUMNAR = "logs-otel.columnar-bench"
TRACES_LOGSDB = "traces-otel.logsdb-bench"
TRACES_COLUMNAR = "traces-otel.columnar-bench"
METRICS_TSDS = "metrics-otel.tsds-bench"

SHARDS = 2
REPLICAS = 0
METRIC_LOOK_BACK = "7d"

KW = {"type": "keyword"}
MOT = {"type": "match_only_text"}


def _kw_dim():
    return {"type": "keyword", "time_series_dimension": True}


def _resource_props(dim=False):
    props = {}
    for k in RESOURCE_KEYS:
        props[k] = _kw_dim() if (dim and k in ("service.name", "host.name", "k8s.pod.name", "k8s.namespace.name", "cloud.region")) else dict(KW)
    return {"resource": {"properties": {"attributes": {"properties": props}}}}


def logs_mapping():
    return {
        "dynamic": "strict",
        "properties": {
            "@timestamp": {"type": "date"},
            "observed_timestamp": {"type": "date"},
            "trace_id": dict(KW),
            "span_id": dict(KW),
            "severity_text": dict(KW),
            "severity_number": {"type": "integer"},
            "body": {"properties": {"text": dict(MOT)}},
            **_resource_props(),
            "scope": {"properties": {"name": dict(KW), "version": dict(KW)}},
            "attributes": {"properties": {
                "http.request.method": dict(KW),
                "http.response.status_code": {"type": "long"},
                "url.path": dict(KW),
                "thread.name": dict(KW),
                "exception.type": dict(KW),
                "exception.message": dict(MOT),
                "app.order.id": dict(KW),
                "app.cart.items": {"type": "integer"},
            }},
        },
    }


def traces_mapping():
    return {
        "dynamic": "strict",
        "properties": {
            "@timestamp": {"type": "date"},
            "trace_id": dict(KW),
            "span_id": dict(KW),
            "parent_span_id": dict(KW),
            "name": dict(KW),
            "kind": dict(KW),
            "duration": {"type": "long"},
            "status": {"properties": {"code": dict(KW), "message": dict(MOT)}},
            **_resource_props(),
            "scope": {"properties": {"name": dict(KW), "version": dict(KW)}},
            "attributes": {"properties": {
                "http.request.method": dict(KW),
                "http.route": dict(KW),
                "http.response.status_code": {"type": "long"},
                "server.address": dict(KW),
                "db.system": dict(KW),
                "exception.type": dict(KW),
                "exception.message": dict(MOT),
            }},
        },
    }


def metrics_mapping():
    metric_props = {}
    for name in sorted(METRIC_GAUGES | METRIC_COUNTERS):
        is_gauge = name in METRIC_GAUGES
        is_double = name.endswith("utilization") or name.endswith("p95")
        metric_props[name[len("metrics."):]] = {
            "type": "double" if is_double else "long",
            "time_series_metric": "gauge" if is_gauge else "counter",
        }
    return {
        "dynamic": "strict",
        "properties": {
            "@timestamp": {"type": "date"},
            **_resource_props(dim=True),
            "attributes": {"properties": {"stream": _kw_dim()}},
            "metrics": {"properties": _nest(metric_props)},
        },
    }


def _nest(flat):
    root = {}
    for dotted, spec in flat.items():
        node = root
        parts = dotted.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {"properties": {}})["properties"]
        node[parts[-1]] = spec
    return root


METRICS_ROUTING_PATH = [
    "resource.attributes.service.name",
    "resource.attributes.host.name",
    "resource.attributes.k8s.pod.name",
    "resource.attributes.k8s.namespace.name",
    "resource.attributes.cloud.region",
    "attributes.stream",
]
