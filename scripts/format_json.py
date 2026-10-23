"""Reformat every JSON file under results/ and samples/ as indented, readable JSON.

- Each file is parsed, re-written with 2-space indentation and checked to be
  identical after re-parsing (no data is changed, only whitespace).
- samples/*.ndjson (one document per line) are also written as pretty JSON
  arrays alongside the originals, e.g. samples/logs.sample.json.

Usage: python3 scripts/format_json.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def format_file(path):
    with open(path, encoding="utf-8") as fh:
        original = json.load(fh)
    text = pretty(original)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    with open(path, encoding="utf-8") as fh:
        again = json.load(fh)
    if again != original:
        raise SystemExit("content changed after formatting: %s" % path)
    return True


def ndjson_to_pretty(path, out):
    docs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                docs.append(json.loads(line))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(pretty(docs))
    return len(docs)


def json_files(*dirs):
    found = []
    for d in dirs:
        for dirpath, _, files in os.walk(os.path.join(ROOT, d)):
            for name in files:
                if name.endswith(".json"):
                    found.append(os.path.join(dirpath, name))
    return sorted(found)


def main():
    formatted = []
    for path in json_files("results", "samples"):
        format_file(path)
        formatted.append(os.path.relpath(path, ROOT))

    samples_dir = os.path.join(ROOT, "samples")
    for name in sorted(os.listdir(samples_dir)):
        if not name.endswith(".ndjson"):
            continue
        path = os.path.join(samples_dir, name)
        out = path[: -len(".ndjson")] + ".json"
        n = ndjson_to_pretty(path, out)
        formatted.append("%s -> %s (%d docs)" % (os.path.relpath(path, ROOT), os.path.relpath(out, ROOT), n))

    for item in formatted:
        print("formatted", item)
    print("%d files formatted and verified" % len(formatted))


if __name__ == "__main__":
    sys.exit(main())
