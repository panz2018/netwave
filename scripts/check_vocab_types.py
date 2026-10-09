#!/usr/bin/env python3
"""Cross-end vocabulary consistency gate (spec: frequency-unit "vocabulary
single source" / "三端成员集合相等").

The runtime three-end equality is pinned by the per-end tests (native / wasm /
python each assert the same independent CANONICAL list). This gate closes the
remaining gap: the *generated type artifacts* — the Python `.pyi` and the two
TypeScript `.d.ts` — must carry the identical member-name set, so a stale build
artifact (an end rebuilt after a core rename) trips CI here rather than
shipping a drifted `.d.ts`.

Reads the build outputs directly (no hand-copied vocabulary): each artifact's
member set is extracted from its own enum/class block. Run after all three
glues are built (the node job's `check:cross` step, which already builds
python + napi + wasm).

    python3 scripts/check_vocab_types.py

Exit code 1 on any mismatch or missing artifact. Pure stdlib.
"""

import re
import sys
from pathlib import Path

# Repo root = parent of this scripts/ dir, so the gate works from any cwd.
ROOT = Path(__file__).resolve().parent.parent

# Each vocabulary: the canonical member list, in core definition order.
# Independent literals (a core rename SHOULD trip this gate).
CANONICAL = {
    "FrequencyUnit": ["Hz", "kHz", "MHz", "GHz", "THz"],
    "WavelengthUnit": ["m", "cm", "mm", "um", "nm"],
}

# Generated type artifacts, relative to repo root.
PYI = ROOT / "python" / "netwave" / "_netwave.pyi"
NODE_DTS = ROOT / "typescript" / "dist" / "index.node.generated.d.mts"
WASM_DTS = ROOT / "typescript" / "dist" / "wasm-web" / "netwave_wasm.d.ts"


def strip_comments(src: str) -> str:
    """Strip `/* */` and `//` comments so a doc line mentioning a name never
    counts as a member."""
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"//.*$", "", src, flags=re.MULTILINE)


def ts_members(src: str, enum: str) -> list[str]:
    """TS enum members: the `Name = ...` lines inside the `enum <enum>`
    block (delimited by braces)."""
    code = strip_comments(src)
    match = re.search(r"enum " + re.escape(enum) + r"\b", code)
    if not match:
        raise ValueError(f"{enum} enum not found")
    body = code[match.start() : code.index("}", match.start())]
    return re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", body, flags=re.MULTILINE)


def py_members(src: str, enum: str) -> list[str]:
    """Python class members: the 4-space-indented `Name = ...` lines under
    `class <enum>`. Blank lines and docstring prose (also 4-space indented)
    are skipped; the body ends at the first dedented line (the next
    top-level `def`/`class`/decorator) — a Python class has no closing brace."""
    lines = src.split("\n")
    start = next(
        (i for i, line in enumerate(lines) if re.match(r"^class " + re.escape(enum) + r"\b", line)),
        None,
    )
    if start is None:
        raise ValueError(f"{enum} class not found")
    out: list[str] = []
    for line in lines[start + 1 :]:
        # pyo3-stub-gen emits every enum member as `    Name = ...`; the
        # literal `...` value distinguishes members from docstring prose.
        member = re.match(r"^ {4}([A-Za-z_][A-Za-z0-9_]*) = \.\.\.", line)
        if member:
            out.append(member.group(1))
        elif line.strip() == "" or re.match(r"^ {4}", line):
            continue  # blank / docstring
        else:
            break  # dedented: next top-level definition
    return out


def read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"generated artifact missing: {path}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    bad = 0
    for enum, canonical in CANONICAL.items():
        try:
            pyi = py_members(read(PYI), enum)
            node = ts_members(read(NODE_DTS), enum)
            wasm = ts_members(read(WASM_DTS), enum)
        except (FileNotFoundError, ValueError) as exc:
            print(f"VOCAB TYPES: {enum}: {exc}", file=sys.stderr)
            return 1
        for label, members in (("python .pyi", pyi), ("node .d.mts", node), ("wasm .d.ts", wasm)):
            if members != canonical:
                print(f"VOCAB TYPES: {enum} {label} members {members} != {canonical}")
                bad += 1
        if not bad and not (node == pyi == wasm):
            print(f"VOCAB TYPES: {enum} artifacts disagree: pyi={pyi} node={node} wasm={wasm}")
            bad += 1
        else:
            print(f"vocab types OK: {enum} all three artifacts carry {canonical}")

    if bad:
        print(f"VOCAB TYPES: {bad} artifact(s) drifted from core vocabulary")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
