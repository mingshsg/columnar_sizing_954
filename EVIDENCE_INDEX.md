# Evidence index: Elasticsearch 9.5.5 OTel storage benchmark

Generated: 2026-10-23 11:23 UTC

Every file below was produced by the benchmark scripts or captured from the cluster. JSON files are pretty-printed and checked to parse. Start with the sizing summary, then use the configuration files to confirm what was applied.

## Start here

- [`results/sizing_summary.json`](results/sizing_summary.json): readable sizing summary (logsdb vs logsdb_columnar vs TSDS)
- [`results/summary.md`](results/summary.md): full results report with samples
- [`results/field_size_report.md`](results/field_size_report.md): field-by-field storage comparison
- [`results/config_report.md`](results/config_report.md): settings and mappings in one document
- [`README.md`](README.md): how the benchmark was built, how to re-run it, and caveats

## 1. Configuration applied to the cluster

Captured from the live cluster after load. One set of files per data stream.

| Data stream | Signal | Mode | Files |
|---|---|---|---|
| `logs-otel.logsdb-bench` | logs | logsdb | [data_stream](results/config/logs-otel.logsdb-bench.data_stream.json), [index_template](results/config/logs-otel.logsdb-bench.index_template.json), [settings](results/config/logs-otel.logsdb-bench.settings.json), [effective_settings](results/config/logs-otel.logsdb-bench.effective_settings.json), [mapping](results/config/logs-otel.logsdb-bench.mapping.json) |
| `logs-otel.columnar-bench` | logs | logsdb_columnar | [data_stream](results/config/logs-otel.columnar-bench.data_stream.json), [index_template](results/config/logs-otel.columnar-bench.index_template.json), [settings](results/config/logs-otel.columnar-bench.settings.json), [effective_settings](results/config/logs-otel.columnar-bench.effective_settings.json), [mapping](results/config/logs-otel.columnar-bench.mapping.json) |
| `traces-otel.logsdb-bench` | traces | logsdb | [data_stream](results/config/traces-otel.logsdb-bench.data_stream.json), [index_template](results/config/traces-otel.logsdb-bench.index_template.json), [settings](results/config/traces-otel.logsdb-bench.settings.json), [effective_settings](results/config/traces-otel.logsdb-bench.effective_settings.json), [mapping](results/config/traces-otel.logsdb-bench.mapping.json) |
| `traces-otel.columnar-bench` | traces | logsdb_columnar | [data_stream](results/config/traces-otel.columnar-bench.data_stream.json), [index_template](results/config/traces-otel.columnar-bench.index_template.json), [settings](results/config/traces-otel.columnar-bench.settings.json), [effective_settings](results/config/traces-otel.columnar-bench.effective_settings.json), [mapping](results/config/traces-otel.columnar-bench.mapping.json) |
| `metrics-otel.tsds-bench` | metrics | time_series (TSDS) | [data_stream](results/config/metrics-otel.tsds-bench.data_stream.json), [index_template](results/config/metrics-otel.tsds-bench.index_template.json), [settings](results/config/metrics-otel.tsds-bench.settings.json), [effective_settings](results/config/metrics-otel.tsds-bench.effective_settings.json), [mapping](results/config/metrics-otel.tsds-bench.mapping.json) |

## 1a. Configuration files

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`results/config/logs-otel.logsdb-bench.data_stream.json`](results/config/logs-otel.logsdb-bench.data_stream.json) | logs-otel.logsdb-bench: Data stream definition as returned by the cluster | 1015 B | valid |
| [`results/config/logs-otel.logsdb-bench.index_template.json`](results/config/logs-otel.logsdb-bench.index_template.json) | logs-otel.logsdb-bench: Index template the benchmark created (`bench-<data stream>`) | 3.72 KiB | valid |
| [`results/config/logs-otel.logsdb-bench.settings.json`](results/config/logs-otel.logsdb-bench.settings.json) | logs-otel.logsdb-bench: Settings set on the backing index (user-set only) | 810 B | valid |
| [`results/config/logs-otel.logsdb-bench.effective_settings.json`](results/config/logs-otel.logsdb-bench.effective_settings.json) | logs-otel.logsdb-bench: Effective settings including defaults that apply | 742 B | valid |
| [`results/config/logs-otel.logsdb-bench.mapping.json`](results/config/logs-otel.logsdb-bench.mapping.json) | logs-otel.logsdb-bench: Field mapping of the backing index | 4.35 KiB | valid |
| [`results/config/logs-otel.columnar-bench.data_stream.json`](results/config/logs-otel.columnar-bench.data_stream.json) | logs-otel.columnar-bench: Data stream definition as returned by the cluster | 1.01 KiB | valid |
| [`results/config/logs-otel.columnar-bench.index_template.json`](results/config/logs-otel.columnar-bench.index_template.json) | logs-otel.columnar-bench: Index template the benchmark created (`bench-<data stream>`) | 3.73 KiB | valid |
| [`results/config/logs-otel.columnar-bench.settings.json`](results/config/logs-otel.columnar-bench.settings.json) | logs-otel.columnar-bench: Settings set on the backing index (user-set only) | 823 B | valid |
| [`results/config/logs-otel.columnar-bench.effective_settings.json`](results/config/logs-otel.columnar-bench.effective_settings.json) | logs-otel.columnar-bench: Effective settings including defaults that apply | 753 B | valid |
| [`results/config/logs-otel.columnar-bench.mapping.json`](results/config/logs-otel.columnar-bench.mapping.json) | logs-otel.columnar-bench: Field mapping of the backing index | 2.12 KiB | valid |
| [`results/config/traces-otel.logsdb-bench.data_stream.json`](results/config/traces-otel.logsdb-bench.data_stream.json) | traces-otel.logsdb-bench: Data stream definition as returned by the cluster | 1023 B | valid |
| [`results/config/traces-otel.logsdb-bench.index_template.json`](results/config/traces-otel.logsdb-bench.index_template.json) | traces-otel.logsdb-bench: Index template the benchmark created (`bench-<data stream>`) | 3.77 KiB | valid |
| [`results/config/traces-otel.logsdb-bench.settings.json`](results/config/traces-otel.logsdb-bench.settings.json) | traces-otel.logsdb-bench: Settings set on the backing index (user-set only) | 814 B | valid |
| [`results/config/traces-otel.logsdb-bench.effective_settings.json`](results/config/traces-otel.logsdb-bench.effective_settings.json) | traces-otel.logsdb-bench: Effective settings including defaults that apply | 744 B | valid |
| [`results/config/traces-otel.logsdb-bench.mapping.json`](results/config/traces-otel.logsdb-bench.mapping.json) | traces-otel.logsdb-bench: Field mapping of the backing index | 4.09 KiB | valid |
| [`results/config/traces-otel.columnar-bench.data_stream.json`](results/config/traces-otel.columnar-bench.data_stream.json) | traces-otel.columnar-bench: Data stream definition as returned by the cluster | 1.02 KiB | valid |
| [`results/config/traces-otel.columnar-bench.index_template.json`](results/config/traces-otel.columnar-bench.index_template.json) | traces-otel.columnar-bench: Index template the benchmark created (`bench-<data stream>`) | 3.79 KiB | valid |
| [`results/config/traces-otel.columnar-bench.settings.json`](results/config/traces-otel.columnar-bench.settings.json) | traces-otel.columnar-bench: Settings set on the backing index (user-set only) | 827 B | valid |
| [`results/config/traces-otel.columnar-bench.effective_settings.json`](results/config/traces-otel.columnar-bench.effective_settings.json) | traces-otel.columnar-bench: Effective settings including defaults that apply | 755 B | valid |
| [`results/config/traces-otel.columnar-bench.mapping.json`](results/config/traces-otel.columnar-bench.mapping.json) | traces-otel.columnar-bench: Field mapping of the backing index | 2.16 KiB | valid |
| [`results/config/metrics-otel.tsds-bench.data_stream.json`](results/config/metrics-otel.tsds-bench.data_stream.json) | metrics-otel.tsds-bench: Data stream definition as returned by the cluster | 1.19 KiB | valid |
| [`results/config/metrics-otel.tsds-bench.index_template.json`](results/config/metrics-otel.tsds-bench.index_template.json) | metrics-otel.tsds-bench: Index template the benchmark created (`bench-<data stream>`) | 5.58 KiB | valid |
| [`results/config/metrics-otel.tsds-bench.settings.json`](results/config/metrics-otel.tsds-bench.settings.json) | metrics-otel.tsds-bench: Settings set on the backing index (user-set only) | 1.22 KiB | valid |
| [`results/config/metrics-otel.tsds-bench.effective_settings.json`](results/config/metrics-otel.tsds-bench.effective_settings.json) | metrics-otel.tsds-bench: Effective settings including defaults that apply | 1007 B | valid |
| [`results/config/metrics-otel.tsds-bench.mapping.json`](results/config/metrics-otel.tsds-bench.mapping.json) | metrics-otel.tsds-bench: Field mapping of the backing index | 4.62 KiB | valid |

## 2. Sizing

Storage numbers and their breakdown.

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`results/sizing_summary.json`](results/sizing_summary.json) | Readable sizing summary with human-readable sizes, field types, per-structure breakdown, per-field comparison (logs, traces) and per-field metrics, plus the store reconciliation | 52.80 KiB | valid |
| [`results/es_report.json`](results/es_report.json) | Verification results per data stream: counts, field coverage, round-trip, store size, compression, mapping and settings checks | 11.21 KiB | valid |
| [`results/field_size_report.md`](results/field_size_report.md) | Field-by-field disk usage report (markdown) | 23.32 KiB | - |
| [`results/field_usage/logs-otel.logsdb-bench.disk_usage.json`](results/field_usage/logs-otel.logsdb-bench.disk_usage.json) | Raw index disk usage output from Elasticsearch (`_disk_usage`) for logs-otel.logsdb-bench | 23.00 KiB | valid |
| [`results/field_usage/logs-otel.columnar-bench.disk_usage.json`](results/field_usage/logs-otel.columnar-bench.disk_usage.json) | Raw index disk usage output from Elasticsearch (`_disk_usage`) for logs-otel.columnar-bench | 31.60 KiB | valid |
| [`results/field_usage/traces-otel.logsdb-bench.disk_usage.json`](results/field_usage/traces-otel.logsdb-bench.disk_usage.json) | Raw index disk usage output from Elasticsearch (`_disk_usage`) for traces-otel.logsdb-bench | 23.57 KiB | valid |
| [`results/field_usage/traces-otel.columnar-bench.disk_usage.json`](results/field_usage/traces-otel.columnar-bench.disk_usage.json) | Raw index disk usage output from Elasticsearch (`_disk_usage`) for traces-otel.columnar-bench | 34.02 KiB | valid |
| [`results/field_usage/metrics-otel.tsds-bench.disk_usage.json`](results/field_usage/metrics-otel.tsds-bench.disk_usage.json) | Raw index disk usage output from Elasticsearch (`_disk_usage`) for metrics-otel.tsds-bench | 15.75 KiB | valid |

## 3. Validation of the generated data

Full-content checks on every generated document. Pass/fail is in each file.

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`results/validation_logs.json`](results/validation_logs.json) | Full-file validation result for logs (149,147,666 documents) | 514 B | valid |
| [`results/validation_traces.json`](results/validation_traces.json) | Full-file validation result for traces (154,100,082 spans) | 511 B | valid |
| [`results/validation_metrics.json`](results/validation_metrics.json) | Full-file validation result for metrics (274,280,000 documents) | 543 B | valid |
| [`samples/validation_logs.sample.json`](samples/validation_logs.sample.json) | Validation of the 5 sample documents for logs | 450 B | valid |
| [`samples/validation_traces.sample.json`](samples/validation_traces.sample.json) | Validation of the 5 sample documents for traces | 479 B | valid |
| [`samples/validation_metrics.sample.json`](samples/validation_metrics.sample.json) | Validation of the 5 sample documents for metrics | 453 B | valid |

## 4. Sample documents

Real documents from the generated files. `.json` is the readable form; `.ndjson` is the original one-per-line form.

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`samples/logs.sample.json`](samples/logs.sample.json) | Five sample logs documents, pretty-printed | 4.56 KiB | valid |
| [`samples/traces.sample.json`](samples/traces.sample.json) | Five sample traces documents, pretty-printed | 4.50 KiB | valid |
| [`samples/metrics.sample.json`](samples/metrics.sample.json) | Five sample metrics documents, pretty-printed | 2.79 KiB | valid |
| [`samples/logs.sample.ndjson`](samples/logs.sample.ndjson) | Five sample logs documents, one per line (original form) | 3.46 KiB | - |
| [`samples/traces.sample.ndjson`](samples/traces.sample.ndjson) | Five sample traces documents, one per line (original form) | 3.39 KiB | - |
| [`samples/metrics.sample.ndjson`](samples/metrics.sample.ndjson) | Five sample metrics documents, one per line (original form) | 1.85 KiB | - |

## 5. Ingestion

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`results/load_logs-otel.logsdb-bench.json`](results/load_logs-otel.logsdb-bench.json) | Ingestion result for logs-otel.logsdb-bench: documents indexed, failures, rate | 317 B | valid |
| [`results/load_logs-otel.columnar-bench.json`](results/load_logs-otel.columnar-bench.json) | Ingestion result for logs-otel.columnar-bench: documents indexed, failures, rate | 320 B | valid |
| [`results/load_traces-otel.logsdb-bench.json`](results/load_traces-otel.logsdb-bench.json) | Ingestion result for traces-otel.logsdb-bench: documents indexed, failures, rate | 321 B | valid |
| [`results/load_traces-otel.columnar-bench.json`](results/load_traces-otel.columnar-bench.json) | Ingestion result for traces-otel.columnar-bench: documents indexed, failures, rate | 324 B | valid |
| [`results/load_metrics-otel.tsds-bench.json`](results/load_metrics-otel.tsds-bench.json) | Ingestion result for metrics-otel.tsds-bench: documents indexed, failures, rate | 322 B | valid |

## 6. Run records

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`results/status.json`](results/status.json) | Pipeline completion status | 86 B | valid |
| [`logs/pipeline.log`](logs/pipeline.log) | Full log of the pipeline run (generate, validate, setup, load, verify, report) | 18.94 KiB | - |
| [`logs/gen_logs.out`](logs/gen_logs.out) | Generator output for logs (document count, bytes, timestamps) | 278 B | - |
| [`logs/gen_traces.out`](logs/gen_traces.out) | Generator output for traces | 282 B | - |
| [`logs/gen_metrics.out`](logs/gen_metrics.out) | Generator output for metrics | 285 B | - |
| [`logs/pull_es956.log`](logs/pull_es956.log) | Record of the failed pull of Elasticsearch 9.5.6 (not in the registry), which led to using 9.5.5 | 139 B | - |

## 7. Scripts

| File | What it contains | Size | JSON check |
|---|---|---:|---|
| [`scripts/build_evidence_index.py`](scripts/build_evidence_index.py) | Builds this index | 9.10 KiB | - |
| [`scripts/common.py`](scripts/common.py) | Shared helpers: .env loading and authenticated session | 715 B | - |
| [`scripts/config_report.py`](scripts/config_report.py) | Configuration reference (markdown with embedded JSON) | 4.46 KiB | - |
| [`scripts/field_report.py`](scripts/field_report.py) | Field-by-field storage comparison (markdown) | 9.98 KiB | - |
| [`scripts/field_types.py`](scripts/field_types.py) | Field types from the captured mappings; used by the field and sizing reports | 2.49 KiB | - |
| [`scripts/format_json.py`](scripts/format_json.py) | Pretty-prints every JSON file and checks it is unchanged | 2.26 KiB | - |
| [`scripts/gen_otel.py`](scripts/gen_otel.py) | Deterministic generator for logs, traces and metrics (NDJSON) | 12.30 KiB | - |
| [`scripts/load_bulk.py`](scripts/load_bulk.py) | Bulk loader that writes the generated documents to a data stream | 4.77 KiB | - |
| [`scripts/report.py`](scripts/report.py) | Main results report (summary.md) | 6.92 KiB | - |
| [`scripts/run_pipeline.sh`](scripts/run_pipeline.sh) | End-to-end pipeline with checkpoints | 3.82 KiB | - |
| [`scripts/schema.py`](scripts/schema.py) | OTel field definitions, index mappings and data stream names | 5.00 KiB | - |
| [`scripts/setup_es.py`](scripts/setup_es.py) | Creates index templates and data streams; verifies settings | 4.00 KiB | - |
| [`scripts/sizing_summary.py`](scripts/sizing_summary.py) | Readable sizing summary (JSON) | 8.22 KiB | - |
| [`scripts/validate_files.py`](scripts/validate_files.py) | Full-content validator: schema, formats, enums, counters | 13.36 KiB | - |
| [`scripts/verify_es.py`](scripts/verify_es.py) | Post-load checks: counts, mappings, settings, field coverage, round-trip, store size | 12.89 KiB | - |
| [`scripts/verify_field_report.py`](scripts/verify_field_report.py) | Independent check that every number in field_size_report.md matches the raw disk usage output | 11.12 KiB | - |

## Reproducing the evidence

1. Run `scripts/run_pipeline.sh` (see README).
2. Capture disk usage for the four logs and traces indices with `POST <index>/_disk_usage?run_expensive_tasks=true`, saving each response as `results/field_usage/<data stream>.disk_usage.json`.
3. Run `scripts/field_report.py`, `scripts/sizing_summary.py`, `scripts/config_report.py`, `scripts/format_json.py` and `scripts/build_evidence_index.py`.

