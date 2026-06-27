from inflection_discovery.harness.metrics import wilson, fmt_ci


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
