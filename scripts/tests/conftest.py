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

import pytest
from lib.repository import ROOT, drain_stray_profraw


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
