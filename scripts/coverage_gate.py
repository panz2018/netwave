#!/usr/bin/env python3
"""Gate on cargo-llvm-cov's codecov.json (OR-merged line coverage).

Why not `--fail-under-lines`: it evaluates the `llvm-cov report` numbers,
which count every unexecuted inlined copy of a function in each integration
test binary as missed lines — even when the lib unit test executes the same
source line (upstream src/report.rs computes the percent from the report
JSON, not from the codecov export). The `--codecov` export uses
`llvm-cov show` semantics: a line executed in ANY instantiation counts as
covered (the standard line-coverage OR every other language tool uses).
This gate reads codecov.json so the 100% floor measures real line coverage
without distorting the hot path or excluding files.

Usage: coverage_gate.py [codecov.json] [floor_percent]
Exit 0 if line coverage >= floor, else 1 (missed lines printed).
"""

import json
import sys


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "codecov.json"
    floor = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    covered = 0
    total = 0
    missed: dict[str, list[int]] = {}
    for fname, lines in data["coverage"].items():
        for ln, val in lines.items():
            if not ln.isdigit():
                continue
            total += 1
            hit = int(val.partition("/")[0])
            if hit > 0:
                covered += 1
            else:
                missed.setdefault(fname, []).append(int(ln))
    percent = 100.0 * covered / total if total else 0.0
    print(f"codecov line coverage: {covered}/{total} = {percent:.2f}% (floor {floor}%)")
    for fname, lns in sorted(missed.items()):
        print(f"missed {fname}: {lns}")
    return 0 if percent >= floor else 1


if __name__ == "__main__":
    sys.exit(main())
