"""Create the benchmark index templates and data streams on the target cluster and
verify that each index picked up the intended mode, source mode and settings.

Data streams:
  logs-otel.logsdb-bench      index.mode=logsdb          synthetic _source
  logs-otel.columnar-bench    index.mode=logsdb_columnar synthetic _source
  traces-otel.logsdb-bench    index.mode=logsdb          synthetic _source
  traces-otel.columnar-bench  index.mode=logsdb_columnar synthetic _source
  metrics-otel.tsds-bench     index.mode=time_series     (TSDS, look_back_time 7d)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import es_session  # noqa: E402
import schema as S  # noqa: E402

SPECS = [
    {"ds": S.LOGS_LOGSDB, "mode": "logsdb", "mapping": S.logs_mapping, "kind": "logs"},
    {"ds": S.LOGS_COLUMNAR, "mode": "logsdb_columnar", "mapping": S.logs_mapping, "kind": "logs"},
    {"ds": S.TRACES_LOGSDB, "mode": "logsdb", "mapping": S.traces_mapping, "kind": "traces"},
    {"ds": S.TRACES_COLUMNAR, "mode": "logsdb_columnar", "mapping": S.traces_mapping, "kind": "traces"},
    {"ds": S.METRICS_TSDS, "mode": "time_series", "mapping": S.metrics_mapping, "kind": "metrics"},
]


def template_for(spec):
    settings = {
        "index.mode": spec["mode"],
        "number_of_shards": S.SHARDS,
        "number_of_replicas": S.REPLICAS,
        "index.mapping.source.mode": "synthetic",
    }
    if spec["kind"] == "metrics":
        settings["index.routing_path"] = S.METRICS_ROUTING_PATH
        settings["index.look_back_time"] = S.METRIC_LOOK_BACK
    return {
        "index_patterns": [spec["ds"]],
        "data_stream": {},
        "priority": 500,
        "template": {"settings": settings, "mappings": spec["mapping"]()},
        "_meta": {"benchmark": "otel-es-benchmark", "signal": spec["kind"]},
    }


def main():
    s, base = es_session()
    lic = s.get(base + "/_license").json()["license"]
    print("license:", lic["type"], lic["status"])
    if lic["status"] != "active":
        sys.exit("license not active")

    ver = s.get(base + "/").json()["version"]["number"]
    print("elasticsearch version:", ver)
    if ver != "9.5.5":
        sys.exit("unexpected version %s" % ver)

    for spec in SPECS:
        s.delete(base + "/_data_stream/" + spec["ds"])
        s.delete(base + "/_index_template/bench-" + spec["ds"])
        r = s.put(base + "/_index_template/bench-" + spec["ds"], data=json.dumps(template_for(spec)))
        print("template", spec["ds"], r.status_code, r.text[:120])
        r.raise_for_status()

    for spec in SPECS:
        r = s.put(base + "/_data_stream/" + spec["ds"])
        print("data stream", spec["ds"], r.status_code, r.text[:120])
        r.raise_for_status()

    ok = True
    for spec in SPECS:
        idx = s.get(base + "/_data_stream/" + spec["ds"]).json()["data_streams"][0]["indices"][0]["index_name"]
        st = s.get(base + "/" + idx + "/_settings").json()[idx]["settings"]["index"]
        got = {
            "index.mode": st.get("mode"),
            "source.mode": st.get("mapping", {}).get("source", {}).get("mode"),
            "shards": st.get("number_of_shards"),
            "replicas": st.get("number_of_replicas"),
        }
        if spec["kind"] == "metrics":
            got["time_series"] = st.get("time_series")
            got["look_back_time"] = st.get("look_back_time")
            got["routing_path"] = st.get("routing_path")
        want_mode = spec["mode"]
        expect_source = "synthetic"
        check = got["index.mode"] == want_mode and got["source.mode"] == expect_source and str(got["shards"]) == str(S.SHARDS)
        if spec["kind"] == "metrics":
            check = check and got["time_series"] is not None and got["look_back_time"] == S.METRIC_LOOK_BACK
        ok = ok and check
        print("VERIFY", "OK  " if check else "FAIL", spec["ds"], idx, json.dumps(got))
    if not ok:
        sys.exit("settings verification failed")
    print("all data streams configured and verified")


if __name__ == "__main__":
    main()
