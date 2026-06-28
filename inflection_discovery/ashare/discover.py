"""A-share LIVE discovery: A/B/D scoring for Chinese A-shares.

A (depressed base) from hfq prices (reuses score_A). B (earnings second
derivative) from THS precomputed quarterly YoY revenue growth + gross margin +
inventory-turnover days. Narrative C is omitted (no free A-share text engine
here). LIVE only — see package docstring on why PIT is not free-achievable.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import pandas as pd

from ..contract import Candidate, make_routing
from ..scorecard import taxonomy as tx
from ..scorecard.score import _clip, _logistic, score_A, score_D
from .data import ashare_fundamentals, ashare_prices


def ashare_score_B(fund: pd.DataFrame) -> dict:
    if fund is None or fund.empty:
        return {"score": None, "turning": False, "evidence": ["no fundamentals"]}
    subs: List[float] = []
    turning = False
    ev: List[str] = []

    yoy = fund["rev_yoy"].dropna()
    if len(yoy) >= 2:
        accel = float(yoy.iloc[-1] - yoy.iloc[-2])
        subs.append(_logistic(accel / tx.B_ACCEL_SCALE))
        turning = turning or accel > 0
        ev.append(f"rev YoY accel {accel:+.1%} (YoY now {float(yoy.iloc[-1]):+.1%})")

    gm = fund["gross_margin"].dropna()
    gm = gm[(gm >= -1.0) & (gm <= 1.0)]
    if len(gm) >= 2:
        md = float(gm.iloc[-1] - gm.iloc[-2])
        trough = float(gm.tail(tx.B_MARGIN_TROUGH_WINDOW).min())
        off = _clip((float(gm.iloc[-1]) - trough) / tx.B_MARGIN_TROUGH_FULL)
        subs.append(_clip(0.5 * _logistic(md / tx.B_MARGIN_DELTA_SCALE) + 0.5 * off))
        turning = turning or md > 0
        ev.append(f"gross margin {float(gm.iloc[-1]):.1%} (Δ {md:+.1%})")

    inv = fund["inv_days"].dropna()
    if len(inv) >= 2 and float(inv.iloc[-2]) > 0:
        prev, cur = float(inv.iloc[-2]), float(inv.iloc[-1])
        subs.append(_clip(0.5 + (prev - cur) / prev))
        ev.append(f"inventory days {cur:.0f} vs {prev:.0f}")

    score = sum(subs) / len(subs) if subs else None
    return {"score": score, "turning": bool(turning), "evidence": ev}


def ashare_trap(fund: pd.DataFrame) -> dict:
    if fund is None or fund.empty:
        return {"score": 0.0, "evidence": ["no fundamentals"]}
    comps: List[float] = []
    ev: List[str] = []
    yoy = fund["rev_yoy"].dropna()
    if len(yoy) >= 4:
        recent = yoy.tail(4)
        improving = float(yoy.iloc[-1] - yoy.iloc[-2]) > 0
        if (recent < 0).all() and not improving:
            comps.append(_clip(min(0.9, -float(recent.mean()))))
            ev.append(f"secular: rev YoY {float(recent.mean()):+.0%} x4q, not improving")
    score = _clip(max(comps)) if comps else 0.0
    return {"score": score, "evidence": ev or ["no trap flags"]}


def _exchange(code: str) -> str:
    if code.startswith(("60", "68")):
        return "SSE"
    if code.startswith(("00", "30")):
        return "SZSE"
    return ""


def score_one_ashare(code: str) -> Candidate:
    prices = ashare_prices(code)
    fund = ashare_fundamentals(code)
    a = score_A(prices)
    b = ashare_score_B(fund)
    trap = ashare_trap(fund)
    d = score_D(a["score"], b["score"], None, trap["score"], prices)
    turn = b["score"] or 0.0
    composite = round(((a["score"] or 0.0) + turn + (1.0 - trap["score"])) / 3.0, 4)
    routing = make_routing(code, exchange=_exchange(code), currency="CNY")
    return Candidate(
        ticker=code,
        as_of_date=str(pd.Timestamp.now().normalize().date()),
        passes_A_gate=a["gate"],
        scores={"A": a["score"], "B": b["score"], "C": None,
                "trap_risk": trap["score"], "D": d},
        composite=composite,
        engine="B",
        evidence={"A": a["evidence"], "B": b["evidence"],
                  "trap_risk": trap["evidence"],
                  "market": ["China A-share LIVE (non-PIT; akshare restated values)"]},
        routing=routing,
        thesis=f"{code} A-share (live): A={a['score']} B={b['score']}",
    )


def discover_ashare(codes: Sequence[str], top_n: int = 20) -> Tuple[List[Candidate], List[Candidate]]:
    scored = [score_one_ashare(c) for c in codes]
    eligible = [c for c in scored
                if c.passes_A_gate and (c.scores.get("trap_risk") or 0.0) <= tx.TRAP_CEILING]
    eligible.sort(key=lambda c: (c.scores.get("D") or 0.0), reverse=True)
    for i, c in enumerate(eligible):
        c.rank = i + 1
    return eligible, scored
