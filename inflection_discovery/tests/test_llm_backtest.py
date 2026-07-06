"""Offline wiring tests for the Implementation A (LLM) comparison-mode backtest.

These do NOT hit the network: they check that the authored LLM scores stay in
sync with the benchmark, are well-formed, and that an A candidate assembled from
them via the SHARED score_D / contract is valid and on the same [0,1] scale as B.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from inflection_discovery.benchmark import load_benchmark
from inflection_discovery.contract import validate
from inflection_discovery.harness.llm_backtest import load_llm_scores
from inflection_discovery.scorecard import score as sc

REPORTS = Path(__file__).resolve().parents[2] / "reports"

NO_DATA = {"WBA"}  # delisted on yfinance — both engines exclude (see report)


def _primary_dates(row):
    if row.label == "positive":
        hd = row.hit_date()
        return [hd] if hd is not None else []
    return row.as_of_dates()


def test_llm_scores_cover_benchmark():
    """Every benchmark (ticker, primary-date) the A engine scores has a judgment
    (except known no-data names), so the file can't silently drift from the CSV."""
    llm = load_llm_scores()
    missing = []
    for row in load_benchmark():
        if row.ticker in NO_DATA:
            continue
        for dt in _primary_dates(row):
            key = (row.ticker, str(pd.Timestamp(dt).date()))
            if key not in llm:
                missing.append(key)
    assert not missing, f"llm_scores.json missing judgments for: {missing}"


def test_llm_scores_well_formed():
    llm = load_llm_scores()
    assert llm, "no LLM scores loaded"
    for (tk, dt), r in llm.items():
        for k in ("B", "C", "trap_risk"):
            v = r[k]
            assert isinstance(v, (int, float)) and 0.0 <= v <= 1.0, f"{tk}@{dt} {k}={v!r}"
        assert r.get("note"), f"{tk}@{dt} missing audit note"


def test_a_candidate_is_valid_contract():
    """An A candidate built from authored B/C/trap + shared score_D validates and
    lands in [0,1] — i.e. it is rankable against B in the same harness."""
    llm = load_llm_scores()
    r = llm[("AXTI", "2024-06-30")]
    a_score = 0.64  # shared A engine value (illustrative; real run uses score_A)
    d = sc.score_D(a_score, r["B"], r["C"], r["trap_risk"], None)
    assert 0.0 <= d <= 1.0
    cand = {
        "ticker": "AXTI", "as_of_date": "2024-06-30", "passes_A_gate": True,
        "scores": {"A": a_score, "B": r["B"], "C": r["C"], "trap_risk": r["trap_risk"], "D": d},
        "composite": 0.5, "engine": "A",
    }
    assert validate(cand) == []


# The one intrinsically-ambiguous trap: INTC's 2023 "fake start" reads like a
# real cyclical trough on the as-of numbers (rev decline decelerating, GM
# recovered, EPS positive). A is honestly fooled here too — documented in the
# report as the irreducible hard case, so it is allow-listed rather than papered
# over. Keep this set tiny: it is the explicit limit of free-data separability.
AMBIGUOUS_TRAPS = {("INTC", "2023-09-30")}


def test_traps_score_high_or_low_turn():
    """Every labeled trap is either flagged structurally (trap_risk high) or has a
    weak turn (low max(B,C)) — never 'clean turn + low trap' — EXCEPT the small,
    documented set of intrinsically-ambiguous fake-starts."""
    llm = load_llm_scores()
    offenders = []
    for (tk, dt), r in llm.items():
        if r["label"] != "negative":
            continue
        turn = max(r["B"], r["C"])
        if not (r["trap_risk"] >= 0.6 or turn <= 0.5):
            offenders.append((tk, dt))
    assert set(offenders) <= AMBIGUOUS_TRAPS, (
        f"undocumented trap(s) scored like a clean turnaround: {set(offenders) - AMBIGUOUS_TRAPS}")
    assert AMBIGUOUS_TRAPS <= set(offenders), (
        "the documented fake-start is no longer ambiguous — update AMBIGUOUS_TRAPS")


def test_holdout_scores_cover_universe():
    """The post-cutoff holdout scores stay in sync with the sampled universe and
    are well-formed (so reports/run_holdout.py is reproducible)."""
    uni = json.loads((REPORTS / "holdout_universe.json").read_text())
    scores = {r["ticker"]: r for r in json.loads((REPORTS / "llm_holdout_scores.json").read_text())["scores"]}
    missing = [t for t in uni if t not in scores]
    assert not missing, f"llm_holdout_scores.json missing: {missing}"
    for t, r in scores.items():
        for k in ("B", "C", "trap_risk"):
            v = r[k]
            assert isinstance(v, (int, float)) and 0.0 <= v <= 1.0, f"{t} {k}={v!r}"
        assert r.get("note"), f"{t} missing audit note"
