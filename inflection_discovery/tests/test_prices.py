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
    # non-registry ticker: this test must pass via the gap detector alone
    r = prices.forward_return("GAPPED", pd.Timestamp("2022-06-30"), months=12)
    assert r is not None and r <= -0.9, f"recycled ticker must not mask the collapse, got {r}"


def test_forward_return_no_gap_unchanged(monkeypatch):
    dates = pd.bdate_range("2022-01-01", "2023-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [10.0] * len(dates)))
    r = prices.forward_return("OK", pd.Timestamp("2022-06-30"), months=12)
    assert r == pytest.approx(0.0)


def _stitched_frame():
    # Continuous business days, NO calendar gap: the old line dies at pennies and
    # the provider stitches the successor's level directly onto the next session.
    # The 30-day gap rule cannot fire here; only the penny->8x up-jump can.
    old = pd.bdate_range("2022-06-01", "2023-05-01")
    new = pd.bdate_range("2023-05-02", "2023-12-29")
    closes = [10.0] * (len(old) - 1) + [0.07] + [25.0] * len(new)
    return _frame(list(old) + list(new), closes)


def test_forward_return_truncates_at_identity_jump(monkeypatch):
    # 0.07 -> 25.0 in one session (~357x from sub-$1) is a stitched successor,
    # not a market move. Untruncated, the successor's 25.0 masks the collapse.
    monkeypatch.setattr(prices, "_raw_history", lambda t: _stitched_frame())
    r = prices.forward_return("STITCH", pd.Timestamp("2022-06-30"), months=12)
    assert r is not None and r <= -0.9, f"stitched successor must not mask the collapse, got {r}"


def test_forward_return_T_inside_dead_zone(monkeypatch):
    # T = the dying 0.07 session, so the whole forward window is successor
    # prices. Untruncated this books ~+356x; truncated it anchors AND ends at
    # the dying price -> ~0, honest for a position entered at T.
    monkeypatch.setattr(prices, "_raw_history", lambda t: _stitched_frame())
    r = prices.forward_return("STITCH", pd.Timestamp("2023-05-01"), months=12)
    assert r is not None and abs(r) < 0.5, f"dead-zone T must not book the successor's level, got {r}"


def test_forward_return_dead_ticker_realizes_terminal_loss(monkeypatch):
    # yfinance re-anchors recycled tickers to the live successor and DROPS the
    # dead leg (no gap, no penny prices, nothing for a shape detector to see).
    # The curated registry must realize the loss regardless of series shape.
    dates = pd.bdate_range("2022-01-03", "2024-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [25.0] * len(dates)))
    r = prices.forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12)
    assert r is not None and r <= -0.9, f"registry must floor the dead name, got {r}"


def test_forward_return_dead_ticker_alive_whole_window(monkeypatch):
    # Window ends before the death date -> the name was alive throughout; the
    # registry must NOT floor it (normal path).
    dates = pd.bdate_range("2021-01-04", "2024-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [25.0] * len(dates)))
    r = prices.forward_return("BBBY", pd.Timestamp("2021-06-30"), months=12)
    assert r == pytest.approx(0.0)


def test_forward_return_T_after_death_returns_none(monkeypatch):
    # T on/after the death date: the old entity does not exist at T (the symbol
    # belongs to a successor); no forward return is measurable for it.
    dates = pd.bdate_range("2022-01-03", "2024-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [25.0] * len(dates)))
    assert prices.forward_return("BBBY", pd.Timestamp("2024-06-30"), months=12) is None


def test_forward_return_dead_ticker_no_start_returns_none(monkeypatch):
    # Registry path still needs a start price; with no series at all -> None.
    monkeypatch.setattr(prices, "_raw_history", lambda t: pd.DataFrame())
    assert prices.forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12) is None


def test_median_dollar_adv(monkeypatch):
    dates = pd.bdate_range("2024-01-01", "2024-06-30")
    df = pd.DataFrame({"Close": [10.0] * len(dates), "Volume": [200_000] * len(dates)}, index=dates)
    monkeypatch.setattr(prices, "pit_prices", lambda t, T, lookback_days=None: df)
    adv = prices.median_dollar_adv("X", pd.Timestamp("2024-06-30"))
    assert adv == pytest.approx(2_000_000.0)


def test_median_dollar_adv_empty(monkeypatch):
    monkeypatch.setattr(prices, "pit_prices", lambda t, T, lookback_days=None: pd.DataFrame())
    assert prices.median_dollar_adv("X", pd.Timestamp("2024-06-30")) is None
