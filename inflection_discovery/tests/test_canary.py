"""The canary battery is the integration guard for point-in-time integrity.
The all-pass assertion is network-dependent (yfinance + SEC); these must pass
before any metric is trusted. The offline test below asserts the battery
degrades gracefully (never raises) when a fetch fails, so it stays unguarded.
"""
import os

import pytest

from inflection_discovery.harness import canary
from inflection_discovery.harness.canary import run_battery


def test_run_battery_survives_fetch_failure(monkeypatch):
    """When a live fetch raises (offline), the battery must still return a result
    list and mark the affected canary failed with an 'unreachable' detail —
    never propagate the exception. The injected-cf canary (no network) still
    runs, so only the real-fetch path is simulated as unreachable here."""
    real = canary.pit_fundamentals

    def boom(*args, **kwargs):
        if kwargs.get("cf") is not None:  # injected-data path: no network, keep working
            return real(*args, **kwargs)
        raise ConnectionError("no network")

    def boom_net(*args, **kwargs):
        raise ConnectionError("no network")

    # Simulate a full offline environment: every live fetch raises, but the
    # injected-cf canary still works. The battery must return, not crash.
    monkeypatch.setattr(canary, "pit_fundamentals", boom)
    monkeypatch.setattr(canary, "pit_prices", boom_net)
    monkeypatch.setattr(canary, "future_split_factor", boom_net)
    monkeypatch.setattr(canary, "data_available", boom_net)

    results = run_battery()
    assert isinstance(results, list) and len(results) == 5
    lag = next(r for r in results if r["name"] == "filing_lag")
    assert lag["passed"] is False
    assert "unreachable" in lag["detail"]
    # the injected-cf canary needs no network, so it still passes offline
    injected = next(r for r in results if r["name"] == "injected_future_value")
    assert injected["passed"] is True


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
