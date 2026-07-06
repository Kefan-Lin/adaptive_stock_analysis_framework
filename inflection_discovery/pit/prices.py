"""pit_prices — point-in-time price reconstruction (resolves review MF1).

yfinance returns prices back-adjusted for splits as of the *download* date, so
a split that happens after T silently rewrites pre-T price levels. Truncating
the time axis at T is necessary but not sufficient. Here we additionally
**un-adjust future splits** (ex-date > T) so the returned series is expressed in
the share terms an observer at T actually saw. This makes "52-week-low
proximity" and "drawdown" — inputs to the hard A gate — leak-free.

The split/adjustment canary in `harness/canary.py` verifies this directly.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import yfinance as yf

_RAW_CACHE: dict = {}


def _to_ts(T) -> pd.Timestamp:
    return pd.Timestamp(T)


def _raw_history(ticker: str) -> pd.DataFrame:
    """Full unadjusted-OHLC history with action columns, cached per process.

    auto_adjust=False keeps Close split-back-adjusted-to-now (not dividend
    adjusted) and exposes the 'Stock Splits' ratios we need to reverse.
    """
    key = ticker.upper()
    if key in _RAW_CACHE:
        return _RAW_CACHE[key]
    try:
        df = yf.Ticker(ticker).history(period="max", auto_adjust=False, actions=True)
    except Exception:
        df = pd.DataFrame()
    if df is not None and not df.empty and getattr(df.index, "tz", None) is not None:
        df = df.copy()
        df.index = df.index.tz_localize(None)
    _RAW_CACHE[key] = df
    return df


def future_split_factor(ticker: str, T) -> float:
    """Product of split ratios with ex-date strictly after T (1.0 if none)."""
    T = _to_ts(T)
    df = _raw_history(ticker)
    if df is None or df.empty or "Stock Splits" not in df:
        return 1.0
    splits = df["Stock Splits"]
    future = splits[(splits.index > T) & (splits != 0.0)]
    factor = 1.0
    for r in future.values:
        factor *= float(r)
    return factor


def forward_return(ticker: str, T, months: int = 6) -> Optional[float]:
    """Realized price return from T to T+months (legitimately uses future prices).

    Split-consistent (both ends from the same back-adjusted series). Dead-name
    handling: if the series ends before T+months (delisting), the last available
    close is used, so a name that collapsed contributes its realized loss rather
    than silently dropping (review SC1). A 30+ day trading gap inside the window
    is treated as death of the original line: the window is truncated at the last
    pre-gap close so a recycled ticker's successor prices never mask the collapse
    (audit I2).
    """
    T = _to_ts(T)
    df = _raw_history(ticker)
    if df is None or df.empty or "Close" not in df:
        return None
    start = df["Close"].asof(T)
    end_date = T + pd.DateOffset(months=months)
    fut = df[df.index <= end_date]["Close"].dropna()
    window = fut[fut.index > T]
    if len(window) >= 2:
        gaps = window.index.to_series().diff()
        breaks = gaps[gaps > pd.Timedelta(days=30)]
        if not breaks.empty:
            # Trading stopped for 30+ days inside the window: the original line
            # died (delisting); anything after is a recycled ticker or relist.
            # Realize the loss at the last pre-gap close (spec: dead names
            # contribute their realized loss, never a successor's prices).
            fut = window[window.index < breaks.index[0]]
    if pd.isna(start) or start <= 0 or fut.empty:
        return None
    return float(fut.iloc[-1] / start - 1.0)


def pit_prices(ticker: str, T, lookback_days: Optional[int] = None) -> pd.DataFrame:
    """Return the as-of-T price frame (OHLCV), future splits un-adjusted.

    Empty DataFrame signals no reconstructable data (delisted/missing) — the
    caller treats this as a data-availability gate, not an error.
    """
    T = _to_ts(T)
    df = _raw_history(ticker)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[df.index <= T]
    if df.empty:
        return pd.DataFrame()
    factor = future_split_factor(ticker, T)
    out = df.copy()
    for col in ("Open", "High", "Low", "Close"):
        if col in out:
            out[col] = out[col] * factor
    if "Volume" in out and factor:
        out["Volume"] = out["Volume"] / factor
    if lookback_days:
        out = out[out.index > (T - pd.Timedelta(days=lookback_days))]
    cols = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in out]
    return out[cols]


def median_dollar_adv(ticker: str, T, days: int = 60) -> Optional[float]:
    """Median daily dollar volume over the trailing `days` sessions as of T.

    Point-in-time (uses pit_prices). None when no data — callers treat None as
    'cannot verify liquidity' and exclude, counting the name, never guessing.
    """
    df = pit_prices(ticker, T, lookback_days=days * 3)
    if df is None or df.empty or "Close" not in df or "Volume" not in df:
        return None
    tail = df.tail(days)
    dv = (tail["Close"] * tail["Volume"]).dropna()
    return float(dv.median()) if len(dv) else None
