import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "exploit_chain"))

import pytest
from exploit import run_chain


PATCHED_URL = "http://192.168.77.22:8080"
PATCHED_HOST = "192.168.77.22"


def test_injection_blocked_on_patched_target():
    """
    The chain must fail at the injection-confirmation step against the
    patched target, and must not obtain either flag.
    """
    result = run_chain(PATCHED_URL, PATCHED_HOST, "stage6_key", "stage6_key.pub", "/srv/support/uploads")

    assert result["success"] is False, "exploit chain should NOT succeed against patched target"
    assert result["user_flag"] is None, "user flag should not be obtainable on patched target"
    assert result["root_flag"] is None, "root flag should not be obtainable on patched target"
    assert "canary not reflected" in result["error"], \
        f"expected failure at injection precondition, got: {result['error']}"
    assert "does not appear to be an IPv4 or IPv6 address" in result["error"], \
        "failure should be due to IP validation rejecting the payload, confirming root-cause fix"