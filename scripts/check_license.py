#!/usr/bin/env python3
"""Validate that every publish-metadata license field matches the root
declaration (spec: license-compliance). Run from repo root:

    python3 scripts/check_license.py

Exit code 1 on any drift. Pure stdlib; added to `pnpm check` via
`check:meta`. The root declaration is the single source of truth; a
third-party license table lives in the lessons-learned ledger.
"""

import json
import re
import sys

ROOT_LICENSE = "MIT OR Apache-2.0"

CARGO_FILES = [
    "core/Cargo.toml",
    "python/Cargo.toml",
    "typescript/native/Cargo.toml",
    "typescript/wasm/Cargo.toml",
]
JSON_FILES = ["typescript/package.json"]
TOML_FILES = ["python/pyproject.toml"]

LICENSE_LINE = re.compile(r'^license\s*=\s*"([^"]+)"', re.MULTILINE)


def found_license(path: str) -> str | None:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        return json.loads(text).get("license")
    m = LICENSE_LINE.search(text)
    return m.group(1) if m else None


def main() -> int:
    bad = 0
    for path in CARGO_FILES + JSON_FILES + TOML_FILES:
        found = found_license(path)
        if found != ROOT_LICENSE:
            print(f"LICENSE DRIFT {path}: {found!r}")
            bad += 1
    print(
        f"checked {len(CARGO_FILES) + len(JSON_FILES) + len(TOML_FILES)} files;",
        "OK" if bad == 0 else f"{bad} drifted",
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
