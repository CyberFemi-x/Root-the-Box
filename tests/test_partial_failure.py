import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "exploit_chain"))

from unittest.mock import patch
from exploit import run_chain, health_check, FootholdError

KEY_PATH = "stage6_key"
PUBKEY_PATH = "stage6_key.pub"
UPLOADS_DIR = "/srv/support/uploads"


def test_partial_failure_unreachable_target():
    """
    Preflight (health_check) failing against an unreachable/wrong target
    must not raise an unhandled exception all the way up - run_chain
    should catch it and return a structured failure result.
    """
    unreachable_url = "http://192.168.77.250:8080"  # deliberately wrong IP
    unreachable_host = "192.168.77.250"

    result = run_chain(unreachable_url, unreachable_host, KEY_PATH, PUBKEY_PATH, UPLOADS_DIR)

    assert result["success"] is False
    assert result["user_flag"] is None
    assert result["root_flag"] is None
    assert result["error"] is not None


def test_interruption_mid_chain_still_returns_structured_result():
    """
    If a step partway through the chain raises unexpectedly (simulating
    an interruption - e.g. network drop between foothold and escalation),
    run_chain must still catch it, not crash, and still attempt cleanup
    rather than leaving the target in an undefined state.
    """
    with patch("exploit.escalate_to_root", side_effect=FootholdError("simulated interruption during escalation")):
        result = run_chain("http://192.168.77.21:8080", "192.168.77.21", KEY_PATH, PUBKEY_PATH, UPLOADS_DIR)

    assert result["success"] is False
    assert result["root_flag"] is None
    assert "simulated interruption" in result["error"]
    # cleanup must still have been attempted, not skipped
    assert result["cleanup"] is not None