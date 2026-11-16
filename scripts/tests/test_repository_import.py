"""`python/conftest.py` imports `lib.repository` solely for the `SKIP_DIRS`
constant, and it runs on the declared floor interpreter (python 3.10) where
`tomllib` is not yet stdlib. Importing the module for a constant must not pull
in the TOML parser, otherwise loading that conftest fails on the floor cell.
The TOML-parsing functions are never called from that environment, so the
parser belongs inside them, not at module top."""

import builtins
import sys


def _purge_repository() -> None:
    for mod in [m for m in sys.modules if m == "lib.repository"]:
        del sys.modules[mod]


def test_skip_dirs_importable_without_tomllib(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "tomllib":
            raise ModuleNotFoundError("No module named 'tomllib'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    _purge_repository()
    try:
        from lib.repository import SKIP_DIRS
    finally:
        _purge_repository()

    assert "target" in SKIP_DIRS
