"""Field types from the mappings captured from the cluster (results/config/*.mapping.json).

Flattens the nested mapping into dotted field paths, so disk-usage field names
(for example `resource.attributes.service.name`) can be looked up directly.
Elasticsearch-internal entries that have no mapping (`<field>._original`,
`<field>.counts`, `_id`, `_field_names`) get an explicit label.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "results", "config")

INTERNAL = {
    "_id": "(metadata) document id",
    "_field_names": "(metadata) field-name index",
    "_seq_no": "(metadata) sequence number",
    "_primary_term": "(metadata) primary term",
    "_version": "(metadata) document version",
    "_recovery_source_size": "(metadata) recovery source size",
    "__root_doc_for_nested": "(metadata) nested-document root marker",
    "_tsid": "(metadata) TSDS time series id",
    "_ts_routing_hash": "(metadata) TSDS routing hash",
}


def _flatten(props, prefix, out):
    for name, spec in (props or {}).items():
        path = prefix + name
        if "properties" in spec:
            _flatten(spec["properties"], path + ".", out)
        if "type" in spec:
            out[path] = spec
    return out


def load_mapping(ds):
    """Return {field path: mapping spec} for one data stream."""
    with open(os.path.join(CONFIG, "%s.mapping.json" % ds), encoding="utf-8") as fh:
        body = json.load(fh)
    index = next(iter(body.values()))
    return _flatten(index["mappings"].get("properties", {}), "", {})


def label(spec):
    t = spec["type"]
    extras = []
    if spec.get("time_series_dimension"):
        extras.append("dimension")
    if spec.get("time_series_metric"):
        extras.append(spec["time_series_metric"])
    return "%s (%s)" % (t, ", ".join(extras)) if extras else t


def type_of(field, mapped):
    """Human-readable type for a disk-usage field name."""
    if field in mapped:
        return label(mapped[field])
    if field in INTERNAL:
        return INTERNAL[field]
    if field.endswith("._original"):
        base = field[: -len("._original")]
        if base in mapped:
            return "(internal) original copy of %s" % label(mapped[base])
        return "(internal) original copy"
    if field.endswith(".counts"):
        base = field[: -len(".counts")]
        if base in mapped:
            return "(internal) value counts of %s" % label(mapped[base])
        return "(internal) value counts"
    return "(not in mapping)"
