"""Offline guard for scripts/tests: governance tooling tests never reach the
network. A test that forgets to swap out a networked helper fails here with a
clear message instead of flaking on registry rate limits in CI.

The chokepoint is socket.getaddrinfo — every outbound TCP connection through
urllib resolves its host through it (patching socket.socket does not catch
urllib, which references the class via socket.create_connection). Subprocess
calls are unaffected (they are not sockets); helpers that shell out are
covered by swapping them out in the tests that use them."""

import socket
import sys
from pathlib import Path

import pytest
from lib.repository import ROOT, SKIP_DIRS


def drain_stray_profraw(root: Path) -> list[Path]:
    """Delete `*.profraw` files under `root` that sit outside build outputs and
    dependency caches, returning the sorted repo-relative paths removed.

    LLVM writes source-based coverage to `LLVM_PROFILE_FILE`; when that variable
    is unset at process exit it falls back to `default_%m_%p.profraw` in the
    process cwd. A profraw outside `target/` is therefore proof the coverage
    chain did not take effect, and such files are never report inputs — `cargo
    llvm-cov report` only reads what is registered under `target/`, so deleting
    them loses nothing."""
    removed: list[Path] = []
    for path in root.rglob("*.profraw"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        path.unlink()
        removed.append(rel)
    return sorted(removed)


def _blocked_getaddrinfo(*args, **kwargs):
    raise socket.gaierror("network access forbidden in tests — swap the networked helper out")


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _blocked_getaddrinfo)


@pytest.fixture(autouse=True, scope="session")
def drain_stray_profraw_session():
    """Fail the run when profraw files sit outside `target/`, scanning once
    before the session and once after, deleting what is found so the next run
    starts clean."""
    _drain_and_report("pre-test")
    yield
    _drain_and_report("post-test")


def _drain_and_report(phase: str) -> None:
    removed = drain_stray_profraw(ROOT)
    if not removed:
        return
    names = "\n".join(f"  {p}" for p in removed)
    print(
        f"profraw outside target/ = the coverage chain did not take effect, "
        f"so coverage numbers for this run are untrustworthy "
        f"({phase}: found {len(removed)}, deleted):\n{names}",
        file=sys.stderr,
    )
    raise RuntimeError(f"{phase}: found {len(removed)} stray profraw file(s) outside target/")
