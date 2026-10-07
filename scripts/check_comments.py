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

Scanned: comments in .rs/.py/.ts sources only. Markdown is covered by
scripts/check_md.py, the developer-documentation gate. No exemptions.

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


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    names = change_names(root)
    patterns = [re.compile(re.escape(n)) for n in names]
    patterns += [STAGE_WORDS, DEV_DOC_POINTERS, ARCHAEOLOGY]

    bad = 0
    for ext in ("rs", "py", "ts"):
        for path in sorted(glob(os.path.join(root, "**", f"*.{ext}"), recursive=True)):
            rel = path.replace("\\", "/")
            if any(d in rel for d in EXEMPT_DIRS):
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

    if bad:
        print(f"check_comments: {bad} stale reference(s) found")
        return 1
    print("check_comments: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
