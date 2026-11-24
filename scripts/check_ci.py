#!/usr/bin/env python3
"""CI gate completeness (root scope): every `test:*` script in the ROOT
package.json must be wired into .github/workflows/ci.yml — either through its
run-script file `scripts/run/test_<name>.sh`, or, when the script delegates to a
package (`pnpm -C <pkg> <cmd>`), through that delegated command string.

Why: a suite that never runs in CI is not a gate (LL-037). The previous rule
checked the typescript package's `test:<name>` literals against ci.yml; once the
node job calls the root `scripts/run/test_ts.sh` instead of inlining
`typescript test:native`, that literal disappears and the old rule misfires. This
rule lifts the source of truth to the root package.json: each root `test:*` maps
to `scripts/run/test_<name>.sh` (multi-segment names like `test:rs:cov` map by
their first segment), and that script path must appear in ci.yml — unless the
script's value is a `pnpm -C` delegation, in which case that command must appear.

Usage: python3 scripts/check_ci.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(root: Path) -> list[str]:
    """Return the root `test:*` script names whose run-script file is missing
    from ci.yml. Empty list means every test entry is wired."""
    pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    missing = []
    for name, value in pkg.get("scripts", {}).items():
        if not name.startswith("test:"):
            continue
        # Delegation form: a root `test:<seg>` whose value is a `pnpm -C <pkg>
        # <cmd>` command has no scripts/run/test_<seg>.sh file — the suite lives
        # in that package. Require the delegated command string itself to appear
        # in ci.yml (the gate still proves the command runs). Only the `pnpm -C`
        # prefix (then a space) triggers this branch; every other value keeps the
        # bash run-script rule below.
        if value.startswith("pnpm -C "):
            if value not in ci:
                missing.append(name)
            continue
        segment = name.split(":")[1]
        # Match the `bash scripts/run/test_<seg>.sh` invocation form, not the bare
        # path: a comment mentioning the path must not satisfy the gate (the gate
        # proves the command runs, not that the path is named).
        call = f"bash scripts/run/test_{segment}.sh"
        if call not in ci:
            missing.append(name)
    return missing


def main() -> int:
    missing = check(ROOT)
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    for name in missing:
        value = pkg["scripts"][name]
        if value.startswith("pnpm -C "):
            expected = f"`{value}`"
        else:
            segment = name.split(":")[1]
            expected = f"`scripts/run/test_{segment}.sh`"
        print(
            f"::error::ci.yml never runs {expected} (root script `{name}`)",
            file=sys.stderr,
        )
    if missing:
        return 1
    tested = [n for n in pkg["scripts"] if n.startswith("test:")]
    print(f"CI gate check OK: {len(tested)} root test scripts all wired into ci.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
