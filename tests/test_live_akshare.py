"""Live akshare adapter (network). Verifies the foreign-filer coverage win:
BILI/NOK get a real B signal that the PIT SEC pipeline could not produce."""
from inflection_discovery.live.akshare_source import live_fundamentals
from inflection_discovery.live.discover import score_one_live


def test_akshare_bili_has_quarterly_fundamentals():
    f = live_fundamentals("BILI")
    assert f.n_quarters >= 8
    gm = f.gross_margin_q()
    assert len(gm) >= 4 and 0.0 < float(gm.iloc[-1]) < 1.0  # sane gross margin


def test_score_one_live_bili_has_B():
    c = score_one_live("BILI", with_text=False)
    assert c.scores["B"] is not None  # was NA via the SEC-only pipeline
    assert any("akshare" in s for s in c.evidence["source"])
