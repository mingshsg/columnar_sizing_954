"""Independent check of results/field_size_report.md against the raw index disk
usage output (results/field_usage/*.disk_usage.json) and the mappings
(results/config/*.mapping.json).

Recomputes every number and type in the report from the raw JSON (without
reusing the report script's logic) and compares it with the markdown:
  - logs and traces: component table, savings sentence, text-field table,
    per-field table (every row, every size column, the percentage), totals row
  - metrics: component table, per-field table (every row, every size column,
    the share of all fields), totals row
  - field types: every type cell against the mapping

Exit code 0 means no differences.

Usage: python3 scripts/verify_field_report.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import field_types as ft  # noqa: E402

MIB = 1024 ** 2
TOL = 0.005 * MIB  # the report rounds to 2 decimals in MiB

SIGNALS = [
    ("logs", "logs-otel.logsdb-bench", "logs-otel.columnar-bench"),
    ("traces", "traces-otel.logsdb-bench", "traces-otel.columnar-bench"),
]
METRICS = "metrics-otel.tsds-bench"


def load(ds):
    with open(os.path.join(ROOT, "results", "field_usage", "%s.disk_usage.json" % ds), encoding="utf-8") as fh:
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


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def vals(entry):
    return {
        "total": num(entry, "total_in_bytes"),
        "inv": num(entry, "inverted_index", "total_in_bytes"),
        "dv": num(entry, "doc_values_in_bytes"),
        "st": num(entry, "stored_fields_in_bytes"),
        "pts": num(entry, "points_in_bytes"),
    }


def main():
    with open(os.path.join(ROOT, "results", "field_size_report.md"), encoding="utf-8") as fh:
        md = fh.read()

    problems = []
    checked = 0
    per_field_rows = 0

    for sig, a_ds, b_ds in SIGNALS:
        A, B = load(a_ds), load(b_ds)
        mapped = ft.load_mapping(a_ds)
        title = "## %s\n" % sig.capitalize()
        if title not in md:
            problems.append("%s: section missing" % sig)
            continue
        section = md.split(title, 1)[1].split("\n## ", 1)[0]
        component, rest = section.split("### Text fields", 1)
        text, per_field = rest.split("### Per-field breakdown", 1)

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
                for got, want, col, label in ((to_bytes(c[1]), a, 1, "logsdb"), (to_bytes(c[2]), b, 2, "columnar")):
                    checked += 1
                    if abs(got - want) > TOL:
                        problems.append("%s component %s %s: md=%s raw=%d" % (sig, c[0], label, c[col], want))
        if seen != set(comp_want):
            problems.append("%s: component rows missing %s" % (sig, sorted(set(comp_want) - seen)))

        saving = (1 - B["store_size_in_bytes"] / A["store_size_in_bytes"]) * 100
        m = re.search(r"uses ([\d.]+)% less disk", section)
        checked += 1
        if not m or abs(float(m.group(1)) - saving) > 0.06:
            problems.append("%s savings sentence: md=%s raw=%.1f" % (sig, m.group(1) if m else None, saving))

        for line in text.splitlines():
            if not line.startswith("| `"):
                continue
            c = cells(line)
            name = c[0].strip("`")
            checked += 1
            if c[1] != ft.type_of(name, mapped):
                problems.append("%s text %s type: md=%s mapping=%s" % (sig, name, c[1], ft.type_of(name, mapped)))
            fa, fb = A["fields"], B["fields"]
            va = num(fa.get(name, {}), "total_in_bytes") + num(fa.get(name + "._original", {}), "total_in_bytes")
            vb = num(fb.get(name, {}), "total_in_bytes")
            for got, want, col, label in ((to_bytes(c[2]), va, 2, "logsdb+_original"), (to_bytes(c[3]), vb, 3, "columnar")):
                checked += 1
                if abs(got - want) > TOL:
                    problems.append("%s text %s %s: md=%s raw=%d" % (sig, name, label, c[col], want))

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
            checked += 1
            if c[1] != ft.type_of(name, mapped):
                problems.append("%s %s type: md=%s mapping=%s" % (sig, name, c[1], ft.type_of(name, mapped)))
            fa, fb = vals(A["fields"].get(name, {})), vals(B["fields"].get(name, {}))
            want = {
                2: fa["total"], 3: fb["total"], 4: fb["total"] - fa["total"],
                6: fa["inv"], 7: fb["inv"], 8: fa["dv"], 9: fb["dv"], 10: fa["st"], 11: fb["st"],
            }
            for col, w in want.items():
                checked += 1
                if abs(to_bytes(c[col]) - w) > TOL:
                    problems.append("%s %s col %d: md=%s raw=%d" % (sig, name, col, c[col], w))
            if fa["total"] and c[5] != "-":
                pct = (fb["total"] - fa["total"]) / fa["total"] * 100
                checked += 1
                if abs(float(c[5].replace("%", "").replace("+", "")) - pct) > 0.06:
                    problems.append("%s %s pct: md=%s raw=%.1f%%" % (sig, name, c[5], pct))

        trow = [l for l in per_field.splitlines() if l.startswith("| **Total")]
        if not trow:
            problems.append("%s: totals row missing" % sig)
        else:
            c = [x.strip().strip("*") for x in cells(trow[0])]
            sum_a = sum(v.get("total_in_bytes", 0) for v in A["fields"].values())
            sum_b = sum(v.get("total_in_bytes", 0) for v in B["fields"].values())
            for got, want, col, label in ((to_bytes(c[2]), sum_a, 2, "logsdb"), (to_bytes(c[3]), sum_b, 3, "columnar")):
                checked += 1
                if abs(got - want) > TOL:
                    problems.append("%s totals %s: md=%s raw=%d" % (sig, label, c[col], want))

    # metrics (TSDS, single mode)
    M = load(METRICS) if os.path.exists(os.path.join(ROOT, "results", "field_usage", "%s.disk_usage.json" % METRICS)) else None
    if M is None:
        problems.append("metrics disk usage file missing")
    else:
        mapped = ft.load_mapping(METRICS)
        title = "## Metrics (TSDS)\n"
        if title not in md:
            problems.append("metrics section missing")
        else:
            section = md.split(title, 1)[1]
            comp, per_field = section.split("### Per-field breakdown", 1)
            a = M["all_fields"]
            comp_want = {
                "Store size (primary, on disk)": M["store_size_in_bytes"],
                "All fields total": a["total_in_bytes"],
                "Inverted index": a["inverted_index"]["total_in_bytes"],
                "Doc values": a["doc_values_in_bytes"],
                "Stored fields": a["stored_fields_in_bytes"],
                "Points (BKD)": a["points_in_bytes"],
            }
            for line in comp.splitlines():
                if not line.startswith("| ") or line.startswith("| Component") or line.startswith("| Component") or line.startswith("|---"):
                    continue
                c = cells(line)
                if c[0] in comp_want:
                    checked += 1
                    if abs(to_bytes(c[1]) - comp_want[c[0]]) > TOL:
                        problems.append("metrics component %s: md=%s raw=%d" % (c[0], c[1], comp_want[c[0]]))
            rows = [l for l in per_field.splitlines() if l.startswith("| `")]
            names = [cells(l)[0].strip("`") for l in rows]
            if set(names) != set(M["fields"]) or len(names) != len(set(names)):
                problems.append("metrics per-field row set differs")
            per_field_rows += len(rows)
            total_all = M["all_fields"]["total_in_bytes"] or 1
            for line in rows:
                c = cells(line)
                name = c[0].strip("`")
                checked += 1
                if c[1] != ft.type_of(name, mapped):
                    problems.append("metrics %s type: md=%s mapping=%s" % (name, c[1], ft.type_of(name, mapped)))
                v = vals(M["fields"].get(name, {}))
                want = {2: v["total"], 4: v["inv"], 5: v["dv"], 6: v["st"], 7: v["pts"]}
                for col, w in want.items():
                    checked += 1
                    if abs(to_bytes(c[col]) - w) > TOL:
                        problems.append("metrics %s col %d: md=%s raw=%d" % (name, col, c[col], w))
                checked += 1
                if abs(float(c[3].rstrip("%")) - v["total"] / total_all * 100) > 0.006:
                    problems.append("metrics %s share: md=%s raw=%.2f%%" % (name, c[3], v["total"] / total_all * 100))
            trow = [l for l in per_field.splitlines() if l.startswith("| **Total")]
            if not trow:
                problems.append("metrics totals row missing")
            else:
                c = [x.strip().strip("*") for x in cells(trow[0])]
                sum_total = sum(vals(e)["total"] for e in M["fields"].values())
                checked += 1
                if abs(to_bytes(c[2]) - sum_total) > TOL:
                    problems.append("metrics totals: md=%s raw=%d" % (c[2], sum_total))

    print("per-field rows: %d, values and types checked: %d, differences: %d" % (per_field_rows, checked, len(problems)))
    for p in problems:
        print("DIFF", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
