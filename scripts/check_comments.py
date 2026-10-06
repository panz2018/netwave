#!/usr/bin/env python3
"""Gate: comments and live specs must state current facts only.

Change names (directory names under openspec/changes/ and its archive/, with
the YYYY-MM-DD- prefix stripped) and roadmap stage words must never appear
in code comments or live specs -- history is traced through git log, not
through comments. Stable contract pointers (iron-rule numbers, LL numbers,
`spec: <capability>`) are allowed.

The change-name pattern list is generated dynamically from the filesystem so
a new change is covered without editing this script. Names that are also
live spec capability names (e.g. `frequency-unit`) are excluded: referencing
a live spec is a legitimate contract pointer, not archaeology.

Scanned: comments in .rs/.py/.ts sources and the body of
openspec/specs/**/*.md. Exempt: the governance spec itself (it defines the
rule and must quote the counter-examples), the lessons-learned ledger (it
cites violations as evidence, same exemption as the LL-033 gate), archived
changes (frozen history), and third-party trees.

Run from repo root:

    python3 scripts/check_comments.py

Exit code 1 on any violation.
"""

import os
import re
import sys
from glob import glob

STAGE_WORDS = re.compile(r"stage [0-9]|phase-[0-9]|\bskeleton\b|arrives with")

COMMENT_PREFIXES = ("//", "///", "//!", "#", "/*", "*/", "* ", "--")

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

LEDGER = "openspec/specs/lessons-learned/"
GOVERNANCE = "openspec/specs/project-governance/spec.md"


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


def scan_text(path: str, patterns: list[re.Pattern]) -> int:
    bad = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            for pat in patterns:
                if pat.search(line):
                    print(f"STALE REF      {path}:{i} {line.strip()[:70]}")
                    bad += 1
                    break
    return bad


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    names = change_names(root)
    patterns = [re.compile(re.escape(n)) for n in names] + [STAGE_WORDS]

    bad = 0
    for ext in ("rs", "py", "ts"):
        for path in sorted(glob(os.path.join(root, "**", f"*.{ext}"), recursive=True)):
            rel = path.replace("\\", "/")
            if any(d in rel for d in EXEMPT_DIRS) or LEDGER in rel:
                continue
            if "/dist/" in rel or "/generated" in rel:
                continue
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if not is_comment(line):
                        continue
                    for pat in patterns:
                        if pat.search(line):
                            print(f"STALE REF      {path}:{i} {line.strip()[:70]}")
                            bad += 1
                            break

    for path in sorted(glob(os.path.join(root, "openspec", "specs", "**", "*.md"), recursive=True)):
        rel = path.replace("\\", "/")
        if rel.endswith(GOVERNANCE) or LEDGER in rel:
            continue
        bad += scan_text(path, patterns)

    if bad:
        print(f"check_comments: {bad} stale reference(s) found")
        return 1
    print("check_comments: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
