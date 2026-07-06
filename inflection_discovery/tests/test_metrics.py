from inflection_discovery.harness.metrics import wilson, fmt_ci


def _cand(ticker, d_score, engine="B"):
    from inflection_discovery.contract import Candidate
    return Candidate(
        ticker=ticker, as_of_date="2023-06-30", passes_A_gate=True,
        scores={"A": 0.9, "B": 0.6, "C": 0.5, "trap_risk": 0.1, "D": d_score},
        composite=0.5, engine=engine,
    )


def test_adv_haircut_excludes_illiquid_from_topN(monkeypatch):
    """A benchmark name that clears A+trap and would rank into top-N is dropped
    from top-N when its median dollar ADV is below MIN_ADV_USD, and is surfaced in
    excluded_illiquid instead of counted as a hit. ADV lookup is monkeypatched so
    the test is fully offline."""
    from inflection_discovery.harness import backtest
    from inflection_discovery.benchmark import BenchmarkRow
    import pandas as pd

    thin = "THIN"
    # score_universe: the benchmark name ranks #1 by D; one liquid control follows.
    def fake_score_universe(universe, dt, top_n=20, with_text=False):
        cands = [_cand(thin, 0.99), _cand("LIQD", 0.80)]
        for i, c in enumerate(cands):
            c.rank = i + 1
        return cands, cands
    # THIN is thinly traded (below floor); everything else is liquid.
    def fake_adv(ticker, dt, days=60):
        return 10_000.0 if ticker == thin else 5_000_000.0

    monkeypatch.setattr(backtest, "score_universe", fake_score_universe)
    monkeypatch.setattr(backtest, "median_dollar_adv", fake_adv)

    row = BenchmarkRow(ticker=thin, label="positive",
                       t_star=pd.Timestamp("2023-09-30"), as_of=None,
                       inflection_type="turnaround", notes="")
    ev = backtest.evaluate_row(row, control=["LIQD"], top_n=10, with_text=False)
    # Present in the scored universe (has data) but never in top-N (illiquid).
    assert ev["no_data"] is False
    assert all(d["in_topN"] is False for d in ev["dates"])
    assert any(d.get("illiquid") for d in ev["dates"])

    results = {"top_n": 10, "control_universe": ["LIQD"], "rows": [ev]}
    summ = backtest.summarize(results)
    assert summ["positives"]["hits"] == 0
    assert any(thin in x for x in summ["excluded_illiquid"])


def test_wilson_empty():
    assert wilson(0, 0) == (0.0, 0.0, 0.0)


def test_wilson_point_estimates():
    p, lo, hi = wilson(10, 10)
    assert p == 1.0 and lo < 1.0 and hi == 1.0
    p, lo, hi = wilson(5, 10)
    assert abs(p - 0.5) < 1e-9 and lo < 0.5 < hi


def test_wilson_small_n_is_wide():
    # 14 positives -> a wide interval; this is the whole point of reporting CIs
    _, lo, hi = wilson(10, 14)
    assert (hi - lo) > 0.30


def test_fmt_ci():
    s = fmt_ci(7, 14)
    assert "7/14" in s and "CI" in s
