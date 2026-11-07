"""Smoke test for the autouse offline guard in conftest.py: any real
network attempt inside scripts/tests must fail immediately."""

import urllib.error
import urllib.request


def test_network_is_forbidden():
    try:
        urllib.request.urlopen("https://example.invalid")
    except urllib.error.URLError as e:
        assert "network access forbidden" in str(e)
    else:
        raise AssertionError("expected URLError from the offline guard")
