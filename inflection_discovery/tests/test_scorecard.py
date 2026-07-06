import pandas as pd

from inflection_discovery.scorecard.score import _logistic, _clip, _yoy, score_A


def test_logistic_and_clip():
    assert abs(_logistic(0.0) - 0.5) < 1e-9
    assert _clip(1.5) == 1.0 and _clip(-0.2) == 0.0


def test_yoy_clips_extreme_base():
    # tiny prior base would explode; clip keeps it bounded
    idx = [pd.Timestamp("2022-05-30"), pd.Timestamp("2023-05-30")]
    s = pd.Series([0.001, 100.0], index=idx)
    y = _yoy(s)
    assert y.iloc[-1] <= 10.0  # clipped


def _prices(last):
    idx = pd.date_range("2021-01-01", periods=600, freq="B")
    vals = [100.0] * 599 + [last]
    return pd.DataFrame({"Close": pd.Series(vals, index=idx)})


def test_A_gate_triggers_on_drawdown():
    a = score_A(_prices(60.0))   # 40% drawdown
    assert a["gate"] is True and a["score"] > 0.5


def test_A_gate_rejects_shallow_drawdown():
    a = score_A(_prices(85.0))   # 15% drawdown
    assert a["gate"] is False


def test_yoy_skips_negative_prior_base():
    import pandas as pd
    from inflection_discovery.scorecard.score import _yoy
    idx = pd.to_datetime(["2024-03-31", "2025-03-31"])
    s = pd.Series([-10.0, 5.0], index=idx)
    out = _yoy(s)
    assert idx[1] not in out.index, "negative prior base must not produce a sign-flipped growth rate"
