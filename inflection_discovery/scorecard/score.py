"""Scorecard scoring: A/B/C/D dimensions + trap_risk from PIT inputs.

Pure functions over already-reconstructed point-in-time inputs (price frame,
Fundamentals, filing text). No look-ahead is possible here because the inputs
are PIT; this module only turns them into 0-1 scores per the taxonomy.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import pandas as pd

from . import taxonomy as tx
from ..pit.fundamentals import Fundamentals, pit_fundamentals
from ..pit.prices import pit_prices
from ..pit.filing_text import recent_filings, fetch_filing_text


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _logistic(x: float) -> float:
    if x < -50:
        return 0.0
    if x > 50:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def _yoy(series: pd.Series, tol_days: int = tx.YOY_TOLERANCE_DAYS,
         clip_range: Tuple[float, float] = (-2.0, 10.0)) -> pd.Series:
    """Year-over-year growth, matching each period to the obs ~365d earlier.

    Robust to Q4 gaps and fiscal-calendar drift, and inherently seasonally
    adjusted (compares like quarter to like quarter). Growth is clipped to a
    sane range so a near-zero prior base (pre-scale companies) cannot produce
    absurd ratios that dominate the signal.
    """
    idx = list(series.index)
    out: Dict[pd.Timestamp, float] = {}
    for e in idx:
        target = e - pd.Timedelta(days=365)
        cand = [i for i in idx if i < e and abs((i - target).days) <= tol_days]
        if not cand:
            continue
        prior = min(cand, key=lambda i: abs((i - target).days))
        if series[prior] not in (0, 0.0):
            g = series[e] / series[prior] - 1.0
            out[e] = max(clip_range[0], min(clip_range[1], g))
    return pd.Series(out).sort_index()


def _inventory_days(fund: Fundamentals) -> pd.Series:
    inv, cogs = fund.inventory, fund.cogs_q
    if inv.empty or cogs.empty:
        return pd.Series(dtype=float)
    common = inv.index.intersection(cogs.index)
    if len(common) < 2:
        return pd.Series(dtype=float)
    days = (inv[common] / cogs[common].replace(0, pd.NA)) * tx.DAYS_PER_QUARTER
    return days.dropna().sort_index()


def _ttm(series: pd.Series) -> pd.Series:
    if len(series) < 4:
        return pd.Series(dtype=float)
    return series.sort_index().rolling(4).sum().dropna()


# --------------------------------------------------------------------------- A
def score_A(prices: pd.DataFrame, fund: Optional[Fundamentals] = None) -> dict:
    ev: List[str] = []
    if prices is None or prices.empty or "Close" not in prices:
        return {"score": None, "gate": False, "evidence": ["no price data"]}
    close = prices["Close"].dropna()
    if close.empty:
        return {"score": None, "gate": False, "evidence": ["no price data"]}
    price = float(close.iloc[-1])
    ref = close.index[-1]
    hi = float(close[close.index > ref - pd.Timedelta(days=tx.A_HIGH_WINDOW_DAYS)].max())
    low = float(close[close.index > ref - pd.Timedelta(days=tx.A_LOW_WINDOW_DAYS)].min())
    drawdown = 1.0 - price / hi if hi > 0 else 0.0
    prox = price / low - 1.0 if low > 0 else 9.9
    dd_score = _clip(drawdown / tx.A_DRAWDOWN_FULL)
    prox_score = _clip((tx.A_LOW_PROX_FAR - prox) / (tx.A_LOW_PROX_FAR - tx.A_LOW_PROX_NEAR))
    ev.append(f"drawdown {drawdown:.0%} from 3y high; {prox:.0%} above 52w low")
    # NOTE: P/S-vs-history is deliberately NOT used here. At a cyclical earnings
    # trough, TTM sales collapse makes P/S look *expensive* exactly when the
    # stock is cheapest -- actively misleading for a turnaround detector. Price
    # drawdown + 52-week-low proximity are the robust depressedness measures.
    subs = [dd_score, prox_score]
    a = sum(subs) / len(subs)
    gate = drawdown >= tx.A_GATE_MIN_DRAWDOWN
    return {"score": _clip(a), "gate": bool(gate), "evidence": ev,
            "drawdown": drawdown}


# --------------------------------------------------------------------------- B
def score_B(fund: Fundamentals) -> dict:
    ev: List[str] = []
    if fund is None or fund.revenue_q.empty:
        return {"score": None, "turning": False, "evidence": ["no fundamentals"]}
    subs: List[float] = []
    turning = False

    # revenue YoY acceleration (seasonally robust); suppressed if too short.
    # _yoy().diff() needs >=5 quarters (a quarter, its year-ago match, and a prior
    # quarter's YoY), so the gate matches what the signal actually requires and the
    # suppression is always reported when accel can't be computed (review #3).
    yoy = _yoy(fund.revenue_q)
    accel = yoy.diff().dropna() if len(yoy) >= 2 else pd.Series(dtype=float)
    if fund.n_quarters >= tx.MIN_QUARTERS_SEASONAL and len(accel):
        a = float(accel.iloc[-1])
        subs.append(_logistic(a / tx.B_ACCEL_SCALE))
        turning = turning or a > 0
        ev.append(f"rev YoY accel {a:+.1%} (YoY now {yoy.iloc[-1]:+.1%})")
    else:
        ev.append("short history: revenue-acceleration signal suppressed (insufficient quarters)")

    # gross-margin inflection (guard against nonsensical margins for pre-scale
    # companies, where COGS >> tiny revenue produces e.g. -1300% "margins")
    gm = fund.gross_margin_q()
    if len(gm) >= 2 and -1.0 <= float(gm.iloc[-1]) <= 1.0 and -1.0 <= float(gm.iloc[-2]) <= 1.0:
        md = float(gm.iloc[-1] - gm.iloc[-2])
        trough = float(gm.tail(tx.B_MARGIN_TROUGH_WINDOW).min())
        off = _clip((float(gm.iloc[-1]) - trough) / tx.B_MARGIN_TROUGH_FULL)
        subs.append(_clip(0.5 * _logistic(md / tx.B_MARGIN_DELTA_SCALE) + 0.5 * off))
        turning = turning or md > 0
        ev.append(f"gross margin {gm.iloc[-1]:.1%} (Δ {md:+.1%}, +{float(gm.iloc[-1])-trough:.1%} off trough)")

    # inventory normalization (destocking)
    invd = _inventory_days(fund)
    if len(invd) >= 2:
        prev, cur = float(invd.iloc[-2]), float(invd.iloc[-1])
        if prev > 0:
            subs.append(_clip(0.5 + (prev - cur) / prev))
            ev.append(f"inventory days {cur:.0f} vs {prev:.0f}")

    score = sum(subs) / len(subs) if subs else None
    return {"score": score, "turning": bool(turning), "evidence": ev}


# --------------------------------------------------------------------------- C
def _keyword_hits(text: str) -> Tuple[int, int]:
    t = (text or "").lower()
    total = sum(t.count(k) for k in tx.INFLECTION_KEYWORDS)
    distinct = sum(1 for k in tx.INFLECTION_KEYWORDS if k in t)
    return total, distinct


def score_C(text_now: str, text_prev: str = "") -> dict:
    if not text_now:
        return {"score": None, "evidence": ["no filing text"]}
    tot_now, distinct_now = _keyword_hits(text_now)
    present = _clip(distinct_now / tx.C_KEYWORD_FULL)
    delta = 0.0
    if text_prev:
        tot_prev, _ = _keyword_hits(text_prev)
        delta = float(tot_now - tot_prev)
    score = _clip(0.6 * present + 0.4 * _logistic(delta / tx.C_DELTA_SCALE))
    present_kw = [k for k in tx.INFLECTION_KEYWORDS if k in text_now.lower()][:8]
    return {"score": score, "evidence": [f"narrative keywords: {', '.join(present_kw)}",
                                         f"keyword-hit delta vs prior filing: {delta:+.0f}"]}


# ------------------------------------------------------------------------- trap
def trap_risk(fund: Optional[Fundamentals], prices: Optional[pd.DataFrame]) -> dict:
    ev: List[str] = []
    comps: List[float] = []
    if fund is not None:
        # dilution
        if not fund.shares.empty:
            sh_yoy = _yoy(fund.shares)
            if len(sh_yoy):
                g = float(sh_yoy.iloc[-1])
                if g > tx.TRAP_DILUTION_YOY:
                    comps.append(_clip((g - tx.TRAP_DILUTION_YOY) /
                                       (tx.TRAP_DILUTION_FULL - tx.TRAP_DILUTION_YOY)))
                    ev.append(f"dilution: shares +{g:.0%} YoY")
        # runway
        if not fund.cash.empty and not fund.ocf_q.empty:
            cash = float(fund.cash.iloc[-1])
            ocf = float(fund.ocf_q.iloc[-1])
            if ocf < 0:
                burn = -ocf
                runway = cash / burn if burn > 0 else 99
                if runway < tx.TRAP_RUNWAY_QUARTERS:
                    comps.append(_clip((tx.TRAP_RUNWAY_QUARTERS - runway) / tx.TRAP_RUNWAY_QUARTERS))
                    ev.append(f"runway ~{runway:.1f}q at current burn")
        # secular decline (3y revenue CAGR < threshold and not accelerating)
        ttm = _ttm(fund.revenue_q)
        if len(ttm) >= 13:
            now, past = float(ttm.iloc[-1]), float(ttm.iloc[-13])
            if past > 0:
                cagr = (now / past) ** (1 / 3) - 1
                yoy = _yoy(fund.revenue_q)
                accel = float(yoy.diff().dropna().iloc[-1]) if len(yoy) >= 2 else 0.0
                if cagr < tx.TRAP_SECULAR_CAGR and accel <= 0:
                    comps.append(_clip((tx.TRAP_SECULAR_CAGR - cagr) / abs(tx.TRAP_SECULAR_CAGR)))
                    ev.append(f"secular: 3y rev CAGR {cagr:+.0%}, not accelerating")
    if not comps:
        return {"score": 0.0, "evidence": ev or ["no trap flags"]}
    score = _clip(0.5 * max(comps) + 0.5 * (sum(comps) / len(comps)))
    return {"score": score, "evidence": ev}


# --------------------------------------------------------------------------- D
def score_D(a: Optional[float], b: Optional[float], c: Optional[float],
            trap: float, prices: Optional[pd.DataFrame]) -> float:
    a = a or 0.0
    turn = max(b or 0.0, c or 0.0)
    mom = 0.0
    if prices is not None and not prices.empty and "Close" in prices:
        close = prices["Close"].dropna()
        if len(close) >= tx.SMA_FAST:
            sma = float(close.tail(tx.SMA_FAST).mean())
            mom = 1.0 if float(close.iloc[-1]) > sma else 0.0
    base = tx.D_W_A * a + tx.D_W_TURN * turn + tx.D_W_MOM * mom
    return _clip(base) * (1.0 - tx.D_TRAP_PENALTY * trap)


# --------------------------------------------------------------------- orchestr.
def compute_dimensions(ticker: str, T, with_text: bool = True,
                       cf: Optional[dict] = None) -> dict:
    """Compute all dimensions for one (ticker, T) from PIT inputs.

    Returns dict with scores A/B/C/trap_risk/D, the A gate, composite, and
    evidence. Used by Implementation B; the same taxonomy is documented for A.
    """
    prices = pit_prices(ticker, T)
    fund = pit_fundamentals(ticker, T, cf=cf)

    a = score_A(prices, fund)
    b = score_B(fund)
    trap = trap_risk(fund, prices)

    c = {"score": None, "evidence": ["text not fetched"]}
    if with_text:
        try:
            filings = recent_filings(ticker, T, ("10-K", "10-Q"), limit=2)
            text_now = fetch_filing_text(filings[0]) if filings else ""
            text_prev = fetch_filing_text(filings[1]) if len(filings) > 1 else ""
            c = score_C(text_now, text_prev)
        except Exception as e:  # noqa: BLE001
            c = {"score": None, "evidence": [f"text error: {e}"]}

    d = score_D(a["score"], b["score"], c["score"], trap["score"], prices)
    turn = max(b["score"] or 0.0, c["score"] or 0.0)
    composite = sum([a["score"] or 0.0, turn, 1.0 - trap["score"]]) / 3.0

    return {
        "ticker": ticker,
        "as_of": str(pd.Timestamp(T).date()),
        "passes_A_gate": a["gate"],
        "scores": {
            "A": a["score"], "B": b["score"], "C": c["score"],
            "trap_risk": trap["score"], "D": d,
        },
        "composite": round(composite, 4),
        "B_turning": b.get("turning", False),
        "evidence": {
            "A": a["evidence"], "B": b["evidence"],
            "C": c["evidence"], "trap_risk": trap["evidence"],
        },
        "n_quarters": fund.n_quarters,
        "price_rows": 0 if prices is None or prices.empty else len(prices),
    }
