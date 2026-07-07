"""Canary battery (resolves review MF3).

A single self-designed injected-value canary only tests the harness tripwire,
not the implicit leaks that actually bite (back-adjusted prices, survivorship,
filing-lag). Each canary here targets a real leak mechanism. No accuracy number
is trusted until the battery passes.
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from ..pit.prices import pit_prices, future_split_factor, forward_return
from ..pit.fundamentals import pit_fundamentals
from ..pit.universe import data_available


def split_adjustment_canary() -> Dict:
    """NVDA had a 10:1 split (ex-date 2024-06-10). As-of 2024-05-01 the price an
    observer saw was pre-split (~$800-900), NOT the back-adjusted ~$83. If our
    series shows ~$83 we are leaking the future split into a pre-split date."""
    try:
        p = pit_prices("NVDA", "2024-05-01")
        factor = future_split_factor("NVDA", "2024-05-01")
    except Exception as exc:  # noqa: BLE001 - a fetch failure is a failed canary, not a crash
        return {"name": "split_adjustment", "passed": False, "detail": f"unreachable: {exc}"}
    if p is None or p.empty:
        return {"name": "split_adjustment", "passed": False, "detail": "no NVDA data"}
    last = float(p["Close"].iloc[-1])
    passed = last > 300 and factor >= 10.0
    return {
        "name": "split_adjustment",
        "passed": passed,
        "detail": f"NVDA @2024-05-01 close={last:.0f} (expect pre-split >300), "
                  f"future_split_factor={factor:.0f} (expect >=10)",
    }


def filing_lag_canary() -> Dict:
    """MU FQ3'24 (period end 2024-05-30) was filed 2024-06-27. As-of 2024-06-20
    that quarter must be ABSENT (filed after T); as-of 2024-06-30 it must be
    PRESENT. Tests the filed<=T selector and that we don't peek at unfiled data."""
    try:
        before = pit_fundamentals("MU", "2024-06-20").revenue_q
        after = pit_fundamentals("MU", "2024-06-30").revenue_q
    except Exception as exc:  # noqa: BLE001 - a fetch failure is a failed canary, not a crash
        return {"name": "filing_lag", "passed": False, "detail": f"unreachable: {exc}"}
    target = pd.Timestamp("2024-05-30")
    has_before = any(abs((i - target).days) <= 3 for i in before.index)
    has_after = any(abs((i - target).days) <= 3 for i in after.index)
    passed = (not has_before) and has_after
    return {
        "name": "filing_lag",
        "passed": passed,
        "detail": f"MU FQ end 2024-05-30 present@2024-06-20={has_before} (want False), "
                  f"present@2024-06-30={has_after} (want True)",
    }


def injected_future_value_canary() -> Dict:
    """Inject a synthetic observation FILED AFTER T and assert pit_fundamentals
    excludes it. Direct test that filed>T data never enters the as-of view."""
    cf = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"start": "2024-03-01", "end": "2024-05-30",
                             "val": 1_000_000_000, "filed": "2024-12-31",
                             "form": "10-Q"},  # filed AFTER T below
                            {"start": "2023-03-01", "end": "2023-05-30",
                             "val": 800_000_000, "filed": "2023-07-01",
                             "form": "10-Q"},   # filed BEFORE T -> should appear
                        ]
                    }
                }
            }
        }
    }
    f = pit_fundamentals("FAKE", "2024-06-30", cf=cf)
    has_future = any(i == pd.Timestamp("2024-05-30") for i in f.revenue_q.index)
    has_past = any(i == pd.Timestamp("2023-05-30") for i in f.revenue_q.index)
    passed = (not has_future) and has_past
    return {
        "name": "injected_future_value",
        "passed": passed,
        "detail": f"future-filed obs included={has_future} (want False), "
                  f"past-filed obs included={has_past} (want True)",
    }


def survivorship_canary() -> Dict:
    """A ticker with no reconstructable PIT data must be DETECTED as unavailable
    (so the backtest can count it as excluded-no-data) — never fabricated into a
    silent pass. Uses an invalid symbol as a stand-in for a vanished listing."""
    try:
        avail = data_available("ZZZZ_NOT_A_TICKER", "2023-06-30")
        p = pit_prices("ZZZZ_NOT_A_TICKER", "2023-06-30")
    except Exception as exc:  # noqa: BLE001 - a fetch failure is a failed canary, not a crash
        return {"name": "survivorship", "passed": False, "detail": f"unreachable: {exc}"}
    passed = (avail is False) and (p is None or p.empty)
    return {
        "name": "survivorship",
        "passed": passed,
        "detail": f"invalid ticker data_available={avail} (want False), "
                  f"price_empty={p is None or p.empty} (want True)",
    }


def recycled_ticker_canary() -> Dict:
    """BBBY died in 2023 and its ticker was recycled; yfinance now serves the
    symbol as the live successor's continuous history with the dead leg dropped
    (no gap, no penny prices — nothing for a series-shape detector to see).
    forward_return must still realize the collapse, not the successor's price:
    the curated dead-ticker registry (pit/dead_tickers.py) floors names that
    died inside the window at their terminal value regardless of what series
    the provider re-anchors under the symbol."""
    try:
        r = forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12)
        ok = r is not None and r <= -0.9
        return {"name": "recycled_ticker", "passed": bool(ok), "detail": f"BBBY 12m fwd = {r}"}
    except Exception as exc:  # noqa: BLE001 - a fetch failure is a failed canary, not a crash
        return {"name": "recycled_ticker", "passed": False, "detail": f"unreachable: {exc}"}


def run_battery() -> List[Dict]:
    return [
        split_adjustment_canary(),
        filing_lag_canary(),
        injected_future_value_canary(),
        survivorship_canary(),
        recycled_ticker_canary(),
    ]
