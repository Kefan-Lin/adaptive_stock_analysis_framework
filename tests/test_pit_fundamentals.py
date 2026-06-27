"""Tests the corrected MF6 selector: latest `filed` <= T per period (a
restatement filed *before* T is the truth at T and wins; observations filed
after T are excluded). Pure offline — companyfacts is injected."""
import pandas as pd

from inflection_discovery.pit.fundamentals import pit_fundamentals


def _cf(observations):
    return {"facts": {"us-gaap": {"Revenues": {"units": {"USD": observations}}}}}


def test_latest_filed_before_T_wins_over_original():
    cf = _cf([
        {"start": "2024-03-01", "end": "2024-05-30", "val": 100, "filed": "2024-06-27", "form": "10-Q"},
        {"start": "2024-03-01", "end": "2024-05-30", "val": 110, "filed": "2024-08-01", "form": "10-Q/A"},
        {"start": "2024-03-01", "end": "2024-05-30", "val": 999, "filed": "2025-01-01", "form": "10-Q/A"},
    ])
    f = pit_fundamentals("X", "2024-09-30", cf=cf)
    v = float(f.revenue_q[pd.Timestamp("2024-05-30")])
    assert v == 110  # the before-T restatement, not original 100, not future 999


def test_future_filed_excluded():
    cf = _cf([
        {"start": "2024-03-01", "end": "2024-05-30", "val": 100, "filed": "2024-06-27", "form": "10-Q"},
    ])
    f = pit_fundamentals("X", "2024-06-20", cf=cf)  # T before the filing date
    assert f.revenue_q.empty


def test_quarter_duration_filter_excludes_annual():
    cf = _cf([
        {"start": "2023-06-01", "end": "2024-05-30", "val": 4000, "filed": "2024-06-27", "form": "10-K"},  # ~annual
    ])
    f = pit_fundamentals("X", "2024-09-30", cf=cf)
    assert f.revenue_q.empty  # 365d period is not a quarter
