#!/usr/bin/env python3
"""Validate markdown: links, anchors, and inline-code spans.

Anchor slugs follow GitHub's rule: lowercase, spaces -> '-', punctuation
dropped, CJK kept. Run from repo root after editing any Markdown:

    python3 scripts/check_md.py

Exit code 1 on any violation. Skips code blocks (links there do not
render) and http(s) URLs.

Checks:
- BROKEN FILE / BAD ANCHOR: link targets and heading anchors.
- OPEN CODE SPAN: a line with an odd number of backticks opens a code
  span that is never closed on the same line. Cross-line spans make
  Prettier drop the continuation line's indentation (it must not add
  spaces inside code content) and render badly on GitHub; close the
  span on one line instead.
"""

import os
import re
import sys
import unicodedata
from glob import glob

LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING = re.compile(r"#{1,6} (.*)")


def slug(title: str) -> str:
    out = []
    for ch in title.strip().lower():
        if ch in (" ", "-"):
            out.append("-")
        elif unicodedata.category(ch)[0] in ("L", "N", "M"):
            out.append(ch)
    return "".join(out)


def headings(path: str) -> set[str]:
    hs, in_code = set(), False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            m = HEADING.match(line)
            if m:
                hs.add("#" + slug(m.group(1)))
    return hs


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    files = sorted(glob(os.path.join(root, "*.md"))) + sorted(
        glob(os.path.join(root, "**", "*.md"), recursive=True)
    )
    cache: dict[str, set[str]] = {}
    bad = 0
    for f in files:
        if "/.git/" in f or "node_modules" in f:
            continue
        in_code = False
        with open(f, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if line.lstrip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    continue
                # unclosed inline-code span: odd backtick count outside
                # fences (see module docstring for why this matters)
                if line.count("`") % 2 == 1:
                    print(f"OPEN CODE SPAN {f}:{i} {line.rstrip()[:70]}")
                    bad += 1
                # strip inline-code spans: links there are format templates,
                # not real links (AGENTS.md documents the link syntax inside
                # backticks, so those must not be resolved)
                line = re.sub(r"`+[^`]*`+", "", line)
                for text, target in LINK.findall(line):
                    if target.startswith("http"):
                        continue
                    path, _, anchor = target.partition("#")
                    if path.startswith("~"):
                        path = os.path.expanduser(path)
                    tgt = os.path.normpath(os.path.join(os.path.dirname(f), path)) if path else f
                    if not os.path.exists(tgt):
                        print(f"BROKEN FILE  {f}:{i} [{text}]({target})")
                        bad += 1
                        continue
                    if anchor:
                        if tgt not in cache:
                            cache[tgt] = headings(tgt)
                        if "#" + anchor not in cache[tgt]:
                            print(f"BAD ANCHOR   {f}:{i} [{text}]({target})")
                            bad += 1
    print(f"checked {len(files)} files;", "OK" if bad == 0 else f"{bad} broken")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
