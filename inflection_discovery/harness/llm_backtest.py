"""Comparison-mode backtest for Implementation A (LLM judgment).

The honest experiment: hold the *entire* machinery shared with engine B fixed —
the depressed-base A gate, price momentum, the 65-name control arm, the ``score_D``
aggregation, and every metric definition in ``summarize`` — and swap ONLY the
B / C / trap judgment of the benchmark candidate. Engine B reads those from
numeric features + keyword counting; engine A reads them from the frozen <=T EDGAR
text + PIT fundamentals (scores authored in ``reports/llm_scores.json``).

Each benchmark name is ranked against the *identical* control backdrop that
engine B faces (controls are scored by ``engine_b.score_one``), so the A-vs-B
hit/trap delta is a clean ablation of "LLM judgment vs code features", with the
metric math byte-identical to the engine-B run (same ``summarize``).

Caveats (see report): A's benchmark numbers are a memorization-contaminated UPPER
BOUND; the control arm stays B-scored on purpose (LLM-scoring 65 random tickers
would be *more* biased — asymmetric memorization — and intractable). Positives are
scored at the single fixed hit-date (t*-3mo), so per-A lead-time is not measured.

Usage:  .venv/bin/python -m inflection_discovery.harness.llm_backtest --top-n 10
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

from ..benchmark import load_benchmark, BenchmarkRow
from ..contract import Candidate, make_routing
from ..engine_b import score_one
from ..pit.prices import pit_prices
from ..scorecard import score as sc
from ..scorecard import taxonomy as tx
from .backtest import build_control_universe, summarize

LLM_SCORES = Path(__file__).resolve().parents[2] / "reports" / "llm_scores.json"


def load_llm_scores(path: Path = LLM_SCORES) -> Dict[Tuple[str, str], dict]:
    raw = json.loads(path.read_text())
    out: Dict[Tuple[str, str], dict] = {}
    for r in raw["scores"]:
        out[(r["ticker"], r["as_of"])] = r
    return out


# --- per-(ticker, date) caches so the A and B passes share control scoring ---
_ONE: Dict[Tuple[str, str], Optional[Candidate]] = {}


def _score_b(ticker: str, T, with_text: bool) -> Optional[Candidate]:
    key = (ticker.upper(), str(pd.Timestamp(T).date()))
    if key not in _ONE:
        _ONE[key] = score_one(ticker, T, with_text=with_text)
    return _ONE[key]


_CTRL: Dict[str, List[Candidate]] = {}


def _control_scored(control: Sequence[str], T, with_text: bool) -> List[Candidate]:
    key = str(pd.Timestamp(T).date())
    if key not in _CTRL:
        out = []
        for c in control:
            cand = _score_b(c, T, with_text)
            if cand is not None:
                out.append(cand)
        _CTRL[key] = out
    return _CTRL[key]


def _make_a_candidate(ticker: str, T, llm: dict, b_cand: Candidate) -> Candidate:
    """A candidate: A-gate/A-score/momentum SHARED with B; B/C/trap from the LLM;
    D from the shared ``score_D``."""
    a_score = b_cand.scores.get("A")  # identical depressed-base engine
    gate = b_cand.passes_A_gate
    b, c, trap = llm["B"], llm["C"], llm["trap_risk"]
    prices = pit_prices(ticker, T)  # for the shared momentum term in score_D
    d = sc.score_D(a_score, b, c, trap, prices)
    turn = max(b or 0.0, c or 0.0)
    composite = (([a_score or 0.0][0]) + turn + (1.0 - trap)) / 3.0
    return Candidate(
        ticker=ticker,
        as_of_date=str(pd.Timestamp(T).date()),
        passes_A_gate=bool(gate),
        scores={"A": a_score, "B": b, "C": c, "trap_risk": trap, "D": d},
        composite=round(composite, 4),
        engine="A",
        evidence={"llm": [llm.get("note", "")]},
        routing=make_routing(ticker),
        thesis=llm.get("note", ""),
    )


def _rank(universe: List[Candidate], top_n: int) -> List[Candidate]:
    eligible = [
        c for c in universe
        if c.passes_A_gate and (c.scores.get("trap_risk") or 0.0) <= tx.TRAP_CEILING
    ]
    eligible.sort(key=lambda c: (c.scores.get("D") or 0.0), reverse=True)
    for i, c in enumerate(eligible):
        c.rank = i + 1
    return eligible


def _eval_engine(row: BenchmarkRow, control: Sequence[str], top_n: int,
                 with_text: bool, llm: Dict[Tuple[str, str], dict],
                 engine: str) -> Dict:
    """One benchmark row, one engine. Output shape == harness.evaluate_row."""
    out = {"ticker": row.ticker, "label": row.label, "type": row.inflection_type,
           "notes": row.notes, "dates": [], "no_data": True}
    hit_date = row.hit_date()
    # A scores positives at the hit-date only; B/neg use all as-of dates.
    if engine == "A" and row.label == "positive":
        dates = [hit_date] if hit_date is not None else []
    else:
        dates = row.as_of_dates()
    for dt in dates:
        b_cand = _score_b(row.ticker, dt, with_text)  # data-availability + B candidate
        had_data = b_cand is not None
        if engine == "A":
            key = (row.ticker, str(pd.Timestamp(dt).date()))
            self_c = _make_a_candidate(row.ticker, dt, llm[key], b_cand) if (had_data and key in llm) else None
        else:
            self_c = b_cand
        ctrl = _control_scored(control, dt, with_text)
        universe = ([self_c] if self_c is not None else []) + ctrl
        eligible = _rank(list(universe), top_n)
        topn = eligible[:top_n]
        in_top = self_c is not None and any(c.ticker == row.ticker and c.engine == self_c.engine for c in topn)
        rank = next((c.rank for c in topn if c.ticker == row.ticker and c.engine == (self_c.engine if self_c else "")), None)
        out["dates"].append({
            "as_of": str(pd.Timestamp(dt).date()),
            "is_hit_date": hit_date is not None and pd.Timestamp(dt) == pd.Timestamp(hit_date),
            "in_topN": bool(in_top),
            "rank": rank,
            "eligible_n": len(eligible),
            "gate": bool(self_c.passes_A_gate) if self_c else None,
            "scores": self_c.scores if self_c else None,
        })
        out["no_data"] = out["no_data"] and (not had_data)
    return out


def run_pair(top_n: int = 10, with_text: bool = True, control_keep: int = 65) -> Dict:
    rows = load_benchmark()
    bench = {r.ticker for r in rows}
    control = build_control_universe(keep=control_keep, exclude=bench)
    llm = load_llm_scores()
    res_a = {"top_n": top_n, "with_text": with_text, "control_universe": control,
             "control_n": len(control),
             "rows": [_eval_engine(r, control, top_n, with_text, llm, "A") for r in rows]}
    res_b = {"top_n": top_n, "with_text": with_text, "control_universe": control,
             "control_n": len(control),
             "rows": [_eval_engine(r, control, top_n, with_text, llm, "B") for r in rows]}
    return {"A": {"raw": res_a, "summary": summarize(res_a)},
            "B": {"raw": res_b, "summary": summarize(res_b)}}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--control-keep", type=int, default=65)
    ap.add_argument("--no-text", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    res = run_pair(top_n=a.top_n, with_text=not a.no_text, control_keep=a.control_keep)
    for eng in ("A", "B"):
        s = res[eng]["summary"]
        p, n = s["positives"], s["negatives"]
        print(f"\n=== engine {eng} (top-{a.top_n}, control={s['control_n']}, median_elig={s['median_eligible_n']}) ===")
        print(f"  hit  {p['hits']}/{p['n']} = {p['hit_rate'][0]*100:.0f}% (CI {p['hit_rate'][1]*100:.0f}-{p['hit_rate'][2]*100:.0f}%)")
        print(f"  trap {n['traps']}/{n['n']} = {n['trap_rate'][0]*100:.0f}% (CI {n['trap_rate'][1]*100:.0f}-{n['trap_rate'][2]*100:.0f}%)  [lower=better]")
        fr = s["forward_return"]
        print(f"  fwd12 picks +{fr['picks_12m']*100:.0f}% vs control +{fr['control_12m']*100:.0f}% (n_picks={fr['n_picks']})")
    if a.out:
        Path(a.out).write_text(json.dumps(res, default=str, indent=1))
        print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
