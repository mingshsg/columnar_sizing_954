"""Independent check of results/field_size_report.md against the raw index disk
usage output (results/field_usage/*.disk_usage.json).

Recomputes every number in the report from the raw JSON (without reusing the
report script) and compares it with the markdown:
  - component table, per signal
  - savings sentence
  - per-field breakdown: every row, every column, and the percentage
  - text-field table (field + `._original` for logsdb)
  - totals row against the sum of the raw per-field values

Exit code 0 means no differences.

Usage: python3 scripts/verify_field_report.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIB = 1024 ** 2
TOL = 0.005 * MIB  # the report rounds to 2 decimals in MiB

SIGNALS = [
    ("logs", "logs-otel.logsdb-bench", "logs-otel.columnar-bench"),
    ("traces", "traces-otel.logsdb-bench", "traces-otel.columnar-bench"),
]


def load(ds):
    with open(os.path.join(ROOT, "results", "field_usage", "%s.disk_usage.json" % ds)) as fh:
        body = json.load(fh)
    return next(v for k, v in body.items() if k != "_shards")


def num(d, *path):
    for p in path:
        d = d.get(p, {}) if isinstance(d, dict) else {}
    return d if isinstance(d, (int, float)) else 0


def to_bytes(cell):
    s = cell.strip().replace("**", "")
    if s in ("-", ""):
        return 0.0
    m = re.match(r"([-+]?[\d.]+) (MiB|KiB|B)$", s)
    if not m:
        raise ValueError("unparseable cell: %r" % cell)
    return float(m.group(1)) * {"MiB": MIB, "KiB": 1024, "B": 1}[m.group(2)]


def field_vals(idx, name):
    f = idx["fields"].get(name, {})
    return {
        "total": num(f, "total_in_bytes"),
        "inv": num(f, "inverted_index", "total_in_bytes"),
        "dv": num(f, "doc_values_in_bytes"),
        "st": num(f, "stored_fields_in_bytes"),
    }


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def main():
    with open(os.path.join(ROOT, "results", "field_size_report.md"), encoding="utf-8") as fh:
        md = fh.read()

    problems = []
    checked = 0
    per_field_rows = 0

    for sig, a_ds, b_ds in SIGNALS:
        A, B = load(a_ds), load(b_ds)
        title = "## %s\n" % sig.capitalize()
        if title not in md:
            problems.append("%s: section missing" % sig)
            continue
        section = md.split(title, 1)[1].split("\n## ", 1)[0]
        component, rest = section.split("### Text fields", 1)
        text, per_field = rest.split("### Per-field breakdown", 1)

        # component table
        comp_want = {
            "Store size (primary, on disk)": (A["store_size_in_bytes"], B["store_size_in_bytes"]),
            "All fields total": (A["all_fields"]["total_in_bytes"], B["all_fields"]["total_in_bytes"]),
            "Inverted index": (A["all_fields"]["inverted_index"]["total_in_bytes"], B["all_fields"]["inverted_index"]["total_in_bytes"]),
            "Doc values": (A["all_fields"]["doc_values_in_bytes"], B["all_fields"]["doc_values_in_bytes"]),
            "Stored fields": (A["all_fields"]["stored_fields_in_bytes"], B["all_fields"]["stored_fields_in_bytes"]),
            "Points (BKD)": (A["all_fields"]["points_in_bytes"], B["all_fields"]["points_in_bytes"]),
        }
        seen = set()
        for line in component.splitlines():
            if not line.startswith("| ") or line.startswith("| Component") or line.startswith("|---"):
                continue
            c = cells(line)
            if c[0] in comp_want:
                seen.add(c[0])
                a, b = comp_want[c[0]]
                for got, want, label in ((to_bytes(c[1]), a, "logsdb"), (to_bytes(c[2]), b, "columnar")):
                    checked += 1
                    if abs(got - want) > TOL:
                        problems.append("%s component %s %s: md=%s raw=%d" % (sig, c[0], label, c[1 if label == "logsdb" else 2], want))
        if seen != set(comp_want):
            problems.append("%s: component rows missing %s" % (sig, sorted(set(comp_want) - seen)))

        # savings sentence
        saving = (1 - B["store_size_in_bytes"] / A["store_size_in_bytes"]) * 100
        m = re.search(r"uses ([\d.]+)% less disk", section)
        checked += 1
        if not m or abs(float(m.group(1)) - saving) > 0.06:
            problems.append("%s savings sentence: md=%s raw=%.1f" % (sig, m.group(1) if m else None, saving))

        # text table
        for line in text.splitlines():
            if not line.startswith("| `"):
                continue
            c = cells(line)
            name = c[0].strip("`")
            va = num(A["fields"].get(name, {}), "total_in_bytes") + num(A["fields"].get(name + "._original", {}), "total_in_bytes")
            vb = num(B["fields"].get(name, {}), "total_in_bytes")
            for got, want, label in ((to_bytes(c[1]), va, "logsdb+_original"), (to_bytes(c[2]), vb, "columnar")):
                checked += 1
                if abs(got - want) > TOL:
                    problems.append("%s text %s %s: md=%s raw=%d" % (sig, name, label, c[1 if label.startswith("logsdb") else 2], want))

        # per-field table: every row, every column
        rows = [l for l in per_field.splitlines() if l.startswith("| `")]
        names = [cells(l)[0].strip("`") for l in rows]
        expected = set(A["fields"]) | set(B["fields"])
        if len(names) != len(set(names)) or set(names) != expected:
            problems.append("%s per-field row set differs (missing %s, extra %s)" % (
                sig, sorted(expected - set(names)), sorted(set(names) - expected)))
        per_field_rows += len(rows)
        for line in rows:
            c = cells(line)
            name = c[0].strip("`")
            fa, fb = field_vals(A, name), field_vals(B, name)
            want = {
                1: fa["total"], 2: fb["total"], 3: fb["total"] - fa["total"],
                5: fa["inv"], 6: fb["inv"], 7: fa["dv"], 8: fb["dv"], 9: fa["st"], 10: fb["st"],
            }
            for col, w in want.items():
                checked += 1
                if abs(to_bytes(c[col]) - w) > TOL:
                    problems.append("%s %s col %d: md=%s raw=%d" % (sig, name, col, c[col], w))
            if fa["total"] and c[4] != "-":
                pct = (fb["total"] - fa["total"]) / fa["total"] * 100
                checked += 1
                if abs(float(c[4].replace("%", "").replace("+", "")) - pct) > 0.06:
                    problems.append("%s %s pct: md=%s raw=%.1f%%" % (sig, name, c[4], pct))

        # totals row against the sum of raw per-field values
        trow = [l for l in per_field.splitlines() if l.startswith("| **Total")]
        if not trow:
            problems.append("%s: totals row missing" % sig)
        else:
            c = [x.strip().strip("*") for x in cells(trow[0])]
            sum_a = sum(v.get("total_in_bytes", 0) for v in A["fields"].values())
            sum_b = sum(v.get("total_in_bytes", 0) for v in B["fields"].values())
            for got, want, label in ((to_bytes(c[1]), sum_a, "logsdb"), (to_bytes(c[2]), sum_b, "columnar")):
                checked += 1
                if abs(got - want) > TOL:
                    problems.append("%s totals %s: md=%s raw=%d" % (sig, label, c[1 if label == "logsdb" else 2], want))

    print("per-field rows: %d, values checked: %d, differences: %d" % (per_field_rows, checked, len(problems)))
    for p in problems:
        print("DIFF", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
