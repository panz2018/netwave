#!/usr/bin/env python3
"""CI gate completeness: every `test:*` script in typescript/package.json
must be invoked by .github/workflows/ci.yml.

Why: the browser test line landed with `test:browser` locally but was
missing from CI (LL-037) — a suite that never runs in CI is not a gate.
This turns that text rule into a machine check.

Rule: each devDependency-backed `test:<name>` script (not the bare `test`
aggregator, which is the local entry) must appear as
`typescript test:<name>` in ci.yml. Fail otherwise.

Usage: python3 scripts/check_ci.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    pkg = json.loads((ROOT / "typescript" / "package.json").read_text())
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    missing = [
        name
        for name in pkg.get("scripts", {})
        if re.fullmatch(r"test:[a-z]+", name) and f"typescript {name}" not in ci
    ]
    for name in missing:
        print(f"::error::ci.yml never runs `pnpm -C typescript {name}`", file=sys.stderr)
    if missing:
        return 1
    tested = [n for n in pkg["scripts"] if re.fullmatch(r"test:[a-z]+", n)]
    print(f"CI gate check OK: {len(tested)} test scripts all wired into ci.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
