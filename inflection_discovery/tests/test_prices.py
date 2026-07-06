import pandas as pd
import pytest

from inflection_discovery.pit import prices


def _frame(dates, closes):
    idx = pd.to_datetime(list(dates))
    return pd.DataFrame({"Close": closes, "Volume": [1e6] * len(idx)}, index=idx)


def test_forward_return_truncates_at_trading_gap(monkeypatch):
    # Old entity dies at pennies, a >30d trading gap, then the ticker is recycled
    # at $5 — the recycled leg falling INSIDE the T+12mo window is the leak. Without
    # gap truncation forward_return reads the successor's $5 (-50%) instead of the
    # realized collapse; with it, the last pre-gap close 0.08 -> -99%.
    old = pd.bdate_range("2022-06-01", "2022-08-01")
    new = pd.bdate_range("2022-11-01", "2023-06-01")
    closes = [10.0] * (len(old) - 1) + [0.08] + [5.0] * len(new)
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(list(old) + list(new), closes))
    r = prices.forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12)
    assert r is not None and r <= -0.9, f"recycled ticker must not mask the collapse, got {r}"


def test_forward_return_no_gap_unchanged(monkeypatch):
    dates = pd.bdate_range("2022-01-01", "2023-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [10.0] * len(dates)))
    r = prices.forward_return("OK", pd.Timestamp("2022-06-30"), months=12)
    assert r == pytest.approx(0.0)
