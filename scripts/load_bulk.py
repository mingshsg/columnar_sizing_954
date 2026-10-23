"""Bulk-load an NDJSON document file into an Elasticsearch data stream.

Adds a bulk "create" action line before each document (documents are written
exactly as generated). Writes a JSON result file with timing and error counts.

Usage:
  python3 load_bulk.py --file data/logs.ndjson --data-stream logs-otel.logsdb-bench --out results/load_logs-otel.logsdb-bench.json
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import es_session  # noqa: E402

ACTION = '{"create":{}}\n'


def batches(path, max_bytes, max_docs):
    buf, size, docs = [], 0, 0
    with open(path, "rb", buffering=16 * 1024 * 1024) as fh:
        for raw in fh:
            buf.append(ACTION.encode() + raw)
            size += len(raw) + len(ACTION)
            docs += 1
            if size >= max_bytes or len(buf) >= max_docs:
                yield b"".join(buf), len(buf)
                buf, size = [], 0
    if buf:
        yield b"".join(buf), len(buf)


def send(session, url, body, docs, attempt=0):
    r = session.post(url, data=body, headers={"Content-Type": "application/x-ndjson"}, timeout=1800)
    if r.status_code == 429 and attempt < 10:
        time.sleep(min(30, 2 ** attempt))
        return send(session, url, body, docs, attempt + 1)
    if r.status_code >= 300:
        return {"docs": docs, "ok": 0, "failed": docs, "http_error": r.status_code, "reason": r.text[:500], "error_samples": []}
    res = r.json()
    if not res.get("errors"):
        return {"docs": docs, "ok": docs, "failed": 0, "error_samples": []}
    ok = failed = 0
    samples = []
    for item in res["items"]:
        op = item.get("create") or item.get("index") or {}
        if op.get("status", 500) < 300:
            ok += 1
        else:
            failed += 1
            if len(samples) < 5:
                samples.append(op.get("error"))
    return {"docs": docs, "ok": ok, "failed": failed, "error_samples": samples}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--data-stream", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch-mb", type=float, default=8.0)
    ap.add_argument("--batch-docs", type=int, default=20000)
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    session, base = es_session()
    url = "%s/%s/_bulk" % (base, args.data_stream)
    total = {"docs": 0, "ok": 0, "failed": 0, "http_errors": 0}
    samples = []
    file_bytes = os.path.getsize(args.file)
    started = time.time()
    last_report = started
    max_bytes = int(args.batch_mb * 1024 * 1024)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = set()
        for body, n in batches(args.file, max_bytes, args.batch_docs):
            pending.add(pool.submit(send, session, url, body, n))
            while len(pending) >= args.workers * 2:
                done = next(as_completed(pending))
                pending.remove(done)
                _collect(done.result(), total, samples)
            now = time.time()
            if now - last_report >= 60:
                last_report = now
                el = now - started
                print("%s docs=%d ok=%d failed=%d rate=%.0f docs/s elapsed=%.0fs" % (
                    args.data_stream, total["docs"], total["ok"], total["failed"], total["docs"] / el, el), flush=True)
        for fut in as_completed(pending):
            _collect(fut.result(), total, samples)

    elapsed = time.time() - started
    result = {
        "data_stream": args.data_stream,
        "file": os.path.basename(args.file),
        "file_bytes": file_bytes,
        "docs_sent": total["docs"],
        "docs_indexed": total["ok"],
        "docs_failed": total["failed"],
        "http_errors": total["http_errors"],
        "error_samples": samples[:10],
        "seconds": round(elapsed, 1),
        "docs_per_second": round(total["docs"] / elapsed, 1),
        "mb_per_second": round(file_bytes / elapsed / 1e6, 2),
        "completed": total["failed"] == 0 and total["http_errors"] == 0 and total["docs"] > 0,
    }
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result))
    if not result["completed"]:
        sys.exit(1)


def _collect(res, total, samples):
    total["docs"] += res["docs"]
    total["ok"] += res["ok"]
    total["failed"] += res["failed"]
    if res.get("http_error"):
        total["http_errors"] += 1
    for s in res.get("error_samples", []):
        if len(samples) < 10:
            samples.append(s)
    if res.get("http_error") and len(samples) < 10:
        samples.append({"http_error": res["http_error"], "reason": res.get("reason")})


if __name__ == "__main__":
    main()
