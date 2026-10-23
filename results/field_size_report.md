# Field-level storage report: Elasticsearch 9.5.5

Source: index disk usage API (`_disk_usage?run_expensive_tasks=true`) on the primary shards after force-merge to one segment per shard, and the mappings captured from the cluster (`results/config/`).

Both logs and traces use the same raw data (100 GiB per signal), the same mappings, 2 shards, 0 replicas, default sort (`host.name`, `@timestamp`) and the default `best_compression` codec.

**Field type** is the mapped type from the cluster. Entries in parentheses are dimensions or metric types for TSDS, and the Elasticsearch-internal entries.

Per-field bytes are the field's share of each on-disk structure. Synthetic `_source` is rebuilt from doc values and stored fields, so the doc values and stored fields columns show what the source costs. Fields that are absent in one mode show as `-` in that column.

Internal fields that appear in the per-field tables:

- `<field>._original` (logsdb only): logsdb keeps the original text of each `match_only_text` field so synthetic `_source` can be rebuilt. Columnar mode stores the same text in doc values instead, so compare the text fields in the text table rather than the `._original` rows alone.
- `<field>.counts` (columnar only): per-field value counts stored as separate columns.
- `_field_names` (logsdb only): Elasticsearch's field-name metadata.

## Logs

Index: `logs-otel.logsdb-bench` (logsdb) and `logs-otel.columnar-bench` (logsdb_columnar).

| Component | logsdb | logsdb_columnar | Difference | Columnar vs logsdb |
|---|---:|---:|---:|---:|
| Store size (primary, on disk) | 16239.32 MiB | 10870.11 MiB | -5369.21 MiB | -33.1% |
| All fields total | 16157.32 MiB | 10853.56 MiB | -5303.76 MiB | -32.8% |
| Inverted index | 7060.17 MiB | 1882.96 MiB | -5177.21 MiB | -73.3% |
| Doc values | 7975.88 MiB | 8970.60 MiB | 994.72 MiB | +12.5% |
| Stored fields | 327.62 MiB | 0 B | -327.62 MiB | -100.0% |
| Points (BKD) | 793.64 MiB | 0 B | -793.64 MiB | -100.0% |

logsdb_columnar uses 33.1% less disk than logsdb for logs.

### Text fields (`match_only_text`), including their `._original` copy

| Text field | Type | logsdb (field + `._original`) | columnar (field) | Difference | Columnar vs logsdb |
|---|---|---:|---:|---:|---:|
| `body.text` | match_only_text | 2852.20 MiB | 2850.58 MiB | -1.62 MiB | -0.1% |
| `attributes.exception.message` | match_only_text | 110.26 MiB | 110.26 MiB | 3.5 KiB | +0.0% |

### Per-field breakdown (sorted by combined size)

| Field | Type | logsdb total | columnar total | Difference | Columnar vs logsdb | logsdb inverted | columnar inverted | logsdb doc values | columnar doc values | logsdb stored | columnar stored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `trace_id` | keyword | 4920.33 MiB | 1448.69 MiB | -3471.65 MiB | -70.6% | 2137.66 MiB | 0 B | 2782.67 MiB | 1448.69 MiB | 0 B | 0 B |
| `body.text` | match_only_text | 1431.00 MiB | 2850.58 MiB | 1419.58 MiB | +99.2% | 1431.00 MiB | 1429.41 MiB | 0 B | 1421.17 MiB | 0 B | 0 B |
| `span_id` | keyword | 2454.48 MiB | 755.04 MiB | -1699.45 MiB | -69.2% | 1113.29 MiB | 0 B | 1341.19 MiB | 755.04 MiB | 0 B | 0 B |
| `_id` | (metadata) document id | 729.83 MiB | 829.39 MiB | 99.57 MiB | +13.6% | 402.21 MiB | 386.22 MiB | 0 B | 443.17 MiB | 327.62 MiB | 0 B |
| `body.text._original` | (internal) original copy of match_only_text | 1421.20 MiB | 0 B | -1421.20 MiB | -100.0% | 0 B | 0 B | 1421.20 MiB | 0 B | 0 B | 0 B |
| `resource.attributes.k8s.pod.name` | keyword | 443.00 MiB | 933.60 MiB | 490.61 MiB | +110.7% | 246.27 MiB | 0 B | 196.73 MiB | 933.60 MiB | 0 B | 0 B |
| `attributes.app.order.id` | keyword | 744.40 MiB | 261.09 MiB | -483.31 MiB | -64.9% | 359.43 MiB | 0 B | 384.97 MiB | 261.09 MiB | 0 B | 0 B |
| `attributes.url.path` | keyword | 502.48 MiB | 387.52 MiB | -114.97 MiB | -22.9% | 152.92 MiB | 0 B | 349.57 MiB | 387.52 MiB | 0 B | 0 B |
| `observed_timestamp` | date | 603.70 MiB | 167.64 MiB | -436.06 MiB | -72.2% | 0 B | 0 B | 166.49 MiB | 167.64 MiB | 0 B | 0 B |
| `attributes.thread.name` | keyword | 331.91 MiB | 353.50 MiB | 21.58 MiB | +6.5% | 188.56 MiB | 0 B | 143.35 MiB | 353.50 MiB | 0 B | 0 B |
| `resource.attributes.host.name` | keyword | 331.92 MiB | 322.39 MiB | -9.53 MiB | -2.9% | 188.57 MiB | 0 B | 143.35 MiB | 322.39 MiB | 0 B | 0 B |
| `resource.attributes.service.name` | keyword | 251.63 MiB | 393.72 MiB | 142.09 MiB | +56.5% | 143.84 MiB | 0 B | 107.79 MiB | 393.72 MiB | 0 B | 0 B |
| `resource.attributes.service.version` | keyword | 248.92 MiB | 253.51 MiB | 4.59 MiB | +1.8% | 141.13 MiB | 0 B | 107.79 MiB | 253.51 MiB | 0 B | 0 B |
| `attributes.http.response.status_code` | long | 300.17 MiB | 169.70 MiB | -130.47 MiB | -43.5% | 0 B | 0 B | 168.65 MiB | 169.70 MiB | 0 B | 0 B |
| `resource.attributes.k8s.namespace.name` | keyword | 146.83 MiB | 226.91 MiB | 80.07 MiB | +54.5% | 92.38 MiB | 0 B | 54.45 MiB | 226.91 MiB | 0 B | 0 B |
| `resource.attributes.cloud.region` | keyword | 113.90 MiB | 237.22 MiB | 123.32 MiB | +108.3% | 77.23 MiB | 0 B | 36.67 MiB | 237.22 MiB | 0 B | 0 B |
| `scope.name` | keyword | 104.37 MiB | 235.33 MiB | 130.96 MiB | +125.5% | 67.70 MiB | 0 B | 36.67 MiB | 235.33 MiB | 0 B | 0 B |
| `attributes.http.request.method` | keyword | 125.08 MiB | 159.29 MiB | 34.21 MiB | +27.3% | 72.98 MiB | 0 B | 52.10 MiB | 159.29 MiB | 0 B | 0 B |
| `attributes.app.cart.items` | integer | 197.91 MiB | 51.05 MiB | -146.87 MiB | -74.2% | 0 B | 0 B | 50.70 MiB | 51.05 MiB | 0 B | 0 B |
| `severity_text` | keyword | 107.00 MiB | 130.84 MiB | 23.84 MiB | +22.3% | 70.33 MiB | 0 B | 36.67 MiB | 130.84 MiB | 0 B | 0 B |
| `scope.version` | keyword | 71.50 MiB | 121.30 MiB | 49.81 MiB | +69.7% | 52.61 MiB | 0 B | 18.89 MiB | 121.30 MiB | 0 B | 0 B |
| `attributes.exception.message` | match_only_text | 67.33 MiB | 110.26 MiB | 42.94 MiB | +63.8% | 67.33 MiB | 67.33 MiB | 0 B | 42.93 MiB | 0 B | 0 B |
| `resource.attributes.deployment.environment.name` | keyword | 45.20 MiB | 126.61 MiB | 81.41 MiB | +180.1% | 26.31 MiB | 0 B | 18.89 MiB | 126.61 MiB | 0 B | 0 B |
| `@timestamp` | date | 80.77 MiB | 80.78 MiB | 8.8 KiB | +0.0% | 0 B | 0 B | 80.77 MiB | 80.78 MiB | 0 B | 0 B |
| `severity_number` | integer | 116.60 MiB | 40.04 MiB | -76.56 MiB | -65.7% | 0 B | 0 B | 38.89 MiB | 40.04 MiB | 0 B | 0 B |
| `_seq_no` | (metadata) sequence number | 150.90 MiB | 0 B | -150.90 MiB | -100.0% | 0 B | 0 B | 150.90 MiB | 0 B | 0 B | 0 B |
| `attributes.exception.type` | keyword | 35.07 MiB | 40.58 MiB | 5.50 MiB | +15.7% | 12.35 MiB | 0 B | 22.72 MiB | 40.58 MiB | 0 B | 0 B |
| `attributes.exception.message._original` | (internal) original copy of match_only_text | 42.93 MiB | 0 B | -42.93 MiB | -100.0% | 0 B | 0 B | 42.93 MiB | 0 B | 0 B | 0 B |
| `attributes.http.request.method.counts` | (internal) value counts of keyword | 0 B | 21.46 MiB | 21.46 MiB | - | 0 B | 0 B | 0 B | 21.46 MiB | 0 B | 0 B |
| `attributes.url.path.counts` | (internal) value counts of keyword | 0 B | 21.46 MiB | 21.46 MiB | - | 0 B | 0 B | 0 B | 21.46 MiB | 0 B | 0 B |
| `trace_id.counts` | (internal) value counts of keyword | 0 B | 20.38 MiB | 20.38 MiB | - | 0 B | 0 B | 0 B | 20.38 MiB | 0 B | 0 B |
| `span_id.counts` | (internal) value counts of keyword | 0 B | 20.38 MiB | 20.38 MiB | - | 0 B | 0 B | 0 B | 20.38 MiB | 0 B | 0 B |
| `attributes.app.order.id.counts` | (internal) value counts of keyword | 0 B | 19.37 MiB | 19.37 MiB | - | 0 B | 0 B | 0 B | 19.37 MiB | 0 B | 0 B |
| `attributes.exception.message.counts` | (internal) value counts of match_only_text | 0 B | 18.63 MiB | 18.63 MiB | - | 0 B | 0 B | 0 B | 18.63 MiB | 0 B | 0 B |
| `attributes.exception.type.counts` | (internal) value counts of keyword | 0 B | 18.63 MiB | 18.63 MiB | - | 0 B | 0 B | 0 B | 18.63 MiB | 0 B | 0 B |
| `attributes.exception.message._original.counts` | (internal) value counts | 18.63 MiB | 0 B | -18.63 MiB | -100.0% | 0 B | 0 B | 18.63 MiB | 0 B | 0 B | 0 B |
| `_field_names` | (metadata) field-name index | 16.08 MiB | 0 B | -16.08 MiB | -100.0% | 16.08 MiB | 0 B | 0 B | 0 B | 0 B | 0 B |
| `resource.attributes.deployment.environment.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.cloud.region.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `attributes.thread.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.k8s.pod.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `scope.version.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.service.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `body.text.counts` | (internal) value counts of match_only_text | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `scope.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.host.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.service.version.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `severity_text.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `resource.attributes.k8s.namespace.name.counts` | (internal) value counts of keyword | 0 B | 2.22 MiB | 2.22 MiB | - | 0 B | 0 B | 0 B | 2.22 MiB | 0 B | 0 B |
| `body.text._original.counts` | (internal) value counts | 2.22 MiB | 0 B | -2.22 MiB | -100.0% | 0 B | 0 B | 2.22 MiB | 0 B | 0 B | 0 B |
| `_recovery_source_size` | (metadata) recovery source size | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `_primary_term` | (metadata) primary term | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `__root_doc_for_nested` | (metadata) nested-document root marker | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `_version` | (metadata) document version | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| **Total (fields)** | | **16157.32 MiB** | **10853.56 MiB** | **-5303.76 MiB** | **-32.8%** | **7060.17 MiB** | **1882.96 MiB** | **7975.88 MiB** | **8970.60 MiB** | | |

## Traces

Index: `traces-otel.logsdb-bench` (logsdb) and `traces-otel.columnar-bench` (logsdb_columnar).

| Component | logsdb | logsdb_columnar | Difference | Columnar vs logsdb |
|---|---:|---:|---:|---:|
| Store size (primary, on disk) | 16482.33 MiB | 9823.79 MiB | -6658.54 MiB | -40.4% |
| All fields total | 16380.14 MiB | 9822.34 MiB | -6557.80 MiB | -40.0% |
| Inverted index | 6845.80 MiB | 546.68 MiB | -6299.11 MiB | -92.0% |
| Doc values | 8505.44 MiB | 9275.65 MiB | 770.22 MiB | +9.1% |
| Stored fields | 379.75 MiB | 0 B | -379.75 MiB | -100.0% |
| Points (BKD) | 649.16 MiB | 0 B | -649.16 MiB | -100.0% |

logsdb_columnar uses 40.4% less disk than logsdb for traces.

### Text fields (`match_only_text`), including their `._original` copy

| Text field | Type | logsdb (field + `._original`) | columnar (field) | Difference | Columnar vs logsdb |
|---|---|---:|---:|---:|---:|
| `attributes.exception.message` | match_only_text | 51.37 MiB | 51.37 MiB | -3.2 KiB | -0.0% |
| `status.message` | match_only_text | 51.36 MiB | 51.36 MiB | -3.1 KiB | -0.0% |

### Per-field breakdown (sorted by combined size)

| Field | Type | logsdb total | columnar total | Difference | Columnar vs logsdb | logsdb inverted | columnar inverted | logsdb doc values | columnar doc values | logsdb stored | columnar stored |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `span_id` | keyword | 4158.13 MiB | 1268.51 MiB | -2889.62 MiB | -69.5% | 1909.81 MiB | 0 B | 2248.32 MiB | 1268.51 MiB | 0 B | 0 B |
| `trace_id` | keyword | 3350.66 MiB | 1065.71 MiB | -2284.95 MiB | -68.2% | 1410.01 MiB | 0 B | 1940.66 MiB | 1065.71 MiB | 0 B | 0 B |
| `parent_span_id` | keyword | 2916.46 MiB | 908.72 MiB | -2007.74 MiB | -68.8% | 1333.21 MiB | 0 B | 1583.25 MiB | 908.72 MiB | 0 B | 0 B |
| `_id` | (metadata) document id | 877.52 MiB | 963.70 MiB | 86.17 MiB | +9.8% | 497.77 MiB | 482.73 MiB | 0 B | 480.97 MiB | 379.75 MiB | 0 B |
| `duration` | long | 1159.81 MiB | 591.33 MiB | -568.49 MiB | -49.0% | 0 B | 0 B | 590.14 MiB | 591.33 MiB | 0 B | 0 B |
| `resource.attributes.k8s.pod.name` | keyword | 457.68 MiB | 965.29 MiB | 507.60 MiB | +110.9% | 254.43 MiB | 0 B | 203.26 MiB | 965.29 MiB | 0 B | 0 B |
| `name` | keyword | 626.44 MiB | 544.64 MiB | -81.81 MiB | -13.1% | 208.52 MiB | 0 B | 417.92 MiB | 544.64 MiB | 0 B | 0 B |
| `attributes.http.route` | keyword | 414.44 MiB | 302.17 MiB | -112.28 MiB | -27.1% | 115.88 MiB | 0 B | 298.56 MiB | 302.17 MiB | 0 B | 0 B |
| `resource.attributes.host.name` | keyword | 342.94 MiB | 333.09 MiB | -9.85 MiB | -2.9% | 194.83 MiB | 0 B | 148.11 MiB | 333.09 MiB | 0 B | 0 B |
| `resource.attributes.service.name` | keyword | 259.99 MiB | 406.81 MiB | 146.81 MiB | +56.5% | 148.63 MiB | 0 B | 111.37 MiB | 406.81 MiB | 0 B | 0 B |
| `attributes.server.address` | keyword | 221.04 MiB | 356.09 MiB | 135.05 MiB | +61.1% | 118.54 MiB | 0 B | 102.50 MiB | 356.09 MiB | 0 B | 0 B |
| `resource.attributes.service.version` | keyword | 254.04 MiB | 257.90 MiB | 3.86 MiB | +1.5% | 142.67 MiB | 0 B | 111.37 MiB | 257.90 MiB | 0 B | 0 B |
| `resource.attributes.k8s.namespace.name` | keyword | 151.71 MiB | 234.45 MiB | 82.74 MiB | +54.5% | 95.46 MiB | 0 B | 56.26 MiB | 234.45 MiB | 0 B | 0 B |
| `attributes.http.response.status_code` | long | 225.04 MiB | 146.44 MiB | -78.60 MiB | -34.9% | 0 B | 0 B | 145.56 MiB | 146.44 MiB | 0 B | 0 B |
| `resource.attributes.cloud.region` | keyword | 117.68 MiB | 245.10 MiB | 127.42 MiB | +108.3% | 79.79 MiB | 0 B | 37.89 MiB | 245.10 MiB | 0 B | 0 B |
| `kind` | keyword | 102.84 MiB | 207.08 MiB | 104.24 MiB | +101.4% | 64.95 MiB | 0 B | 37.89 MiB | 207.08 MiB | 0 B | 0 B |
| `attributes.http.request.method` | keyword | 114.35 MiB | 137.68 MiB | 23.33 MiB | +20.4% | 66.96 MiB | 0 B | 47.39 MiB | 137.68 MiB | 0 B | 0 B |
| `scope.name` | keyword | 72.06 MiB | 160.04 MiB | 87.98 MiB | +122.1% | 52.54 MiB | 0 B | 19.52 MiB | 160.04 MiB | 0 B | 0 B |
| `status.code` | keyword | 61.43 MiB | 146.95 MiB | 85.52 MiB | +139.2% | 23.55 MiB | 0 B | 37.89 MiB | 146.95 MiB | 0 B | 0 B |
| `_seq_no` | (metadata) sequence number | 191.88 MiB | 0 B | -191.88 MiB | -100.0% | 0 B | 0 B | 191.88 MiB | 0 B | 0 B | 0 B |
| `resource.attributes.deployment.environment.name` | keyword | 46.71 MiB | 130.83 MiB | 84.13 MiB | +180.1% | 27.19 MiB | 0 B | 19.52 MiB | 130.83 MiB | 0 B | 0 B |
| `@timestamp` | date | 68.43 MiB | 68.43 MiB | 6.9 KiB | +0.0% | 0 B | 0 B | 68.43 MiB | 68.43 MiB | 0 B | 0 B |
| `attributes.exception.message` | match_only_text | 31.99 MiB | 51.37 MiB | 19.38 MiB | +60.6% | 31.99 MiB | 31.98 MiB | 0 B | 19.38 MiB | 0 B | 0 B |
| `status.message` | match_only_text | 31.98 MiB | 51.36 MiB | 19.38 MiB | +60.6% | 31.98 MiB | 31.97 MiB | 0 B | 19.38 MiB | 0 B | 0 B |
| `attributes.db.system` | keyword | 34.41 MiB | 37.53 MiB | 3.12 MiB | +9.1% | 15.43 MiB | 0 B | 18.98 MiB | 37.53 MiB | 0 B | 0 B |
| `scope.version` | keyword | 7.12 MiB | 55.74 MiB | 48.62 MiB | +683.1% | 7.12 MiB | 0 B | 14 B | 55.74 MiB | 0 B | 0 B |
| `attributes.exception.type` | keyword | 16.99 MiB | 18.42 MiB | 1.43 MiB | +8.4% | 5.87 MiB | 0 B | 11.12 MiB | 18.42 MiB | 0 B | 0 B |
| `parent_span_id.counts` | (internal) value counts of keyword | 0 B | 21.88 MiB | 21.88 MiB | - | 0 B | 0 B | 0 B | 21.88 MiB | 0 B | 0 B |
| `attributes.http.route.counts` | (internal) value counts of keyword | 0 B | 21.59 MiB | 21.59 MiB | - | 0 B | 0 B | 0 B | 21.59 MiB | 0 B | 0 B |
| `attributes.http.request.method.counts` | (internal) value counts of keyword | 0 B | 21.59 MiB | 21.59 MiB | - | 0 B | 0 B | 0 B | 21.59 MiB | 0 B | 0 B |
| `attributes.server.address.counts` | (internal) value counts of keyword | 0 B | 21.59 MiB | 21.59 MiB | - | 0 B | 0 B | 0 B | 21.59 MiB | 0 B | 0 B |
| `attributes.db.system.counts` | (internal) value counts of keyword | 0 B | 19.85 MiB | 19.85 MiB | - | 0 B | 0 B | 0 B | 19.85 MiB | 0 B | 0 B |
| `attributes.exception.message._original` | (internal) original copy of match_only_text | 19.38 MiB | 0 B | -19.38 MiB | -100.0% | 0 B | 0 B | 19.38 MiB | 0 B | 0 B | 0 B |
| `status.message._original` | (internal) original copy of match_only_text | 19.38 MiB | 0 B | -19.38 MiB | -100.0% | 0 B | 0 B | 19.38 MiB | 0 B | 0 B | 0 B |
| `attributes.exception.message.counts` | (internal) value counts of match_only_text | 0 B | 9.45 MiB | 9.45 MiB | - | 0 B | 0 B | 0 B | 9.45 MiB | 0 B | 0 B |
| `attributes.exception.type.counts` | (internal) value counts of keyword | 0 B | 9.45 MiB | 9.45 MiB | - | 0 B | 0 B | 0 B | 9.45 MiB | 0 B | 0 B |
| `status.message.counts` | (internal) value counts of match_only_text | 0 B | 9.45 MiB | 9.45 MiB | - | 0 B | 0 B | 0 B | 9.45 MiB | 0 B | 0 B |
| `attributes.exception.message._original.counts` | (internal) value counts | 9.45 MiB | 0 B | -9.45 MiB | -100.0% | 0 B | 0 B | 9.45 MiB | 0 B | 0 B | 0 B |
| `status.message._original.counts` | (internal) value counts | 9.45 MiB | 0 B | -9.45 MiB | -100.0% | 0 B | 0 B | 9.45 MiB | 0 B | 0 B | 0 B |
| `_field_names` | (metadata) field-name index | 8.68 MiB | 0 B | -8.68 MiB | -100.0% | 8.68 MiB | 0 B | 0 B | 0 B | 0 B | 0 B |
| `resource.attributes.k8s.namespace.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.deployment.environment.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.cloud.region.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.k8s.pod.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `scope.version.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.service.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `scope.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.host.name.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `kind.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `resource.attributes.service.version.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `trace_id.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `status.code.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `span_id.counts` | (internal) value counts of keyword | 0 B | 2.30 MiB | 2.30 MiB | - | 0 B | 0 B | 0 B | 2.30 MiB | 0 B | 0 B |
| `_recovery_source_size` | (metadata) recovery source size | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `_primary_term` | (metadata) primary term | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `__root_doc_for_nested` | (metadata) nested-document root marker | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| `_version` | (metadata) document version | 0 B | 0 B | 0 B | - | 0 B | 0 B | 0 B | 0 B | 0 B | 0 B |
| **Total (fields)** | | **16380.14 MiB** | **9822.34 MiB** | **-6557.80 MiB** | **-40.0%** | **6845.80 MiB** | **546.68 MiB** | **8505.44 MiB** | **9275.65 MiB** | | |

## Metrics (TSDS)

Index: `metrics-otel.tsds-bench`. There is no columnar counterpart for metrics, so this section shows one storage mode only.

| Component | Size |
|---|---:|
| Store size (primary, on disk) | 1112.01 MiB |
| All fields total | 1107.93 MiB |
| Inverted index | 0 B |
| Doc values | 1091.93 MiB |
| Stored fields | 0 B |
| Points (BKD) | 0 B |

> **Store size note:** the verification report (`results/es_report.json`, 22 Oct) recorded a metrics store of 1,903,391,531 bytes (1.77 GiB). The current store is 1112.01 MiB and stays the same after flush and force-merge. The cause of the earlier value is not determined. See `results/sizing_summary.json` (`store_reconciliation`).

### Per-field breakdown (sorted by size)

| Field | Type | Total | Share of all fields | Inverted index | Doc values | Stored fields | Points |
|---|---|---:|---:|---:|---:|---:|---:|
| `metrics.system.cpu.utilization` | double (gauge) | 329.65 MiB | 29.75% | 0 B | 329.65 MiB | 0 B | 0 B |
| `metrics.system.memory.usage` | long (gauge) | 209.98 MiB | 18.95% | 0 B | 209.98 MiB | 0 B | 0 B |
| `metrics.http.server.duration.p95` | double (gauge) | 181.89 MiB | 16.42% | 0 B | 181.89 MiB | 0 B | 0 B |
| `metrics.system.disk.io.read` | long (counter) | 87.61 MiB | 7.91% | 0 B | 87.61 MiB | 0 B | 0 B |
| `metrics.http.server.request.count` | long (counter) | 87.59 MiB | 7.91% | 0 B | 87.59 MiB | 0 B | 0 B |
| `metrics.system.network.io.receive` | long (counter) | 87.58 MiB | 7.90% | 0 B | 87.58 MiB | 0 B | 0 B |
| `metrics.system.network.io.transmit` | long (counter) | 87.57 MiB | 7.90% | 0 B | 87.57 MiB | 0 B | 0 B |
| `_id` | (metadata) document id | 16.00 MiB | 1.44% | 0 B | 0 B | 0 B | 0 B |
| `@timestamp` | date | 8.32 MiB | 0.75% | 0 B | 8.32 MiB | 0 B | 0 B |
| `resource.attributes.k8s.pod.name` | keyword (dimension) | 2.14 MiB | 0.19% | 0 B | 2.14 MiB | 0 B | 0 B |
| `resource.attributes.host.name` | keyword (dimension) | 1.69 MiB | 0.15% | 0 B | 1.69 MiB | 0 B | 0 B |
| `_ts_routing_hash` | (metadata) TSDS routing hash | 1.66 MiB | 0.15% | 0 B | 1.66 MiB | 0 B | 0 B |
| `resource.attributes.deployment.environment.name` | keyword | 1.27 MiB | 0.11% | 0 B | 1.27 MiB | 0 B | 0 B |
| `resource.attributes.k8s.namespace.name` | keyword (dimension) | 1.20 MiB | 0.11% | 0 B | 1.20 MiB | 0 B | 0 B |
| `resource.attributes.service.name` | keyword (dimension) | 1.08 MiB | 0.10% | 0 B | 1.08 MiB | 0 B | 0 B |
| `resource.attributes.service.version` | keyword | 1.08 MiB | 0.10% | 0 B | 1.08 MiB | 0 B | 0 B |
| `_tsid` | (metadata) TSDS time series id | 604.7 KiB | 0.05% | 0 B | 604.7 KiB | 0 B | 0 B |
| `resource.attributes.cloud.region` | keyword (dimension) | 524.6 KiB | 0.05% | 0 B | 524.6 KiB | 0 B | 0 B |
| `attributes.stream` | keyword (dimension) | 523.5 KiB | 0.05% | 0 B | 523.5 KiB | 0 B | 0 B |
| `__root_doc_for_nested` | (metadata) nested-document root marker | 0 B | 0.00% | 0 B | 0 B | 0 B | 0 B |
| `_primary_term` | (metadata) primary term | 0 B | 0.00% | 0 B | 0 B | 0 B | 0 B |
| `_recovery_source_size` | (metadata) recovery source size | 0 B | 0.00% | 0 B | 0 B | 0 B | 0 B |
| `_seq_no` | (metadata) sequence number | 0 B | 0.00% | 0 B | 0 B | 0 B | 0 B |
| `_version` | (metadata) document version | 0 B | 0.00% | 0 B | 0 B | 0 B | 0 B |
| **Total (fields)** | | **1107.93 MiB** | **100.00%** | **0 B** | **1091.93 MiB** | **0 B** | **0 B** |

