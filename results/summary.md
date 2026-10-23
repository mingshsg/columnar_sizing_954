# OpenTelemetry compression benchmark: Elasticsearch 9.5.5

Generated: 2026-10-23 11:23:48 UTC

## Cluster

- Elasticsearch version: 9.5.5
- License: trial
- Overall verification: PASSED

## 1. Generated data (raw NDJSON, one document per line)

| Signal | Documents | Raw bytes | Bytes/doc | First timestamp | Last timestamp |
|---|---:|---:|---:|---|---|
| logs | 149,147,666 | 100.00 GiB | 719.9 | 2026-10-18T11:48:03.000Z | 2026-10-20T05:13:53.896Z |
| traces | 154,100,082 | 100.00 GiB | 696.8 | 2026-10-18T11:48:03.000Z | 2026-10-19T09:12:12.376Z |
| metrics | 274,280,000 | 100.00 GiB | 391.5 | 2026-10-16T11:48:00.000Z | 2026-10-19T15:59:20.000Z |

## 2. Validation (full content, every document)

| Signal | Docs checked | Docs with errors | Errors | Result |
|---|---:|---:|---:|---|
| logs | 149,147,666 | 0 | 0 | PASS |
| traces | 154,100,082 | 0 | 0 | PASS |
| metrics | 274,280,000 | 0 | 0 | PASS |

## 3. Ingestion

| Data stream | Mode | Docs indexed | Failed | Seconds | Docs/s | MB/s (raw) |
|---|---|---:|---:|---:|---:|---:|
| logs-otel.columnar-bench | logsdb_columnar | 149,147,666 | 0 | 1309 | 113947 | 82.0 |
| logs-otel.logsdb-bench | logsdb | 149,147,666 | 0 | 1770 | 84247 | 60.6 |
| metrics-otel.tsds-bench | time_series | 274,280,000 | 0 | 2579 | 106364 | 41.6 |
| traces-otel.columnar-bench | logsdb_columnar | 154,100,082 | 0 | 1200 | 128469 | 89.5 |
| traces-otel.logsdb-bench | logsdb | 154,100,082 | 0 | 1723 | 89429 | 62.3 |

## 4. Storage and compression (after refresh + force-merge to 1 segment)

Compression ratio = raw NDJSON bytes / primary store bytes.

| Data stream | Docs | Raw size | Store size (primary) | Compression ratio | Bytes/doc on disk | Round-trip identical |
|---|---:|---:|---:|---:|---:|---|
| logs-otel.logsdb-bench | 149,147,666 | 100.00 GiB | 15.86 GiB | 6.31x | 114.2 | yes |
| logs-otel.columnar-bench | 149,147,666 | 100.00 GiB | 10.62 GiB | 9.42x | 76.4 | yes |
| traces-otel.logsdb-bench | 154,100,082 | 100.00 GiB | 16.10 GiB | 6.21x | 112.2 | yes |
| traces-otel.columnar-bench | 154,100,082 | 100.00 GiB | 9.59 GiB | 10.42x | 66.8 | yes |
| metrics-otel.tsds-bench | 274,280,000 | 100.00 GiB | 1.77 GiB | 56.41x | 6.9 | yes |

### Checks per data stream

- **logs-otel.logsdb-bench**: PASS (mode logsdb, 149,147,666 docs)
- **logs-otel.columnar-bench**: PASS (mode logsdb_columnar, 149,147,666 docs)
- **traces-otel.logsdb-bench**: PASS (mode logsdb, 154,100,082 docs)
- **traces-otel.columnar-bench**: PASS (mode logsdb_columnar, 154,100,082 docs)
- **metrics-otel.tsds-bench**: PASS (mode time_series, 274,280,000 docs)

> **Metrics store note:** the metrics store recorded here (1.77 GiB, compression 56.4x) could not be reproduced on 23 Oct. The current store is 1.09 GiB, which gives about 92x. Both values are kept. See `sizing_summary.json` (`store_reconciliation`) for the comparison and the open question. The headline metrics figure needs to be chosen before publishing.

### Storage comparison (logs and traces, same raw data)

- logs: logsdb_columnar is 1.49x smaller than logsdb (10.62 GiB vs 15.86 GiB)
- traces: logsdb_columnar is 1.68x smaller than logsdb (9.59 GiB vs 16.10 GiB)

## Sample documents (reference)

Two documents per signal, taken from the generated files (first line and one line from the middle of the file). All 15 samples pass the schema validation. Full samples are in `samples/`.

### logs sample 1

```json
{
  "@timestamp": "2026-10-18T11:48:03.001Z",
  "observed_timestamp": "2026-10-18T11:48:03.022Z",
  "severity_text": "DEBUG",
  "severity_number": 5,
  "body": {
    "text": "Query plan cached key=ord-4577665662 hits=369"
  },
  "resource": {
    "attributes": {
      "service.name": "cart-proxy",
      "service.version": "1.14.0",
      "host.name": "node-0082",
      "k8s.pod.name": "cart-proxy-1e2-8a927",
      "k8s.namespace.name": "platform",
      "cloud.region": "eu-west-1",
      "deployment.environment.name": "staging"
    }
  },
  "scope": {
    "name": "app.logger",
    "version": "2.4.1"
  },
  "attributes": {
    "thread.name": "http-nio-8080-exec-90",
    "http.request.method": "POST",
    "http.response.status_code": 500,
    "url.path": "/api/v1/shipping/quote",
    "app.order.id": "ord-4577665662",
    "app.cart.items": 12
  },
  "trace_id": "7d170547122129108887db216fb5b54a",
  "span_id": "ad5d3271471be40c"
}
```

### logs sample 2

```json
{
  "@timestamp": "2026-10-19T03:07:43.306Z",
  "observed_timestamp": "2026-10-19T03:07:43.321Z",
  "severity_text": "INFO",
  "severity_number": 9,
  "body": {
    "text": "Cache refreshed for /api/v1/search entries=816"
  },
  "resource": {
    "attributes": {
      "service.name": "checkout-proxy",
      "service.version": "1.6.5",
      "host.name": "node-0126",
      "k8s.pod.name": "checkout-proxy-7e-7287b",
      "k8s.namespace.name": "shop-prod",
      "cloud.region": "eu-west-1",
      "deployment.environment.name": "production"
    }
  },
  "scope": {
    "name": "io.opentelemetry.http",
    "version": "1.32.0"
  },
  "attributes": {
    "thread.name": "http-nio-8080-exec-188",
    "http.request.method": "DELETE",
    "http.response.status_code": 200,
    "url.path": "/api/v1/search"
  }
}
```

### traces sample 1

```json
{
  "@timestamp": "2026-10-18T11:48:03.002Z",
  "trace_id": "886fef75dd2e86c04f17376c0162dcd6",
  "span_id": "8c99b596ce345609",
  "name": "POST /api/v1/search",
  "kind": "SPAN_KIND_SERVER",
  "duration": 507000000,
  "status": {
    "code": "STATUS_CODE_UNSET"
  },
  "resource": {
    "attributes": {
      "service.name": "gateway-batch",
      "service.version": "1.18.5",
      "host.name": "node-0119",
      "k8s.pod.name": "gateway-batch-45f-d127d",
      "k8s.namespace.name": "observability",
      "cloud.region": "ap-southeast-1",
      "deployment.environment.name": "staging"
    }
  },
  "scope": {
    "name": "io.opentelemetry.http",
    "version": "1.32.0"
  },
  "attributes": {
    "http.request.method": "POST",
    "http.route": "/api/v1/search",
    "http.response.status_code": 404,
    "server.address": "gateway-batch-api"
  }
}
```

### traces sample 2

```json
{
  "@timestamp": "2026-10-18T19:43:15.107Z",
  "trace_id": "94bf9a4feca469ebc247290d21cee555",
  "span_id": "be5d9b1dfc6be5dc",
  "parent_span_id": "4794a3a9460165d6",
  "name": "PUT /api/v1/orders/134060",
  "kind": "SPAN_KIND_INTERNAL",
  "duration": 19280000,
  "status": {
    "code": "STATUS_CODE_UNSET"
  },
  "resource": {
    "attributes": {
      "service.name": "shipping-batch",
      "service.version": "1.19.3",
      "host.name": "node-0191",
      "k8s.pod.name": "shipping-batch-6ff-c8cf8",
      "k8s.namespace.name": "observability",
      "cloud.region": "ap-southeast-1",
      "deployment.environment.name": "staging"
    }
  },
  "scope": {
    "name": "io.opentelemetry.http",
    "version": "1.32.0"
  },
  "attributes": {
    "http.request.method": "PUT",
    "http.route": "/api/v1/orders/134060",
    "http.response.status_code": 404,
    "server.address": "shipping-batch-api"
  }
}
```

### metrics sample 1

```json
{
  "@timestamp": "2026-10-16T11:48:00.000Z",
  "resource": {
    "attributes": {
      "service.name": "cart-api",
      "service.version": "1.1.3",
      "host.name": "node-0000",
      "k8s.pod.name": "cart-api-0-a155d",
      "k8s.namespace.name": "shop-prod",
      "cloud.region": "us-east-1",
      "deployment.environment.name": "production"
    }
  },
  "attributes": {
    "stream": "cpu"
  },
  "metrics": {
    "system": {
      "cpu": {
        "utilization": 0.5855
      }
    }
  }
}
```

### metrics sample 2

```json
{
  "@timestamp": "2026-10-17T15:59:30.000Z",
  "resource": {
    "attributes": {
      "service.name": "notification-api",
      "service.version": "1.18.3",
      "host.name": "node-0152",
      "k8s.pod.name": "notification-api-228-a869f",
      "k8s.namespace.name": "shop-prod",
      "cloud.region": "us-east-1",
      "deployment.environment.name": "production"
    }
  },
  "attributes": {
    "stream": "memory"
  },
  "metrics": {
    "system": {
      "memory": {
        "usage": 3621841744
      }
    }
  }
}
```

## Detailed reports

- `field_size_report.md`: field-by-field storage comparison, logsdb vs logsdb_columnar
- `config_report.md`: index templates, settings, effective settings and mappings for every data stream
- `../README.md`: how the benchmark was built and how to re-run it, with caveats

## Notes

- 100 GiB = raw NDJSON document bytes (no bulk action lines), per the agreed definition.
- Mappings: `body.text`, `status.message` and `attributes.exception.message` are `match_only_text` with no keyword subfield.
- Logs and traces use synthetic `_source` in both logsdb and logsdb_columnar.
- Metrics use a time series data stream (TSDS) with 10k series at a 10 s interval.
- ES maps dotted OTel attribute names (for example `service.name`) as nested objects. The round-trip check normalizes both sides the same way.
