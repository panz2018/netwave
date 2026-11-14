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

Macro-attribute exemption (pattern-driven, no line-number whitelist): an
`#[pymethods]` / `#[napi ...]` attribute on an `impl` block carries one
llvm-cov region whose count never merges back from the macro-generated
wrappers (rustc#79651), so the line shows 0 even when every method runs.
llvm-cov honors no line-level exclusion marker (LCOV_EXCL_* is lcov-perl
only; `#[coverage(off)]` is nightly-only, LL-020), so the grading layer
exempts such lines by triple condition: missed in the report + the source
line is the macro attribute + the next code line (skipping attrs/comments)
starts `impl`. A missed line whose source cannot be read is never exempted
— it stays missed and is reported as unverifiable.
"""

import json
import re
import sys

#: impl-block macro attributes whose attribute line carries the
#: never-merging region (pyo3 `#[pymethods]`, napi `#[napi]`/`#[napi(...)]`).
_MACRO_ATTR = re.compile(r"^#\[(?:pymethods|napi\b)")


def _next_code_line(lines: list[str], idx: int) -> str:
    """First code line after `lines[idx]`, skipping blanks, `//` comments
    and further attribute lines."""
    for raw in lines[idx + 1 :]:
        s = raw.strip()
        if not s or s.startswith("//") or s.startswith("#["):
            continue
        return s
    return ""


def _read_source(fname: str) -> list[str] | None:
    try:
        with open(fname, encoding="utf-8") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "codecov.json"
    floor = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    covered = 0
    total = 0
    missed: dict[str, list[int]] = {}
    exempted: dict[str, list[int]] = {}
    unverifiable: dict[str, list[int]] = {}
    src_cache: dict[str, list[str] | None] = {}
    for fname, lines in data["coverage"].items():
        for ln, val in lines.items():
            if not ln.isdigit():
                continue
            total += 1
            hit = int(val.partition("/")[0])
            if hit > 0:
                covered += 1
                continue
            lineno = int(ln)
            if fname not in src_cache:
                src_cache[fname] = _read_source(fname)
            src = src_cache[fname]
            if src is None or lineno > len(src):
                # Source unreadable: exemption cannot be verified, so the
                # line is never exempted — it stays missed (red at the
                # production floor) and is flagged unverifiable.
                missed.setdefault(fname, []).append(lineno)
                unverifiable.setdefault(fname, []).append(lineno)
                continue
            stripped = src[lineno - 1].strip()
            if _MACRO_ATTR.match(stripped) and _next_code_line(src, lineno - 1).startswith("impl"):
                exempted.setdefault(fname, []).append(lineno)
                covered += 1
            else:
                missed.setdefault(fname, []).append(lineno)
    percent = 100.0 * covered / total if total else 0.0
    print(f"codecov line coverage: {covered}/{total} = {percent:.2f}% (floor {floor}%)")
    for fname, lns in sorted(missed.items()):
        print(f"missed {fname}: {lns}")
    for fname, lns in sorted(exempted.items()):
        print(
            f"exempted {fname}: {lns} (impl-block macro attribute: llvm-cov "
            "counts the attribute line as a region that never merges back "
            "from the generated wrappers, rustc#79651)"
        )
    for fname, lns in sorted(unverifiable.items()):
        print(f"unverifiable {fname}: {lns} (source not readable: never exempted)")
    return 0 if percent >= floor else 1


if __name__ == "__main__":
    sys.exit(main())
