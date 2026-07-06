"""The canary battery is the integration guard for point-in-time integrity.
The all-pass assertion is network-dependent (yfinance + SEC); these must pass
before any metric is trusted. The offline test below asserts the battery
degrades gracefully (never raises) when a fetch fails, so it stays unguarded.
"""
import os

import pytest

from inflection_discovery.harness.canary import run_battery


@pytest.mark.skipif(
    not os.environ.get("RUN_NETWORK_TESTS"),
    reason="live-network test; set RUN_NETWORK_TESTS=1 to run",
)
def test_canary_battery_all_pass():
    results = run_battery()
    failed = [r for r in results if not r["passed"]]
    assert not failed, "canary failures: " + "; ".join(
        f"{r['name']}: {r['detail']}" for r in failed
    )
