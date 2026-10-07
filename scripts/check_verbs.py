#!/usr/bin/env python3
"""Cross-end verb-set equality gate (spec: api-contract / memory-lifecycle
"unified drop verb", ironclad rule 12 — one name per concept, no alias).

The three generated type artifacts are the user-visible surface; a rename on
one end that fails to propagate shows up here as a drifted method set. This
gate extracts the method names of the `Network` and `Frequency` classes and
the module-level free functions from each artifact, normalizes snake_case to
camelCase (the mechanical mapping, ironclad rule 9 exemption), and asserts
they match the single canonical verb set.

    python3 scripts/check_verbs.py

Rules:
  - Network instance/static verbs (excl. the constructor) equal on all three
    ends: {fillPattern, readElement, drop}
  - Frequency verbs equal on all three ends: {fromF, npoints, drop}
  - `upload` is browser-only (the worker linear-memory boundary): present on
    the browser Network, absent on node/Python
  - the two stateless free verbs {frequencyUnits, liveCount} are on all three
  - FORBIDDEN: `free`/`release` as a member/function name on any user-visible
    artifact is red (the retired verbs must never resurface)

Run after all three glues are built (the node job's `check:cross` step).
Exit code 1 on any drift. Pure stdlib.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Independent canonical verb sets (a core rename SHOULD trip this gate —
# same tripwire idiom as check_vocab_types.py's CANONICAL vocabulary list).
NETWORK_VERBS = {"fillPattern", "readElement", "drop"}
FREQUENCY_VERBS = {"fromF", "npoints", "drop"}
FREE_VERBS = {"frequencyUnits", "liveCount"}
# Browser-only: the worker linear-memory boundary does not exist on node/
# Python, so `upload` lives only on the browser Network shell.
BROWSER_ONLY = {"upload"}
# Retired verbs: must never appear as a name on any user-visible surface.
FORBIDDEN = {"free", "release"}

PYI = ROOT / "python" / "netwave" / "_netwave.pyi"
NODE_DTS = ROOT / "typescript" / "dist" / "index.node.generated.d.mts"
BROWSER_DTS = ROOT / "typescript" / "dist" / "index.browser.d.mts"
# The wasm glue is the raw wasm-bindgen output: the single generic `call` is
# the ONLY dispatch entry, plus the `FrequencyUnit` constant enum, the
# `register_resources` start hook (a registration entry, not a verb —
# wasm-bindgen exports the `start` fn by name regardless of Rust visibility),
# and the wasm-pack generated init/default. Any per-verb `#[wasm_bindgen]`
# export reappearing here is the LL-052 relapse this pin detects.
WASM_GLUE_DTS = ROOT / "typescript" / "dist" / "wasm-web" / "netwave_wasm.d.ts"
WASM_GLUE_EXPORTS = {"call", "FrequencyUnit", "register_resources"}


def camel(name: str) -> str:
    """snake_case -> camelCase (the mechanical cross-end mapping)."""
    parts = name.split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*[\s\S]*?\*/", "", src)
    return re.sub(r"//.*$", "", src, flags=re.MULTILINE)


def class_block(code: str, name: str) -> str:
    """The body of `class Name { ... }` (brace-balanced) from TS d.ts."""
    match = re.search(r"class\s+" + re.escape(name) + r"\b", code)
    if not match:
        raise ValueError(f"class {name} not found")
    start = code.index("{", match.start())
    depth = 0
    for i in range(start, len(code)):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return code[start : i + 1]
    raise ValueError(f"unbalanced class {name}")


def ts_class_verbs(src: str, name: str) -> set:
    """Method names of a TS class: `name(` and `static name(`, minus the
    constructor."""
    code = strip_comments(src)
    block = class_block(code, name)
    verbs = set(re.findall(r"\bstatic\s+([A-Za-z_]\w*)\s*\(", block))
    verbs |= set(re.findall(r"^\s+([A-Za-z_]\w*)\s*\(", block, flags=re.MULTILINE))
    return {camel(v) for v in verbs if v != "constructor"}


def py_class_verbs(src: str, name: str) -> set:
    """Method names of a pyclass: `def name(` under `class Name`, minus
    `__new__` (the constructor). The block ends at the next dedented line."""
    lines = src.split("\n")
    cls = re.compile(r"^class\s+" + re.escape(name) + r"\b")
    start = next((i for i, line in enumerate(lines) if cls.match(line)), None)
    if start is None:
        raise ValueError(f"class {name} not found")
    verbs = set()
    for line in lines[start + 1 :]:
        member = re.match(r"^ {4}def\s+([A-Za-z_]\w*)\s*\(", line)
        if member and member.group(1) != "__new__":
            verbs.add(camel(member.group(1)))
        elif line.strip() == "" or line.startswith("    ") or line.startswith("@"):
            continue
        else:
            break
    return verbs


def ts_free_verbs(src: str) -> set:
    """Module-level exported function/const names (the free verbs)."""
    code = strip_comments(src)
    names = set(re.findall(r"^export declare function\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    names |= set(re.findall(r"^export declare const\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    return {camel(n) for n in names}


def wasm_glue_exports(src: str) -> set:
    """Top-level export names of the wasm-bindgen glue d.ts. wasm-bindgen
    emits plain `export function`/`export enum` (no `declare`); the wasm-pack
    init (`export default` / `export function initSync`) is tool-generated and
    excluded; everything else MUST be the single `call`, the `FrequencyUnit`
    constant enum, and the `register_resources` start hook."""
    code = strip_comments(src)
    names = set(re.findall(r"^export function\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    names |= set(re.findall(r"^export enum\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    names |= set(re.findall(r"^export class\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    names |= set(re.findall(r"^export const\s+([A-Za-z_]\w*)", code, flags=re.MULTILINE))
    return names - {"init", "initSync"}


def py_free_verbs(src: str) -> set:
    """Module-level `def name(` at column 0 (the free verbs)."""
    return {camel(m) for m in re.findall(r"^def\s+([A-Za-z_]\w*)\s*\(", src, flags=re.MULTILINE)}


def read(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"generated artifact missing: {path} (rebuild it)")
    return path.read_text(encoding="utf-8")


def main() -> int:
    try:
        pyi = read(PYI)
        node = read(NODE_DTS)
        browser = read(BROWSER_DTS)
    except (FileNotFoundError, ValueError) as exc:
        print(f"VERBS: {exc}", file=sys.stderr)
        return 1

    ends = {
        "python": {
            "Network": py_class_verbs(pyi, "Network"),
            "Frequency": py_class_verbs(pyi, "Frequency"),
            "free": py_free_verbs(pyi),
        },
        "node": {
            "Network": ts_class_verbs(node, "Network"),
            "Frequency": ts_class_verbs(node, "Frequency"),
            "free": ts_free_verbs(node),
        },
        "browser": {
            "Network": ts_class_verbs(browser, "Network"),
            "Frequency": ts_class_verbs(browser, "Frequency"),
            "free": ts_free_verbs(browser),
        },
    }

    bad = 0

    # Network verbs (minus browser-only upload) equal on all three ends.
    for end, verbs in ends.items():
        got = verbs["Network"] - BROWSER_ONLY
        if got != NETWORK_VERBS:
            print(f"VERBS: {end}.Network {sorted(got)} != {sorted(NETWORK_VERBS)}")
            bad += 1
    # upload: browser-only presence.
    if BROWSER_ONLY & ends["browser"]["Network"] != BROWSER_ONLY:
        print(f"VERBS: browser.Network missing upload: {sorted(ends['browser']['Network'])}")
        bad += 1
    for end in ("python", "node"):
        if BROWSER_ONLY & ends[end]["Network"]:
            print(f"VERBS: {end}.Network must NOT expose upload (browser-only boundary)")
            bad += 1

    # Frequency verbs equal on all three ends.
    for end, verbs in ends.items():
        if verbs["Frequency"] != FREQUENCY_VERBS:
            got = sorted(verbs["Frequency"])
            print(f"VERBS: {end}.Frequency {got} != {sorted(FREQUENCY_VERBS)}")
            bad += 1

    # The two stateless free verbs are on all three ends.
    for end, verbs in ends.items():
        if not FREE_VERBS <= verbs["free"]:
            print(f"VERBS: {end} free missing {sorted(FREE_VERBS - verbs['free'])}")
            bad += 1

    # FORBIDDEN retired verbs must never resurface as a name.
    for label, src in (("python .pyi", pyi), ("node .d.mts", node), ("browser .d.mts", browser)):
        code = strip_comments(src)
        for verb in FORBIDDEN:
            hit = re.search(r"\b(?:def|function|const|static)\s+" + re.escape(verb) + r"\b", code)
            if hit:
                print(f"VERBS: FORBIDDEN verb {verb!r} on {label}: {hit.group(0)}")
                bad += 1

    # The wasm glue export set is pinned: the single generic `call` plus the
    # `FrequencyUnit` constant enum — no per-verb entry may reappear
    # (LL-052 relapse detector).
    try:
        glue = read(WASM_GLUE_DTS)
    except FileNotFoundError as exc:
        print(f"VERBS: {exc}", file=sys.stderr)
        return 1
    got = wasm_glue_exports(glue)
    if got != WASM_GLUE_EXPORTS:
        extra = sorted(got - WASM_GLUE_EXPORTS)
        missing = sorted(WASM_GLUE_EXPORTS - got)
        print(f"VERBS: wasm glue exports {sorted(got)} != {sorted(WASM_GLUE_EXPORTS)} (extra={extra} missing={missing})")
        bad += 1

    if bad:
        print(f"VERBS: {bad} drift(s) across the three artifacts")
        return 1
    print(
        f"verbs OK: Network={sorted(NETWORK_VERBS)} Frequency={sorted(FREQUENCY_VERBS)} "
        f"free={sorted(FREE_VERBS)} upload=browser-only, no free/release"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
