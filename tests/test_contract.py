from inflection_discovery.contract import Candidate, validate, make_routing


def _good():
    return Candidate(
        ticker="MU", as_of_date="2023-09-30", passes_A_gate=True,
        scores={"A": 0.6, "B": 0.55, "C": None, "trap_risk": 0.0, "D": 0.6},
        composite=0.7, engine="B", routing=make_routing("MU", "NASDAQ"),
    ).to_dict()


def test_valid_candidate():
    assert validate(_good()) == []


def test_missing_scores_key():
    c = _good()
    del c["scores"]["B"]
    errs = validate(c)
    assert any("scores missing key: B" in e for e in errs)


def test_bad_engine():
    c = _good()
    c["engine"] = "X"
    assert any("engine must be" in e for e in validate(c))


def test_out_of_range_score():
    c = _good()
    c["scores"]["A"] = 1.5
    assert any("score A must be in" in e for e in validate(c))


def test_routing_sets_turnaround_style():
    r = make_routing("AXTI", "NASDAQ")
    assert r["suggested_style"] == "turnaround" and r["tradable_line"] == "AXTI"
