"""Coverage-sink gate: each package's test scripts must carry `--coverage`
themselves, so any caller (local bare run, tasks.md, CI, the root aggregator)
gets coverage by default and a bare run cannot hide a branch gap (the #182
drift: tasks.md hand-copied a bare test command while CI ran it with --coverage).
The node end lives in typescript (test:native); the browser end lives in the
netwave-browser package (test:unit/test:e2e). The threshold values stay in
vitest.*.config.ts; this gate only asserts the collection flag is baked into the
package scripts."""

import json

from lib.repository import ROOT

TS_PKG = ROOT / "typescript" / "package.json"
BROWSER_PKG = ROOT / "browser" / "package.json"


def test_typescript_test_scripts_carry_coverage() -> None:
    scripts = json.loads(TS_PKG.read_text(encoding="utf-8"))["scripts"]
    for name in ("test:native",):
        assert "--coverage" in scripts[name], f"{name} must bake in --coverage"


def test_browser_test_scripts_carry_coverage() -> None:
    scripts = json.loads(BROWSER_PKG.read_text(encoding="utf-8"))["scripts"]
    for name in ("test:unit", "test:e2e"):
        assert "--coverage" in scripts[name], f"{name} must bake in --coverage"
