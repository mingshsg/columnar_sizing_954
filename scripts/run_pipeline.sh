#!/usr/bin/env bash
# End-to-end benchmark pipeline. Runs in the background; each stage writes a
# marker in results/ so a re-run resumes from the first unfinished stage.
#
#   1. generate  : 100 GiB raw NDJSON each for logs, traces, metrics
#   2. validate  : full-content schema validation of every generated document
#   3. setup     : index templates, data streams, settings verification
#   4. load      : bulk ingest into the five data streams
#   5. verify    : refresh/forcemerge, settings/mapping checks, counts, field
#                  coverage, round-trip fidelity, store size and compression
#   6. report    : results/summary.md
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
mkdir -p data results logs
PY=python3
GIB=${GIB:-100}
WORKERS=${WORKERS:-4}
LOG=logs/pipeline.log

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }
fail() { log "FAILED: $*"; echo "{\"stage\":\"$CURRENT\",\"status\":\"failed\",\"detail\":\"$*\"}" > results/status.json; exit 1; }
done_marker() { [ -f "results/.done_$1" ]; }
mark() { date -u +%Y-%m-%dT%H:%M:%SZ > "results/.done_$1"; }

NOW_MS=$(( $(date -u +%s) * 1000 ))
DAY=86400000
# Metric timeline must sit inside the TSDS writable window [load-time - 7d, load-time].
# Start 6 days back; ~3.2 days of 10s ticks at 10k series fit before "now".
BASE_METRICS=$(( (NOW_MS - 6 * DAY) / 10000 * 10000 ))
BASE_LOGS=$(( NOW_MS - 4 * DAY ))
BASE_TRACES=$(( NOW_MS - 4 * DAY ))

CURRENT=generate
if ! done_marker generate; then
  log "stage generate: ${GIB} GiB per signal (base logs=$BASE_LOGS traces=$BASE_TRACES metrics=$BASE_METRICS)"
  $PY scripts/gen_otel.py logs    --out data/logs.ndjson    --target-gib "$GIB" --base-ms "$BASE_LOGS"    --seed 101 > logs/gen_logs.out 2>&1 &  p1=$!
  $PY scripts/gen_otel.py traces  --out data/traces.ndjson  --target-gib "$GIB" --base-ms "$BASE_TRACES"  --seed 202 > logs/gen_traces.out 2>&1 &  p2=$!
  $PY scripts/gen_otel.py metrics --out data/metrics.ndjson --target-gib "$GIB" --base-ms "$BASE_METRICS" --seed 303 > logs/gen_metrics.out 2>&1 &  p3=$!
  wait $p1 || fail "logs generation"
  wait $p2 || fail "traces generation"
  wait $p3 || fail "metrics generation"
  cat logs/gen_logs.out logs/gen_traces.out logs/gen_metrics.out >> "$LOG"
  mark generate
fi

CURRENT=validate
for sig in logs traces metrics; do
  if [ -f "results/validation_${sig}.json" ] && $PY -c "import json,sys; sys.exit(0 if json.load(open('results/validation_${sig}.json'))['passed'] else 1)"; then
    log "validate $sig: already passed"; continue
  fi
  log "validate $sig"
  $PY scripts/validate_files.py "$sig" "data/${sig}.ndjson" --workers "$WORKERS" --out "results/validation_${sig}.json" >> "$LOG" 2>&1 \
    || fail "validation of $sig"
done
mark validate

CURRENT=setup_load
if ! done_marker load; then
  log "setup: templates and data streams (recreated, so loads always start from empty)"
  $PY scripts/setup_es.py >> "$LOG" 2>&1 || fail "setup_es.py"
  load_one() {
    local file=$1 ds=$2
    log "load $ds from $file"
    $PY scripts/load_bulk.py --file "data/$file" --data-stream "$ds" --out "results/load_${ds}.json" --workers 3 >> "$LOG" 2>&1 \
      || fail "load of $ds"
  }
  load_one logs.ndjson    logs-otel.logsdb-bench
  load_one logs.ndjson    logs-otel.columnar-bench
  load_one traces.ndjson  traces-otel.logsdb-bench
  load_one traces.ndjson  traces-otel.columnar-bench
  load_one metrics.ndjson metrics-otel.tsds-bench
  mark load
fi

CURRENT=verify
if ! done_marker verify; then
  log "verify"
  $PY scripts/verify_es.py --results results/es_report.json >> "$LOG" 2>&1 || fail "verify_es.py (see results/es_report.json)"
  mark verify
fi

CURRENT=report
$PY scripts/report.py >> "$LOG" 2>&1 || fail "report.py"
mark report

echo "{\"stage\":\"report\",\"status\":\"complete\",\"finished\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > results/status.json
log "pipeline complete"
