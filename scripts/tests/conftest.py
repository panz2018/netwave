"""Offline guard for scripts/tests: governance tooling tests never reach the
network. A test that forgets to swap out a networked helper fails here with a
clear message instead of flaking on registry rate limits in CI.

The chokepoint is socket.getaddrinfo — every outbound TCP connection through
urllib resolves its host through it (patching socket.socket does not catch
urllib, which references the class via socket.create_connection). Subprocess
calls are unaffected (they are not sockets); helpers that shell out are
covered by swapping them out in the tests that use them."""

import socket

import pytest


def _blocked_getaddrinfo(*args, **kwargs):
    raise socket.gaierror("network access forbidden in tests — swap the networked helper out")


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _blocked_getaddrinfo)
