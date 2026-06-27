"""The canary battery is the integration guard for point-in-time integrity.
Network-dependent (yfinance + SEC); these must pass before any metric is trusted.
"""
from inflection_discovery.harness.canary import run_battery


def test_canary_battery_all_pass():
    results = run_battery()
    failed = [r for r in results if not r["passed"]]
    assert not failed, "canary failures: " + "; ".join(
        f"{r['name']}: {r['detail']}" for r in failed
    )
