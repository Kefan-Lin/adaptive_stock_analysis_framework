#!/usr/bin/env python
"""Post-cutoff holdout: does engine A's ranking carry forward-return signal on a
universe whose OUTCOME is blind to the model (T after the Jan-2026 knowledge cutoff)?

Reads reports/holdout_universe.json (fresh depressed names @ T, no benchmark/control
overlap) and reports/llm_holdout_scores.json (A's B/C/trap, authored from <=T
evidence BEFORE any forward return was computed). Scores A (LLM judgment over the
SHARED A-gate/momentum/score_D) and B (engine_b, numeric), ranks both, and measures
realized forward return T -> today. Writes reports/holdout_results.json.

This is a tiny-n, ~5-month, single-regime directional probe -- NOT a labeled
hit/trap rate (no post-cutoff labels exist yet). Its only job: remove the
memorization confound from the A-vs-B forward-return comparison.

Usage: .venv/bin/python reports/run_holdout.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inflection_discovery.engine_b import score_one  # noqa: E402
from inflection_discovery.harness.metrics import mean  # noqa: E402
from inflection_discovery.pit.prices import pit_prices, forward_return  # noqa: E402
from inflection_discovery.scorecard import score as sc  # noqa: E402
from inflection_discovery.scorecard import taxonomy as tx  # noqa: E402

HERE = Path(__file__).resolve().parent
T = "2026-01-31"
FWD_MONTHS = 5  # T + 5mo ~= today (2026-06); forward_return uses latest available <= that
TOP_K = 5


def load(name):
    return json.loads((HERE / name).read_text())


def a_candidate(ticker, llm):
    b_cand = score_one(ticker, T, with_text=False)  # shared A-gate / A-score
    if b_cand is None:
        return None
    a_score = b_cand.scores.get("A")
    b, c, trap = llm["B"], llm["C"], llm["trap_risk"]
    prices = pit_prices(ticker, T)
    d = sc.score_D(a_score, b, c, trap, prices)
    return {"ticker": ticker, "A": a_score, "B": b, "C": c, "trap_risk": trap, "D": d,
            "gate": bool(b_cand.passes_A_gate), "engine": "A"}


def b_candidate(ticker):
    b = score_one(ticker, T, with_text=False)
    if b is None:
        return None
    s = b.scores
    return {"ticker": ticker, "A": s.get("A"), "B": s.get("B"), "C": s.get("C"),
            "trap_risk": s.get("trap_risk"), "D": s.get("D"), "gate": bool(b.passes_A_gate),
            "engine": "B"}


def eligible_sorted(cands):
    el = [c for c in cands if c["gate"] and (c["trap_risk"] or 0.0) <= tx.TRAP_CEILING]
    el.sort(key=lambda c: (c["D"] or 0.0), reverse=True)
    for i, c in enumerate(el):
        c["rank"] = i + 1
    return el


def main():
    universe = load("holdout_universe.json")
    llm = {r["ticker"]: r for r in load("llm_holdout_scores.json")["scores"]}
    fwd = {t: forward_return(t, T, FWD_MONTHS) for t in universe}

    a_all = [c for c in (a_candidate(t, llm[t]) for t in universe if t in llm) if c]
    b_all = [c for c in (b_candidate(t) for t in universe) if c]
    a_el = eligible_sorted(a_all)
    b_el = eligible_sorted(b_all)

    def topk_fwd(el, k):
        rets = [fwd[c["ticker"]] for c in el[:k] if fwd.get(c["ticker"]) is not None]
        return mean(rets), [c["ticker"] for c in el[:k]], rets

    pool_rets = [v for v in fwd.values() if v is not None]
    a_top_mean, a_top, a_top_rets = topk_fwd(a_el, TOP_K)
    b_top_mean, b_top, b_top_rets = topk_fwd(b_el, TOP_K)

    # A trap discrimination: forward of names A FLAGS as trap (ineligible by trap) vs clears
    a_flagged = [c["ticker"] for c in a_all if (c["trap_risk"] or 0) > tx.TRAP_CEILING]
    a_cleared = [c["ticker"] for c in a_all if (c["trap_risk"] or 0) <= tx.TRAP_CEILING and c["gate"]]
    flagged_fwd = mean([fwd[t] for t in a_flagged if fwd.get(t) is not None])
    cleared_fwd = mean([fwd[t] for t in a_cleared if fwd.get(t) is not None])

    out = {
        "T": T, "fwd_months": FWD_MONTHS, "top_k": TOP_K,
        "universe_n": len(universe), "scored_a": len(a_all), "eligible_a": len(a_el),
        "eligible_b": len(b_el),
        "pool_fwd_mean": mean(pool_rets), "pool_fwd_n": len(pool_rets),
        "A_top": {"tickers": a_top, "fwd_mean": a_top_mean, "rets": a_top_rets},
        "B_top": {"tickers": b_top, "fwd_mean": b_top_mean, "rets": b_top_rets},
        "A_trap_discrimination": {
            "flagged_tickers": a_flagged, "flagged_fwd_mean": flagged_fwd,
            "cleared_tickers": a_cleared, "cleared_fwd_mean": cleared_fwd},
        "per_name": [
            {"ticker": t,
             "A_D": next((c["D"] for c in a_all if c["ticker"] == t), None),
             "A_rank": next((c.get("rank") for c in a_el if c["ticker"] == t), None),
             "A_trap": (llm[t]["trap_risk"] if t in llm else None),
             "B_D": next((c["D"] for c in b_all if c["ticker"] == t), None),
             "B_rank": next((c.get("rank") for c in b_el if c["ticker"] == t), None),
             "fwd": fwd.get(t)}
            for t in universe],
    }
    (HERE / "holdout_results.json").write_text(json.dumps(out, indent=1, default=str))

    def p(x):
        return "n/a" if x != x or x is None else f"{x*100:+.0f}%"
    print(f"=== POST-CUTOFF HOLDOUT  T={T}  fwd~{FWD_MONTHS}mo  (n={len(universe)} depressed) ===")
    print(f"  A top-{TOP_K} fwd {p(a_top_mean)}  {a_top}")
    print(f"  B top-{TOP_K} fwd {p(b_top_mean)}  {b_top}")
    print(f"  depressed-pool base rate {p(out['pool_fwd_mean'])} (n={out['pool_fwd_n']})")
    print(f"  A trap-flagged fwd {p(flagged_fwd)} ({len(a_flagged)}) vs A-cleared fwd {p(cleared_fwd)} ({len(a_cleared)})")
    print("  wrote reports/holdout_results.json")


if __name__ == "__main__":
    main()
