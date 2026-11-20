#!/usr/bin/env python3
"""Gate: code comments must state current usage facts only.

Code is user-facing documentation. Its comments (line comments plus
rustdoc/docstring/JSDoc) MUST describe the current contract -- what it does,
why, and under what conditions -- and MUST NOT carry development-process
information:

- change names (directory names under openspec/changes/ and its archive/,
  with the YYYY-MM-DD- prefix stripped);
- roadmap stage words (a Chinese stage word followed by a digit, English
  `stage N` / `phase-N` / `phase N`, plus words meaning "an unfinished
  temporary shell" or "arrives later");
- discussion codenames and archaeology narration ("replaces X", "no longer",
  "deviation filed");
- pointers to development documents (`spec: <capability>`, `LL-NNN`,
  iron-rule numbers, `openspec/`, `Plan/`): a reader of code never needs to
  open a planning document in order to use the API.

History is traced through git log, not through comments.

The change-name pattern list is generated dynamically from the filesystem so
a new change is covered without editing this script. Names that are also
live spec capability names (e.g. `frequency-unit`) are excluded: they are
ordinary vocabulary in code, not archaeology.

A second, independent check enforces the language-zone rule: every line (not
only comments) of the scanned files MUST be free of CJK ideographs, since code,
config, and CI step bodies are English-zone. A line is exempt when it carries a
verified spec-title reference shape -- `「title」(specs/<capability>/spec.md)`
whose spec file exists under openspec/ and really contains that title -- or when
the file is the gate's own source (scripts/check_*.py) or self-test
(scripts/tests/), whose Chinese is functional (banned-word patterns, error
strings, probe fixtures), or when it lives in a Chinese-zone directory
(openspec/, Plan/). Fullwidth punctuation is out of scope.

Scanned: comments in .rs/.py/.ts sources and .yml/.yaml/.toml configs.
Markdown is covered by scripts/check_md.py, the developer-documentation gate.
File-level exemptions (whitelist, nothing else is exempt): pnpm-lock.yaml
(generated), .openspec.yaml under openspec/changes/archive/ (frozen history),
openspec/config.yaml (its path references are the functional meaning of
workflow instructions, not development leakage), and build directories.

Run from repo root:

    python3 scripts/check_comments.py

Exit code 1 on any violation.
"""

import os
import re
import sys
from glob import glob

STAGE_WORDS = re.compile(r"阶段\s*[0-9]|stage [0-9]|phase[- ][0-9]|\bskeleton\b|arrives with")

# Pointers into development documents: reading the code must never require
# opening a spec, ledger, or planning document.
DEV_DOC_POINTERS = re.compile(r"spec: |LL-[0-9]+|铁律[一二三四五六七八九十]+|openspec/|Plan/")

# Archaeology narration: describes a transition from a previous state instead
# of the current contract.
ARCHAEOLOGY = re.compile(r"replaces X|no longer|deviation filed", re.IGNORECASE)

# Run identifiers: a CI run number is only ever a development-process pointer.
CI_RUN = re.compile(r"CI run [0-9]{6,}")

# Date attribution: a re-enable/calibration date explains why a value is what
# it is today. A bare date (a version string, a data value) is not attribution,
# so the verb prefix is required.
DATE_ATTRIBUTION = re.compile(
    r"Re-enabled [0-9]{4}-[0-9]{2}-[0-9]{2}|重新启用 [0-9]{4}-[0-9]{2}-[0-9]{2}|已标定"
)

# Discussion codenames: decision numbers only make sense inside the document
# that defines them.
DECISION_CODENAME = re.compile(r"design decision [0-9]+|design D[0-9]+", re.IGNORECASE)

COMMENT_PREFIXES = ("//", "///", "//!", "#", "/*", "*/", "* ", "--")

# CJK gate: every line (not only comments) of the scanned suffixes is checked
# for CJK ideographs. Fullwidth punctuation is out of scope. A line is exempt
# when it carries a verified spec-title reference shape, or when the file is
# the gate's own source/self-test, or lives in a Chinese-zone directory.
CJK = re.compile(r"[\u4e00-\u9fff]")
SPEC_REF = re.compile(r"「([^」]+)」\(specs/([^)]+\.md)\)")

EXEMPT_DIRS = (
    "node_modules",
    "target",
    "target-wasm",
    "dist",
    ".venv",
    ".git",
    ".claude",
    ".pytest_cache",
    "coverage",
)

# Files skipped entirely: generated artifacts, frozen history, and the workflow
# config whose path references are instruction semantics rather than leakage.
EXEMPT_FILES = (
    "pnpm-lock.yaml",
    "openspec/config.yaml",
)

ARCHIVE_DIR = "openspec/changes/archive/"

SCAN_SUFFIXES = ("rs", "py", "ts", "yml", "yaml", "toml")


def is_exempt(rel: str) -> bool:
    """Match exempt directories by path component, not substring: a substring
    test would exempt `.github/` because it contains `.git`."""
    parts = rel.split("/")
    if any(part in EXEMPT_DIRS for part in parts):
        return True
    if rel in EXEMPT_FILES:
        return True
    if ARCHIVE_DIR in rel and rel.endswith(".openspec.yaml"):
        return True
    return False


def change_names(root: str) -> list[str]:
    """Change directory names, date prefix stripped, minus live spec names."""
    live = {
        os.path.basename(os.path.dirname(p))
        for p in glob(os.path.join(root, "openspec", "specs", "*", "spec.md"))
    }
    names = set()
    for base in (
        os.path.join(root, "openspec", "changes"),
        os.path.join(root, "openspec", "changes", "archive"),
    ):
        for entry in os.listdir(base) if os.path.isdir(base) else []:
            if entry in (".gitkeep", "archive") or entry.startswith("."):
                continue
            name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", entry)
            if name not in live:
                names.add(name)
    return sorted(names)


def is_comment(line: str) -> bool:
    s = line.lstrip()
    return s.startswith(COMMENT_PREFIXES)


def iter_scanned_files(root: str):
    """Yield (path, relpath) for every scannable source/config file.

    os.walk is used instead of glob because glob skips dot-prefixed paths, and
    the scan surface includes .github/workflows/ci.yml and .openspec.yaml."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXEMPT_DIRS)
        for name in sorted(filenames):
            if not name.endswith(tuple("." + s for s in SCAN_SUFFIXES)):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            if is_exempt(rel):
                continue
            if "/dist/" in rel or rel.startswith("dist/") or "/generated" in rel:
                continue
            yield path, rel


def is_cjk_whitelist(rel: str) -> bool:
    """The gate's own sources (scripts/check_*.py at the top level) and its
    self-tests (scripts/tests/) carry functional Chinese -- banned-word
    patterns, error strings, and probe fixtures -- so the CJK gate skips them
    entirely. scripts/versions/check_*.py is NOT whitelisted: its Chinese is
    spec-title references that must carry the verified reference shape."""
    parts = rel.split("/")
    if rel.startswith("scripts/tests/"):
        return True
    return len(parts) == 2 and parts[0] == "scripts" and parts[1].startswith("check_")


def is_chinese_zone(rel: str) -> bool:
    """openspec/ and Plan/ are Chinese-zone directories: prose there is the
    contract language, so the CJK gate does not scan them."""
    return rel.startswith("openspec/") or rel.startswith("Plan/")


def spec_ref_valid(root: str, line: str) -> bool:
    """True when the line carries a `「title」(specs/<cap>/spec.md)` shape whose
    spec file exists under openspec/ and actually contains that title. A
    half-shape (title without path, or path without title) never matches and
    so never exempts."""
    for title, rel_spec in SPEC_REF.findall(line):
        path = os.path.join(root, "openspec", "specs", rel_spec)
        try:
            with open(path, encoding="utf-8") as f:
                if title in f.read():
                    return True
        except OSError:
            continue
    return False


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    names = change_names(root)
    patterns = [re.compile(re.escape(n)) for n in names]
    patterns += [
        STAGE_WORDS,
        DEV_DOC_POINTERS,
        ARCHAEOLOGY,
        CI_RUN,
        DATE_ATTRIBUTION,
        DECISION_CODENAME,
    ]

    bad = 0
    for path, _rel in iter_scanned_files(root):
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not is_comment(line):
                    continue
                for pat in patterns:
                    if pat.search(line):
                        print(f"STALE REF      {path}:{i} {line.strip()[:70]}")
                        bad += 1
                        break

    cjk_bad = 0
    for path, rel in iter_scanned_files(root):
        if is_cjk_whitelist(rel) or is_chinese_zone(rel):
            continue
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                m = CJK.search(line)
                if not m:
                    continue
                if spec_ref_valid(root, line):
                    continue
                print(f"CJK            {m.group(0)} {path}:{i}")
                cjk_bad += 1

    if bad or cjk_bad:
        if bad:
            print(f"check_comments: {bad} stale reference(s) found")
        if cjk_bad:
            print(f"check_comments: {cjk_bad} CJK character(s) in English-zone file(s)")
        return 1
    print("check_comments: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
