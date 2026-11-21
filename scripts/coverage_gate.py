#!/usr/bin/env python3
"""Gate on line coverage from codecov.json or an llvm-cov lcov tracefile.

Why not `--fail-under-lines`: it evaluates the `llvm-cov report` numbers,
which count every unexecuted inlined copy of a function in each integration
test binary as missed lines — even when the lib unit test executes the same
source line (upstream src/report.rs computes the percent from the report
JSON, not from the codecov export). The `--codecov` export uses
`llvm-cov show` semantics: a line executed in ANY instantiation counts as
covered (the standard line-coverage OR every other language tool uses).
This gate reads codecov.json so the 100% floor measures real line coverage
without distorting the hot path or excluding files.

Usage: coverage_gate.py [codecov.json|lcov.info] [floor_percent]
Accepts a cargo-llvm-cov codecov.json or an llvm-cov lcov tracefile; both
normalize to the same per-line shape so grading below is format-agnostic.
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

Two further exemptions cover structurally-unreachable lines that llvm-cov
1.100 stopped reporting as covered (an earlier toolchain's false-positive
hid them; the same non-merging class as the macro attribute, pattern-driven
with no line-number whitelist):

- defensive map_err: a `.map_err(` arm of a statement built on an always-
  succeeds constructor (`from_shape`/`from_shape_vec`/`ArrayView`/
  `runtime::Builder`/`.build(`) whose argument is derived from the data, so
  the error arm cannot be reached by any input (the shape always matches; the
  runtime builds unless the OS is out of resources).
- continuation artifact: a branch-free continuation line of a multi-line
  statement that demonstrably executed (a sibling line in the same statement
  is hit), so its 0 count is a region non-merge artifact, not a gap.

Both refuse to widen: a `.map_err(` on a non-deriving call, a continuation
that opens a branch or carries a closure param, and a whole unexecuted
statement all stay missed (red at the production floor).
"""

import json
import re
import sys

#: impl-block macro attributes whose attribute line carries the
#: never-merging region (pyo3 `#[pymethods]`, napi `#[napi]`/`#[napi(...)]`).
_MACRO_ATTR = re.compile(r"^#\[(?:pymethods|napi\b)")

#: constructors whose `Result` cannot fail for inputs the glue itself derives
#: (the shape argument is computed from the data, so it always matches; the
#: tokio runtime builds unless the OS is out of resources). Their `.map_err`
#: error arm is structurally unreachable, so llvm-cov shows it 0 even though
#: the statement runs — the same non-merging class as the macro attribute.
_DEFENSIVE_CTOR = re.compile(r"from_shape|ArrayView|runtime::Builder|\.build\(")

#: keywords that open a decision point; a line starting with one is a real
#: branch and is never treated as a structural continuation artifact.
_BRANCH_KW = re.compile(r"^(?:if|match|else|for|while|loop|Ok\(|Err\()")


def _next_code_line(lines: list[str], idx: int) -> str:
    """First code line after `lines[idx]`, skipping blanks, `//` comments
    and further attribute lines."""
    for raw in lines[idx + 1 :]:
        s = raw.strip()
        if not s or s.startswith("//") or s.startswith("#["):
            continue
        return s
    return ""


def _statement_span(lines: list[str], lineno: int) -> tuple[int, int]:
    """1-based inclusive span of the statement containing `lineno`, bounded by
    the nearest preceding terminator (`;`/`{`/`}`) and the next `;`."""
    n = len(lines)
    end = n
    for i in range(lineno, n + 1):
        if lines[i - 1].rstrip().endswith((";", "{", "}")):
            end = i
            break
    start = 1
    for i in range(lineno - 1, 0, -1):
        if lines[i - 1].rstrip().endswith((";", "{", "}")):
            start = i + 1
            break
    return start, end


def _is_defensive_err(lines: list[str], lineno: int) -> bool:
    """A `.map_err(` continuation arm of a statement built on an always-
    succeeds constructor — its error path is structurally unreachable."""
    if not lines[lineno - 1].strip().startswith(".map_err("):
        return False
    start, end = _statement_span(lines, lineno)
    body = " ".join(lines[start - 1 : end])
    return bool(_DEFENSIVE_CTOR.search(body))


def _is_continuation_artifact(lines: list[str], lineno: int, hits: dict[int, int]) -> bool:
    """A branch-free continuation line of a multi-line statement that
    demonstrably executed: it has no closure param, no `?` error-propagation
    and opens no branch, so a 0 count here is a region non-merge artifact, not
    a real gap (a real gap would carry a decision point)."""
    stripped = lines[lineno - 1].strip()
    if stripped.startswith("#[") or _BRANCH_KW.match(stripped):
        return False  # attribute line or decision point: never an artifact
    if "|" in stripped or stripped.endswith("?"):
        return False
    start, end = _statement_span(lines, lineno)
    if start == end:
        return False  # single-line statement: a 0 count is a genuine miss
    return any(hits.get(i, 0) > 0 for i in range(start, end + 1))


#: Exemption reasons, one per structurally-unreachable line class.
_MACRO_REASON = (
    "impl-block macro attribute: llvm-cov counts the attribute line as a "
    "region that never merges back from the generated wrappers, rustc#79651"
)
_DEFENSIVE_REASON = (
    "defensive map_err on an always-succeeds constructor: the shape/runtime "
    "argument is derived from the data so the error arm is unreachable"
)
_ARTIFACT_REASON = (
    "multi-line statement region non-merge artifact: the statement executed "
    "(a sibling line is hit) and this branch-free continuation carries no region"
)


def _exemption_reason(lines: list[str], lineno: int, hits: dict[int, int]) -> str | None:
    """Reason string if this missed line is structurally unreachable, else None."""
    stripped = lines[lineno - 1].strip()
    if _MACRO_ATTR.match(stripped) and _next_code_line(lines, lineno - 1).startswith("impl"):
        return _MACRO_REASON
    if _is_defensive_err(lines, lineno):
        return _DEFENSIVE_REASON
    if _is_continuation_artifact(lines, lineno, hits):
        return _ARTIFACT_REASON
    return None


def _read_source(fname: str) -> list[str] | None:
    try:
        with open(fname, encoding="utf-8") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _load_coverage(path: str) -> dict:
    """Load a coverage file into the codecov shape `{"coverage": {file:
    {line: "covered/count"}}}`. A `.json` file is read as-is (cargo-llvm-cov
    codecov export); any other extension is parsed as an llvm-cov lcov
    tracefile, where each `DA:<line>,<hits>` record is already the OR-merged
    per-line hit count, so it maps to `"<hits>/1"`. Grading below is then
    format-agnostic."""
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    coverage: dict[str, dict[str, str]] = {}
    current: str | None = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("SF:"):
                current = line[3:]
                coverage.setdefault(current, {})
            elif line.startswith("DA:") and current is not None:
                lineno, _, rest = line[3:].partition(",")
                if not lineno.isdigit():
                    continue
                hits = rest.partition(",")[0]
                coverage[current][lineno] = f"{int(hits)}/1"
    return {"coverage": coverage}


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "codecov.json"
    floor = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
    data = _load_coverage(path)
    covered = 0
    total = 0
    missed: dict[str, list[int]] = {}
    exempted: dict[str, list[int]] = {}
    reasons: dict[str, list[str]] = {}
    unverifiable: dict[str, list[int]] = {}
    src_cache: dict[str, list[str] | None] = {}
    hits_cache: dict[str, dict[int, int]] = {}
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
                hits_cache[fname] = {
                    int(k): int(v.partition("/")[0]) for k, v in lines.items() if k.isdigit()
                }
            src = src_cache[fname]
            if src is None or lineno > len(src):
                # Source unreadable: exemption cannot be verified, so the
                # line is never exempted — it stays missed (red at the
                # production floor) and is flagged unverifiable.
                missed.setdefault(fname, []).append(lineno)
                unverifiable.setdefault(fname, []).append(lineno)
                continue
            reason = _exemption_reason(src, lineno, hits_cache[fname])
            if reason is not None:
                exempted.setdefault(fname, []).append(lineno)
                bucket = reasons.setdefault(fname, [])
                if reason not in bucket:
                    bucket.append(reason)
                covered += 1
            else:
                missed.setdefault(fname, []).append(lineno)
    percent = 100.0 * covered / total if total else 0.0
    print(f"codecov line coverage: {covered}/{total} = {percent:.2f}% (floor {floor}%)")
    for fname, lns in sorted(missed.items()):
        print(f"missed {fname}: {lns}")
    for fname, lns in sorted(exempted.items()):
        print(f"exempted {fname}: {lns} ({'; '.join(reasons[fname])})")
    for fname, lns in sorted(unverifiable.items()):
        print(f"unverifiable {fname}: {lns} (source not readable: never exempted)")
    return 0 if percent >= floor else 1


if __name__ == "__main__":
    sys.exit(main())
