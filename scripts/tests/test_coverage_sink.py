"""Coverage-sink gate: the typescript package's test scripts must carry
`--coverage` themselves, so any caller (local bare run, tasks.md, CI, the root
aggregator) gets coverage by default and a bare run cannot hide a branch gap
(the #182 drift: tasks.md hand-copied a bare `test:wasm` while CI ran
`test:wasm --coverage`). The threshold values stay in vitest.*.config.ts; this
gate only asserts the collection flag is baked into the package scripts."""

import json

from lib.repository import ROOT

TS_PKG = ROOT / "typescript" / "package.json"


def test_typescript_test_scripts_carry_coverage() -> None:
    scripts = json.loads(TS_PKG.read_text(encoding="utf-8"))["scripts"]
    for name in ("test:native", "test:wasm", "test:browser"):
        assert "--coverage" in scripts[name], f"{name} must bake in --coverage"
