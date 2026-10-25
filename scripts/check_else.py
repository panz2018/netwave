#!/usr/bin/env python3
"""Gate: `else` must be an error fallback, never a correct branch.

In an `if/elif/.../else` chain (one or more `elif`), the terminal `else` body
MUST start with an error fallback (`raise`, or `break`/`continue` in a loop).
A known-good branch written into `else` is a violation — it silently swallows
future unhandled values instead of failing loudly.

Exempt by construction (no `elif`, so not a multi-way discriminator):
  - boolean two-way `if/else`
  - error guards (`if bad: report else: normal`)
  - loop termination (`else: break`)

Rust is covered by the compiler (exhaustive `match`); this gate is Python-only.

Usage: python3 scripts/check_else.py   (wired into pnpm check:meta)
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ("python", "scripts")
# statements that legitimately terminate an else fallback: raise = error,
# break/continue = loop-termination exemption. `return` is NOT a fallback —
# it can silently hand back a normal value, exactly what the rule forbids;
# a genuine error path in Python raises.
FALLBACK = (ast.Raise, ast.Break, ast.Continue)


def _is_elif_chain(node):
    """True if node is an If whose orelse is a single If (i.e. uses `elif`)."""
    return isinstance(node, ast.If) and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If)


def chain_head_ifs(tree):
    """If nodes that start an if/elif chain (not themselves an `elif`)."""
    elif_nodes = set()
    for node in ast.walk(tree):
        if _is_elif_chain(node):
            elif_nodes.add(id(node.orelse[0]))
    return [n for n in ast.walk(tree) if isinstance(n, ast.If) and id(n) not in elif_nodes]


def terminal_else(head):
    """Walk an if/elif chain to its terminal else body; (None, False) if none."""
    cur = head
    has_elif = False
    while cur.orelse:
        if _is_elif_chain(cur):
            has_elif = True
            cur = cur.orelse[0]
        else:
            return (cur.orelse, has_elif)
    return (None, has_elif)


def check_file(path):
    errs = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for head in chain_head_ifs(tree):
        body, has_elif = terminal_else(head)
        if body is None or not has_elif:
            continue  # no else, or plain boolean if/else — exempt
        if not body or not isinstance(body[0], FALLBACK):
            rel = path.relative_to(ROOT)
            errs.append(f"{rel}: else carries a non-fallback branch")
    return errs


def main() -> int:
    errors = []
    for d in TARGETS:
        for py in sorted((ROOT / d).rglob("*.py")):
            if "target" in py.parts or ".venv" in py.parts:
                continue
            errors.extend(check_file(py))
    if errors:
        for e in errors:
            print(f"::error::{e}", file=sys.stderr)
        return 1
    print("else-fallback OK: every elif-chain else is an error fallback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
