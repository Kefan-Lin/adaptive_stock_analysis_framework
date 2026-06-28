"""LIVE-ONLY US/ADR/foreign quarterly fundamentals via akshare (Eastmoney).

Fills the foreign-filer gap the SEC us-gaap/ifrs pipeline cannot: akshare returns
standardized quarterly statements for BILI, NOK, ADRs, etc.

**NOT POINT-IN-TIME.** `stock_financial_us_report_em` carries only the period end
(REPORT_DATE), no announcement/filing date, and the values are current-restated.
Using it in the backtest would reintroduce look-ahead (the MF6 leak the SEC
pipeline closes). It is therefore for LIVE discovery only and must never be
called from the backtest path.
"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from ..pit.fundamentals import Fundamentals

_INCOME, _BALANCE, _CASHFLOW = "综合损益表", "资产负债表", "现金流量表"

REV_ITEMS = ["营业收入", "主营收入"]
COGS_ITEMS = ["营业成本", "主营成本"]
GP_ITEMS = ["毛利"]
EPS_ITEMS = ["摊薄每股收益-普通股", "基本每股收益-普通股", "摊薄每股收益-ADS", "基本每股收益-ADS"]
SHARES_ITEMS = ["摊薄加权平均股数-普通股", "基本加权平均股数-普通股"]
INV_ITEMS = ["存货"]
CASH_ITEMS = ["现金及现金等价物"]
OCF_ITEMS = ["经营活动产生的现金流量净额"]


def _report(stock: str, symbol: str) -> Optional[pd.DataFrame]:
    import akshare as ak
    try:
        return ak.stock_financial_us_report_em(stock=stock, symbol=symbol, indicator="单季报")
    except Exception:
        return None


def _series(df: Optional[pd.DataFrame], items: List[str]) -> pd.Series:
    if df is None or len(df) == 0 or "ITEM_NAME" not in df:
        return pd.Series(dtype=float)
    for it in items:
        sub = df[df["ITEM_NAME"] == it]
        if len(sub):
            s = pd.Series(
                pd.to_numeric(sub["AMOUNT"], errors="coerce").values,
                index=pd.to_datetime(sub["REPORT_DATE"]),
            ).dropna()
            s = s[~s.index.duplicated(keep="first")].sort_index()
            if len(s):
                return s
    return pd.Series(dtype=float)


def live_fundamentals(ticker: str) -> Fundamentals:
    """Build a Fundamentals (same shape as pit_fundamentals) from akshare. LIVE."""
    inc = _report(ticker, _INCOME)
    bal = _report(ticker, _BALANCE)
    cfs = _report(ticker, _CASHFLOW)
    return Fundamentals(
        ticker=ticker,
        as_of=pd.Timestamp.now().normalize(),
        revenue_q=_series(inc, REV_ITEMS),
        gross_profit_q=_series(inc, GP_ITEMS),
        cogs_q=_series(inc, COGS_ITEMS),
        inventory=_series(bal, INV_ITEMS),
        eps_q=_series(inc, EPS_ITEMS),
        shares=_series(inc, SHARES_ITEMS),
        cash=_series(bal, CASH_ITEMS),
        ocf_q=_series(cfs, OCF_ITEMS),
    )
