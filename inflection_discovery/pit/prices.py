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

from .dead_tickers import DEAD_TICKERS

_RAW_CACHE: dict = {}

# Identity-break thresholds for forward_return. A back-adjusted series that
# switches entity mid-stream shows either a long trading silence (delisting
# gap) or — when the provider stitches a successor onto a dead line — a
# single-session jump from penny levels that no market move produces.
# Direction-gated on purpose: legitimate crash days are DOWN moves; only a
# sub-$1 close jumping >8x UP in one session marks a stitched successor.
IDENTITY_GAP_DAYS = 30
IDENTITY_JUMP_RATIO = 8.0
IDENTITY_PENNY_CEILING = 1.0


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


def _identity_breaks(close: pd.Series) -> pd.DatetimeIndex:
    """All identity-break indices in a Close series (possibly empty).

    Break signals (either fires):
    (a) a calendar gap > IDENTITY_GAP_DAYS between consecutive sessions
        (trading silence = delisting; whatever trades after is a relist or a
        recycled ticker), or
    (b) close[i]/close[i-1] > IDENTITY_JUMP_RATIO while close[i-1] <
        IDENTITY_PENNY_CEILING — a sub-$1 name jumping >8x in ONE session in a
        back-adjusted series is a stitched successor or a mangled feed splice,
        not a market move. The test is up-only by construction, so genuine
        crash days (DOWN moves) never trigger it.

    A break index marks the FIRST session of the new identity/segment.
    """
    if len(close) < 2:
        return close.index[:0]
    gap = close.index.to_series().diff() > pd.Timedelta(days=IDENTITY_GAP_DAYS)
    prev = close.shift(1)
    jump = (close / prev > IDENTITY_JUMP_RATIO) & (prev < IDENTITY_PENNY_CEILING)
    return close.index[(gap | jump).to_numpy()]


def _identity_segment(close: pd.Series, T: pd.Timestamp) -> pd.Series:
    """The contiguous same-identity sub-series containing the as-of date T.

    The series is split at every identity break (a break index starts a new
    segment); the segment T falls in is returned. Prices before the segment
    cannot anchor T, and prices after it cannot be read as T's forward window.
    This simultaneously stops a stitched successor from masking a collapse
    (a break AFTER T bounds the window on the right) and stops a transient
    feed glitch years earlier from truncating a modern window (a break
    AT/BEFORE T only trims the left) — making the measured return invariant
    to glitches outside T's own segment (live case: LEAT's two-session 2012
    bad tick, which whole-series truncation turned into a false 0.0 for a
    2026 window).
    """
    left = None
    right = None
    for b in _identity_breaks(close):
        if b <= T:
            left = b
        else:
            right = b
            break
    if left is not None:
        close = close[close.index >= left]
    if right is not None:
        close = close[close.index < right]
    return close


def forward_return(ticker: str, T, months: int = 6) -> Optional[float]:
    """Realized price return from T to T+months (legitimately uses future prices).

    Split-consistent (both ends from the same back-adjusted series). Dead-name
    handling, in order:

    1. **Curated registry** (`pit.dead_tickers.DEAD_TICKERS`): yfinance
       re-anchors recycled tickers to the live successor and drops the dead leg
       entirely, so no series-shape check can realize those losses. A name that
       died inside the window returns the curated terminal value against the
       as-of-T start (terminal 0 dominates any start-price re-anchoring); a T
       on/after the death date returns None (the old entity did not exist at
       T); a death after the window falls through to the normal path.
    2. **Identity-segment truncation** (defense-in-depth for feed shapes that
       DO retain both legs): start and end are read only from the contiguous
       identity segment containing T — the series split at every break, i.e. a
       >IDENTITY_GAP_DAYS calendar gap or a stitch-jump (sub-$1 close rising
       >IDENTITY_JUMP_RATIO x in one session; direction-gated, see
       `_identity_breaks`). A break after T bounds the window so a successor's
       prices never mask the collapse (audit I2) and a T inside the dead zone
       anchors at the dying price (audit M-1); a break at/before T only trims
       the left, so a transient feed glitch years earlier cannot zero a modern
       window (see `_identity_segment`).
    3. If the segment ends before T+months (delisting), the last available
       close is used, so a collapsed name contributes its realized loss rather
       than silently dropping (review SC1).
    """
    T = _to_ts(T)
    end_date = T + pd.DateOffset(months=months)
    dead = DEAD_TICKERS.get(ticker.upper())
    if dead is not None:
        death = pd.Timestamp(dead["death_date"])
        if T >= death:
            return None  # the old entity did not exist at T
        if death <= end_date:
            df = _raw_history(ticker)
            if df is None or df.empty or "Close" not in df:
                return None
            start = df["Close"].asof(T)
            if pd.isna(start) or start <= 0:
                return None
            # Terminal value dominates: with a curated recovery of ~0, the
            # realized loss is ~-100% regardless of the (possibly successor-
            # re-anchored) start level the feed serves.
            return float(dead["terminal_value"] / start - 1.0)
        # death after the window: the name was alive throughout -> normal path
    df = _raw_history(ticker)
    if df is None or df.empty or "Close" not in df:
        return None
    close = _identity_segment(df["Close"].dropna(), T)
    start = close.asof(T)
    fut = close[close.index <= end_date]
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
