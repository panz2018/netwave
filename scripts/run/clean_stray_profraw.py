#!/usr/bin/env python3
"""CLI shell over the single stray-profraw implementation (`drain_stray_profraw`
in lib.repository): delete `*.profraw` outside `target/` and fail, because such
files prove the coverage chain did not take effect. Called by ci.yml drain
steps and scripts/run/test_rs.sh.

Usage: python3 scripts/run/clean_stray_profraw.py [root]  (root defaults to
the repo root; pass a directory to scan a subtree)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "versions"))

from lib.repository import ROOT, drain_stray_profraw  # noqa: E402 — path set above


def main(argv: list[str]) -> int:
    root = Path(argv[0]) if argv else ROOT
    removed = drain_stray_profraw(root)
    if not removed:
        return 0
    names = "\n".join(f"  {p}" for p in removed)
    print(
        f"profraw outside target/ = the coverage chain did not take effect, "
        f"so coverage numbers for this run are untrustworthy "
        f"(found {len(removed)}, deleted):\n{names}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
