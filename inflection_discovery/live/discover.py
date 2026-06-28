"""LIVE discovery entrypoint (NON-PIT) — uses today's data.

Fundamentals source per name: SEC us-gaap/ifrs when it yields enough quarters;
otherwise the akshare live source (foreign filers / ADRs like BILI, NOK). Prices
from yfinance, narrative C from the latest filings. Everything here is current
data — fine for live discovery, never used by the backtest.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import pandas as pd

from ..contract import Candidate, make_routing
from ..pit.filing_text import fetch_filing_text, recent_filings
from ..pit.fundamentals import pit_fundamentals
from ..pit.prices import pit_prices
from ..scorecard import taxonomy as tx
from ..scorecard.score import score_A, score_B, score_C, score_D, trap_risk
from .akshare_source import live_fundamentals


def score_one_live(ticker: str, with_text: bool = True) -> Candidate:
    today = pd.Timestamp.now().normalize()
    prices = pit_prices(ticker, today)

    f_sec = pit_fundamentals(ticker, today)
    if f_sec.n_quarters >= 4:
        fund, source = f_sec, "SEC us-gaap/ifrs"
    else:
        fund, source = live_fundamentals(ticker), "akshare (live, NON-PIT)"

    a = score_A(prices, fund)
    b = score_B(fund)
    trap = trap_risk(fund, prices)
    c = {"score": None, "evidence": ["text skipped"]}
    if with_text:
        try:
            fl = recent_filings(ticker, today, ("10-K", "10-Q", "20-F", "6-K"), limit=2)
            tn = fetch_filing_text(fl[0]) if fl else ""
            tp = fetch_filing_text(fl[1]) if len(fl) > 1 else ""
            c = score_C(tn, tp)
        except Exception:  # noqa: BLE001
            pass

    d = score_D(a["score"], b["score"], c["score"], trap["score"], prices)
    turn = max(b["score"] or 0.0, c["score"] or 0.0)
    composite = round(((a["score"] or 0.0) + turn + (1.0 - (trap["score"] or 0.0))) / 3.0, 4)
    return Candidate(
        ticker=ticker,
        as_of_date=str(today.date()),
        passes_A_gate=a["gate"],
        scores={"A": a["score"], "B": b["score"], "C": c["score"],
                "trap_risk": trap["score"], "D": d},
        composite=composite,
        engine="B",
        evidence={"A": a["evidence"], "B": b["evidence"], "C": c["evidence"],
                  "trap_risk": trap["evidence"],
                  "source": [f"fundamentals: {source}", "LIVE (non-PIT) discovery"]},
        routing=make_routing(ticker),
        thesis=f"{ticker} (live, {source}): A={a['score']} B={b['score']} C={c['score']}",
    )


def discover_live(tickers: Sequence[str], top_n: int = 20,
                  with_text: bool = True) -> Tuple[List[Candidate], List[Candidate]]:
    scored = [score_one_live(t, with_text=with_text) for t in tickers]
    eligible = [c for c in scored
                if c.passes_A_gate and (c.scores.get("trap_risk") or 0.0) <= tx.TRAP_CEILING]
    eligible.sort(key=lambda c: (c.scores.get("D") or 0.0), reverse=True)
    for i, c in enumerate(eligible):
        c.rank = i + 1
    return eligible, scored
