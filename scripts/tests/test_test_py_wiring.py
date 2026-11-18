"""Wiring smoke test for the python test entry: root package.json must expose
`test:py`, ci.yml's python job must call scripts/run/test_py.sh (not inline the
chain), and both rust and python test scripts must put the stray-profraw drain
first in their post-run cleanup block so a later-appended command cannot push the
detection step to the end."""

import json
import re
from pathlib import Path

from lib.repository import ROOT

PKG = ROOT / "package.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"
TEST_RS = ROOT / "scripts" / "run" / "test_rs.sh"
TEST_PY = ROOT / "scripts" / "run" / "test_py.sh"


def test_root_package_exposes_test_py() -> None:
    scripts = json.loads(PKG.read_text(encoding="utf-8"))["scripts"]
    assert scripts["test:py"] == "bash scripts/run/test_py.sh"


def test_ci_python_job_calls_test_py_script() -> None:
    ci = CI.read_text(encoding="utf-8")
    assert "bash scripts/run/test_py.sh" in ci


def test_test_py_script_exists() -> None:
    assert TEST_PY.is_file()


def _post_block_drain_first(script: Path) -> bool:
    """True when the last drain call precedes the last instrumented-clean
    command, i.e. drain heads the post-run cleanup block."""
    lines = script.read_text(encoding="utf-8").splitlines()
    drain = [i for i, ln in enumerate(lines) if "clean_stray_profraw.py" in ln]
    clean = [
        i
        for i, ln in enumerate(lines)
        if re.search(r"rm -rf target/llvm-cov-target|cargo llvm-cov clean", ln)
    ]
    return bool(drain) and bool(clean) and max(drain) < max(clean)


def test_test_rs_post_block_drains_before_clean() -> None:
    assert _post_block_drain_first(TEST_RS)


def test_test_py_post_block_drains_before_clean() -> None:
    assert _post_block_drain_first(TEST_PY)
