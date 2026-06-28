"""Implementation B — code-first Inflection Score pipeline.

Scores a universe at a point in time using the shared scorecard, gates on A,
applies the trap ceiling, ranks the survivors by D, and emits candidate
contracts. Deterministic and fully backtestable.
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from ..contract import Candidate, make_routing
from ..scorecard import compute_dimensions
from ..scorecard import taxonomy as tx


def _thesis(ticker: str, d: dict) -> str:
    s = d["scores"]
    parts: List[str] = []
    if d["passes_A_gate"]:
        parts.append("depressed base")
    if (s["B"] or 0) > 0.5:
        parts.append("earnings 2nd-derivative turning up")
    if (s["C"] or 0) > 0.5:
        parts.append("narrative re-rating")
    tr = s["trap_risk"] or 0.0
    risk = "low trap risk" if tr < 0.3 else f"elevated trap risk ({tr:.2f})"
    body = ", ".join(parts) if parts else "no clear inflection"
    return f"{ticker} @ {d['as_of']}: {body}; {risk}. Route to analyzing-stocks."


def score_one(ticker: str, T, with_text: bool = True,
              cf: Optional[dict] = None) -> Optional[Candidate]:
    try:
        d = compute_dimensions(ticker, T, with_text=with_text, cf=cf)
    except Exception:
        return None
    if d["price_rows"] == 0 and d["n_quarters"] == 0:
        return None  # data-availability gate: nothing reconstructable
    return Candidate(
        ticker=ticker,
        as_of_date=d["as_of"],
        passes_A_gate=d["passes_A_gate"],
        scores=d["scores"],
        composite=d["composite"],
        engine="B",
        evidence=d["evidence"],
        routing=make_routing(ticker),
        thesis=_thesis(ticker, d),
    )


def score_universe(tickers: Sequence[str], T, top_n: int = 20,
                   with_text: bool = False) -> Tuple[List[Candidate], List[Candidate]]:
    """Return (ranked_eligible_topN_first, all_scored).

    Eligible = passes A gate AND trap_risk <= ceiling. Eligible are ranked by D
    (descending); ``rank`` is assigned 1..k. Non-eligible are returned in
    all_scored for diagnostics but never ranked.
    """
    scored: List[Candidate] = []
    seen = set()
    for t in tickers:
        if t in seen:
            continue
        seen.add(t)
        c = score_one(t, T, with_text=with_text)
        if c is not None:
            scored.append(c)
    # Eligibility = passes A gate AND trap_risk under ceiling. (A turn-strength
    # gate on max(B,C) was tried and removed: on this data, deeply-depressed real
    # turnarounds — META/NVDA/NFLX at their troughs — have turn scores that overlap
    # the value traps, so any threshold that excludes traps also kills positives.
    # Discrimination is left to ¬trap + ranking by D, not a hard turn gate.)
    eligible = [
        c for c in scored
        if c.passes_A_gate and (c.scores.get("trap_risk") or 0.0) <= tx.TRAP_CEILING
    ]
    eligible.sort(key=lambda c: (c.scores.get("D") or 0.0), reverse=True)
    for i, c in enumerate(eligible):
        c.rank = i + 1
    return eligible, scored
