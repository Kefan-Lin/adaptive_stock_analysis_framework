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


def test_canonical_symbol_bridge():
    from inflection_discovery.symbols import canonical_symbol
    assert canonical_symbol("600519", exchange="SSE") == ("600519.SH", "CN")
    assert canonical_symbol("000001", exchange="SZSE") == ("000001.SZ", "CN")
    assert canonical_symbol("430047", exchange="BSE") == ("430047.BJ", "CN")
    assert canonical_symbol("700", exchange="HKEX") == ("0700.HK", "HK")
    assert canonical_symbol("AXTI") == ("AXTI", "US")


def test_symbol_patterns_match_repo_validator():
    """The bridge must stay in lockstep with scripts/validate_records.py."""
    import importlib.util, pathlib
    from inflection_discovery.symbols import SYMBOL_PATTERNS as PKG
    spec = importlib.util.spec_from_file_location(
        "validate_records", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "validate_records.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert {k: p.pattern for k, p in PKG.items()} == {k: p.pattern for k, p in mod.SYMBOL_PATTERNS.items()}


def test_routing_carries_canonical_symbol():
    r = make_routing("600519", exchange="SSE", currency="CNY")
    assert r["symbol"] == "600519.SH" and r["market"] == "CN"


def test_routing_never_crashes_on_uncanonicalizable():
    r = make_routing("430047", exchange="")  # bare BSE code, no exchange hint
    assert r["symbol"] == "" and r["market"] == ""
    assert "canonicalization_error" in r


def test_validate_rejects_symbol_without_matching_market():
    c = _good()
    c["symbol"] = "600519"  # not canonical for market CN
    c["market"] = "CN"
    assert any("symbol" in e and "600519" in e for e in validate(c))


def test_validate_accepts_canonical_symbol_and_market():
    c = _good()
    c["symbol"] = "600519.SH"
    c["market"] = "CN"
    assert validate(c) == []
