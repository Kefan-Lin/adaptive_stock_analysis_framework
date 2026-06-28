"""A-share data adapters (LIVE).

- ashare_prices(code): hfq (后复权) daily history -> Close/Volume. hfq is anchored
  at listing and only rescales on subsequent actions, so a truncated series is
  point-in-time-safe for the price (A) dimension.
- ashare_fundamentals(code): per-stock quarterly fundamentals via THS abstract
  (营业总收入 / 同比 / 销售毛利率 / 存货周转天数). Current-restated values, no
  original announcement date -> LIVE only (see package docstring).
"""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd


def ashare_prices(code: str) -> pd.DataFrame:
    import akshare as ak
    try:
        h = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="hfq")
    except Exception:
        return pd.DataFrame()
    if h is None or len(h) == 0:
        return pd.DataFrame()
    h = h.rename(columns={"日期": "Date", "收盘": "Close", "成交量": "Volume"})
    h["Date"] = pd.to_datetime(h["Date"])
    h = h.set_index("Date").sort_index()
    return h[["Close", "Volume"]]


def _num(x) -> float:
    """Parse Chinese-formatted numbers: '261.71亿' -> 2.6171e10, '5.2万' -> 52000."""
    if x is None or x is False or (isinstance(x, float) and pd.isna(x)):
        return float("nan")
    s = str(x).strip()
    if s in ("", "False", "--", "nan"):
        return float("nan")
    mult = 1.0
    if s.endswith("万亿"):
        mult, s = 1e12, s[:-2]
    elif s.endswith("亿"):
        mult, s = 1e8, s[:-1]
    elif s.endswith("万"):
        mult, s = 1e4, s[:-1]
    s = s.replace(",", "").replace("%", "")
    try:
        return float(s) * mult
    except ValueError:
        return float("nan")


def _pct(x) -> float:
    """Parse '15.54%' -> 0.1554; False/NA -> nan."""
    if x is None or x is False:
        return float("nan")
    s = str(x).strip()
    if s in ("", "False", "--", "nan"):
        return float("nan")
    try:
        return float(s.replace("%", "")) / 100.0
    except ValueError:
        return float("nan")


def ashare_fundamentals(code: str) -> pd.DataFrame:
    """Quarterly per-stock fundamentals. Columns: revenue, rev_yoy, gross_margin,
    np_yoy, inv_days — indexed by period end. LIVE / restated values."""
    import akshare as ak
    try:
        d = ak.stock_financial_abstract_ths(symbol=code, indicator="按单季度")
    except Exception:
        return pd.DataFrame()
    if d is None or len(d) == 0 or "报告期" not in d:
        return pd.DataFrame()
    out = pd.DataFrame(index=pd.to_datetime(d["报告期"]))
    out["revenue"] = d["营业总收入"].map(_num).values
    out["rev_yoy"] = d["营业总收入同比增长率"].map(_pct).values
    out["gross_margin"] = d["销售毛利率"].map(_pct).values
    out["np_yoy"] = d["净利润同比增长率"].map(_pct).values
    if "存货周转天数" in d:
        out["inv_days"] = pd.to_numeric(d["存货周转天数"], errors="coerce").values
    else:
        out["inv_days"] = float("nan")
    return out.sort_index()
