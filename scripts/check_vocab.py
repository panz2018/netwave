#!/usr/bin/env python3
"""Grep gate: no hand-copied frequency-unit string literals in the binding
sources (spec: frequency-unit "vocabulary single source").

    python3 scripts/check_vocab.py

The unit vocabulary lives ONLY in the core enum; every binding surface
discovers it by reflection (pyo3 / napi / wasm-bindgen) and every type
artifact (.pyi / .d.ts) is generated at build time. A unit name written as
a string literal in a binding source is a hand-copy that can silently drift
from core, so this gate fails the build on any occurrence.

Scanned (binding source only):
    python/src, python/netwave, python/scripts, typescript/src

Exempt by design:
    - build artifacts (.pyi / .d.ts / generated glue): generated, not
      hand-copied — they legitimately contain the names
    - test directories (python/tests, typescript/test): tests assert the
      contract with independent literals on purpose (tripwires); a core
      rename SHOULD turn them red, so they are not the drift surface

Exit code 1 on any hit. Pure stdlib; wired into `pnpm check` via
`check:meta`.
"""

import re
import sys
from pathlib import Path

# Repo root = parent of this scripts/ dir, so the gate works from any cwd.
ROOT = Path(__file__).resolve().parent.parent

# Complete unit spellings, each delimited by a quote on both sides so a
# substring inside a longer identifier or word never matches (e.g. the
# `kHz` inside a doc comment word, or `Hz` inside `MHz`).
UNITS = ("Hz", "kHz", "MHz", "GHz", "THz")
QUOTE = "\"'`"
PATTERN = re.compile(rf"[{QUOTE}](?:{'|'.join(UNITS)})[{QUOTE}]")

# Directories whose sources are scanned for hand-copied vocabulary.
SCAN_DIRS = ("python/src", "python/netwave", "python/scripts", "typescript/src")
# Extensions that are binding source (generated .pyi/.d.ts are excluded).
SOURCE_SUFFIXES = (".rs", ".py", ".ts", ".mts", ".cts", ".mjs", ".cjs", ".js")


def main() -> int:
    bad = 0
    scanned = 0
    for scan in SCAN_DIRS:
        root = ROOT / scan
        if not root.is_dir():
            print(f"VOCAB GATE: scan dir missing: {scan}", file=sys.stderr)
            return 1
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            scanned += 1
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if PATTERN.search(line):
                    print(f"VOCAB DRIFT {path}:{lineno}: {line.strip()}")
                    bad += 1
    print(
        f"scanned {scanned} binding source files;",
        "OK" if bad == 0 else f"{bad} hand-copied unit literal(s)",
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
