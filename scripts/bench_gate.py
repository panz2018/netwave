#!/usr/bin/env python3
"""Criterion regression gate (ci-matrix spec: >20% regression MUST fail).

Reads target/criterion/<bench>/change/estimates.json written by
`cargo bench -- --baseline=<name>` and fails if any benchmark's mean
estimate of change exceeds the threshold.

Usage: python3 scripts/bench_gate.py <criterion_dir> [threshold=0.20]
"""

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
    found = False
    for est in root.glob("*/change/estimates.json"):
        found = True
        mean = json.loads(est.read_text(encoding="utf-8"))["mean"]["point_estimate"]
        name = est.parents[1].name
        if mean > threshold:
            print(f"BENCH REGRESSION: {name} +{mean:.1%} > {threshold:.0%}")
            return 1
        print(f"bench OK: {name} {mean:+.1%}")
    if not found:
        print("bench gate: no baseline comparison data (first run?) — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
