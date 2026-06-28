import math

import pandas as pd

from inflection_discovery.ashare.data import _num, _pct, ashare_fundamentals
from inflection_discovery.ashare.discover import score_one_ashare


# --- offline parsing ---
def test_num_parsing():
    assert abs(_num("261.71亿") - 2.6171e10) < 1
    assert abs(_num("5.2万") - 52000) < 1
    assert _num(False) != _num(False) or math.isnan(_num(False))  # nan
    assert math.isnan(_num("--"))


def test_pct_parsing():
    assert abs(_pct("15.54%") - 0.1554) < 1e-9
    assert math.isnan(_pct(False))


# --- network: real A-share data ---
def test_ashare_fundamentals_cosco():
    f = ashare_fundamentals("601919")  # 中远海控
    assert not f.empty and len(f) >= 8
    gm = f["gross_margin"].dropna()
    assert len(gm) >= 4 and -1.0 < float(gm.iloc[-1]) < 1.0


def test_score_one_ashare():
    c = score_one_ashare("601919")
    assert c.scores["B"] is not None
    assert any("A-share" in m for m in c.evidence["market"])
