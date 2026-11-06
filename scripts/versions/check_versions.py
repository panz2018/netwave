#!/usr/bin/env python3
"""Version consistency rule gate — four structural laws, no registry.

Every version pin lives in the file that carries it (rust-toolchain.toml,
.python-version, pyproject.toml, package.json, .github/workflows/ci.yml).
This gate scans repo manifests against general laws and reads no manifest
list: a new subproject is covered automatically, and any violation fails on
the spot naming the offending file.

Laws:
  1. MSRV: every workspace member (root Cargo.toml `members`) carries
     `rust-version`, all values are equal, and none is above the
     rust-toolchain.toml channel (major.minor); the channel must be exact.
  2. Python project: every pyproject.toml declaring `[project]` declares
     `requires-python` and has a sibling `.python-version`.
  3. packageManager: every package.json carrying `packageManager` is an
     exact pnpm version, and all such values are equal across the repo.
  4. Matrix coverage: every .python-version pin appears among the python
     matrix cells of the CI workflows.

Whether a pin is the latest version is the job of
scripts/versions/check_outdated.py (manual, networked).

Exit codes: 0 = all laws hold, 1 = violations (each printed as ::error::).
Judgement lives in lib/rules.py; this facade selects the checks, aggregates
errors, and sets the exit code.

Usage: python3 scripts/versions/check_versions.py
"""

import sys

from lib.repository import ROOT
from lib.rules import all_laws, summary


def main() -> int:
    errors = [err for law in all_laws(ROOT) for err in law]
    if errors:
        for err in errors:
            print(f"::error::{err}", file=sys.stderr)
        return 1
    print(summary(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
