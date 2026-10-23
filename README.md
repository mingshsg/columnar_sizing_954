# OpenTelemetry storage benchmark: logsdb vs logsdb_columnar vs TSDS (Elasticsearch 9.5.5)

This project measures how much disk Elasticsearch needs for 100 GiB of OpenTelemetry-shaped logs, traces and metrics under three storage modes:

- **logsdb** (synthetic `_source`) for logs and traces
- **logsdb_columnar** (synthetic `_source`) for logs and traces, technical preview in 9.5
- **time series data stream (TSDS)** for metrics

Repository: https://github.com/mingshsg/columnar_sizing_954

## Headline results

Compression ratio = raw NDJSON bytes / primary store bytes, after refresh and force-merge to one segment per shard.

| Data stream | Mode | Docs | Store size | Compression ratio |
|---|---|---:|---:|---:|
| logs-otel.logsdb-bench | logsdb | 149,147,666 | 15.86 GiB | 6.31x |
| logs-otel.columnar-bench | logsdb_columnar | 149,147,666 | 10.62 GiB | 9.42x |
| traces-otel.logsdb-bench | logsdb | 154,100,082 | 16.10 GiB | 6.21x |
| traces-otel.columnar-bench | logsdb_columnar | 154,100,082 | 9.59 GiB | 10.42x |
| metrics-otel.tsds-bench | time_series | 274,280,000 | 1.77 GiB | 56.41x |

logsdb_columnar uses 33% less disk than logsdb for logs and 40% less for traces. The metrics ratio comes from synthetic data and will be lower on real metrics (see caveats).

## Documents and reports

| Document | What it contains |
|---|---|
| [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) | Index of every configuration, sizing, validation and run file, with links and JSON checks |
| [`results/sizing_summary.json`](results/sizing_summary.json) | Readable sizing summary with human-readable sizes |
| [`results/summary.md`](results/summary.md) | Full results: generation, validation, ingestion, storage, checks and sample documents |
| [`results/field_size_report.md`](results/field_size_report.md) | Field-by-field disk usage, logsdb vs logsdb_columnar, with the text-field comparison |
| [`results/config_report.md`](results/config_report.md) | Index templates, user settings, effective settings and mappings for all five data streams |
| [`samples/`](samples/) | Sample documents per signal and their validation output |
| [`results/es_report.json`](results/es_report.json) | Machine-readable verification results |
| [`results/validation_*.json`](results) | Full-content validation results per signal |
| [`results/load_*.json`](results) | Ingestion results per data stream |
| [`results/field_usage/`](results/field_usage) | Raw `_disk_usage` output used for the field-level report |
| [`results/config/`](results/config) | Raw settings, mappings and templates captured from the cluster |
| [`logs/pipeline.log`](logs/pipeline.log) | Full log of the pipeline run |

## Repository layout

```
scripts/
  schema.py           OTel field definitions, index mappings, data stream names
  gen_otel.py         Deterministic generator for logs, traces and metrics (NDJSON)
  validate_files.py   Full-content validator (every document)
  setup_es.py         Index templates, data streams, settings verification
  load_bulk.py        Bulk loader (documents as generated, with bulk action lines added)
  verify_es.py        Force-merge, settings and mapping checks, counts, field coverage,
                      round-trip comparison, store size and compression
  field_report.py     Field-by-field storage comparison (from _disk_usage output)
  sizing_summary.py   Readable sizing summary (results/sizing_summary.json)
  config_report.py    Config reference (templates, settings, mappings)
  format_json.py      Pretty-prints every JSON file and checks it is unchanged
  build_evidence_index.py  Builds EVIDENCE_INDEX.md with links and JSON checks
  report.py           results/summary.md
  run_pipeline.sh     End-to-end pipeline with checkpoints
  common.py           Shared helpers (.env loading, authenticated session)
results/              Reports and raw outputs (see table above)
samples/              Sample documents and validation output
```

`data/` (the generated NDJSON, about 300 GiB) and `es-data/` (the Elasticsearch data directory) are not in the repository. See `.gitignore`.

## Requirements

- Linux host with Docker, Python 3.9+ and the `requests` package
- At least 20 GiB RAM for the Elasticsearch container and about 400 GiB free disk for the full run
- Elasticsearch 9.5.5 image: `docker.elastic.co/elasticsearch/elasticsearch:9.5.5`

The 9.5.6 image was not available when this benchmark ran, so 9.5.5 was used. `setup_es.py` refuses to run against any other version.

## Running the benchmark

1. Start Elasticsearch 9.5.5 with security on. Example:

   ```bash
   docker run -d --name bench-es955 -p 127.0.0.1:19455:9200 \
     -e discovery.type=single-node -e ELASTIC_PASSWORD='<password>' \
     -e xpack.security.enabled=true -e xpack.license.self_generated.type=trial \
     -e ES_JAVA_OPTS="-Xms8g -Xmx8g" --memory 20g --ulimit memlock=-1:-1 \
     -v "$PWD/es-data:/usr/share/elasticsearch/data" \
     docker.elastic.co/elasticsearch/elasticsearch:9.5.5
   ```

2. Create `.env` in the project root (it is git-ignored):

   ```
   ES_URL=http://127.0.0.1:19455
   ES_USER=elastic
   ES_PASSWORD=<password>
   ```

3. Start the trial license if it is not already active: `POST _license/start_trial?acknowledge=true`.

4. Run the pipeline in the background (it is checkpointed, so re-running resumes from the first unfinished stage):

   ```bash
   nohup bash scripts/run_pipeline.sh > logs/pipeline.out 2>&1 &
   tail -f logs/pipeline.log
   ```

   The stages are generate, validate, setup and load, verify, and report. Generation takes about 45 minutes, validation about 20 minutes and loading about 2 to 3 hours on 4 vCPUs.

5. After the pipeline finishes, generate the field-level and config reports:

   ```bash
   python3 scripts/field_report.py   # needs results/field_usage/*.json (see below)
   python3 scripts/config_report.py  # needs results/config/*.json
   ```

   `field_usage/` is produced with `POST <index>/_disk_usage?run_expensive_tasks=true` on each logs and traces backing index. `config/` is produced with `GET <data stream>/_settings` and `GET <data stream>/_mapping`. Both are plain API calls and are not done by the pipeline.

To regenerate only the raw data without Elasticsearch, run `scripts/gen_otel.py`. For example:

```bash
python3 scripts/gen_otel.py logs --out data/logs.ndjson --target-gib 100 --base-ms <epoch-ms> --seed 101
```

## Data definition

- **100 GiB** = raw NDJSON bytes of the document lines (bulk action lines are excluded). Compression ratio uses the same byte count.
- **Logs:** OTel log records with `body.text`, severity, resource attributes (`service.name`, `host.name`, `k8s.pod.name`, `k8s.namespace.name`, `cloud.region`, `deployment.environment.name`), scope and attributes. About 60% carry `trace_id` and `span_id`.
- **Traces:** spans with parent links within a trace (3 to 9 spans per trace), `kind`, `duration` in nanoseconds, `status` and HTTP or database attributes.
- **Metrics:** 2,000 pods x 5 streams = 10,000 series at a 10 s interval, with one document per series per tick. Dimensions are `resource.attributes.*` and `attributes.stream`. Counters are monotonic per series.

Text fields `body.text`, `attributes.exception.message` and `status.message` are `match_only_text` with no keyword subfield.

## Reproducibility

- Generation is deterministic for a given seed and base time. The seeds are set in `scripts/run_pipeline.sh` (101 for logs, 202 for traces, 303 for metrics). The first and last timestamps of each file are recorded in `data/*.ndjson.meta.json` (not in the repository) and in `logs/gen_*.out`.
- The metrics timeline is generated relative to the time of generation, so it always sits inside the TSDS writable window (see caveats).

## Caveats

- **Synthetic data.** The generator produces smooth, repetitive values with a limited set of names. Real telemetry will compress less, particularly metrics (56x here) and logs with more varied text.
- **Random attributes.** HTTP attributes are picked at random, independent of log level and message. Documents pass the schema, but the content is not realistic (for example a DEBUG line can carry an HTTP 500). This does not change the storage results, but it limits what the content tells you.
- **Trial license.** Synthetic `_source` requires a subscription. The results use a 30-day trial.
- **Technical preview.** `logsdb_columnar` is a technical preview in 9.5. Results may change in later releases.
- **Elasticsearch 9.5.5, not 9.5.6.** 9.5.6 was not available in the registry when this was run.
- **TSDS writable window.** A TSDS only accepts timestamps in its writable window. `index.look_back_time` is set to 7 days, so the metric timeline must sit within 7 days before the load. Loads that start more than a day after generation will be rejected.
- **Timestamp precision.** Timestamps have millisecond precision.
- **Text search.** A `match_phrase` query on `match_only_text` is very slow on 150 million documents, because the field stores no token positions and every candidate is checked against `_source`. The verifier uses a `match` query instead.
- **Dotted names.** Elasticsearch stores dotted OTel attribute names (for example `service.name`) as nested objects. The round-trip check normalizes both sides to the same form.
- **Shard count.** All data streams use 2 primary shards and 0 replicas on a single node.
- **Internal fields in disk usage.** logsdb stores `<field>._original` copies of text fields for synthetic `_source`. Columnar stores `<field>.counts` columns. Compare the text fields as a combined row (see `results/field_size_report.md`).

## License

No license has been set for this repository.
