"""pit_fundamentals — as-of-T numeric financials from SEC companyfacts.

Resolves review MF6 (corrected): for each (concept, period) we keep the
observation with the **latest `filed` date <= T** — a restatement filed before T
was the public truth at T, so it is used; observations filed after T are
discarded. Concepts are *merged* (not first-wins) to survive XBRL tag drift
(e.g. ``Revenues`` -> ``RevenueFromContractWithCustomerExcludingAssessedTax``).

companyfacts covers only numeric XBRL facts; narrative text (dimension C) and
backlog/book-to-bill come from `pit_filing_text`, not here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import pandas as pd

from .. import edgar

REVENUE_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
]
GROSS_PROFIT_CONCEPTS = ["GrossProfit"]
COGS_CONCEPTS = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]
INVENTORY_CONCEPTS = ["InventoryNet"]
EPS_CONCEPTS = ["EarningsPerShareDiluted", "EarningsPerShareBasic"]
CASH_CONCEPTS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
]
OCF_CONCEPTS = ["NetCashProvidedByUsedInOperatingActivities"]
SHARES_CONCEPTS = ["CommonStockSharesOutstanding", "CommonStockSharesIssued"]
SHARES_DEI = ["EntityCommonStockSharesOutstanding"]

_QUARTER_MIN, _QUARTER_MAX = 80, 100  # days; one fiscal quarter (13-14 weeks)


def _facts(cf, taxonomy: str = "us-gaap") -> dict:
    return (cf or {}).get("facts", {}).get(taxonomy, {})


def _pick_unit(units: dict, prefer: Sequence[str]) -> list:
    for u in prefer:
        if u in units:
            return units[u]
    return next(iter(units.values()), [])


def _merged_series(cf, concepts, T, kind="duration", prefer=("USD",), taxonomy="us-gaap") -> pd.Series:
    """Latest-filed<=T value per period, merged across concepts (tag drift)."""
    us = _facts(cf, taxonomy)
    T = pd.Timestamp(T)
    by_period: dict = {}
    for concept in concepts:
        node = us.get(concept)
        if not node:
            continue
        for ob in _pick_unit(node.get("units", {}), prefer):
            filed = ob.get("filed")
            end = ob.get("end")
            if not filed or not end:
                continue
            if pd.Timestamp(filed) > T:
                continue  # not public at T
            if kind == "duration":
                start = ob.get("start")
                if not start:
                    continue
                dur = (pd.Timestamp(end) - pd.Timestamp(start)).days
                if not (_QUARTER_MIN <= dur <= _QUARTER_MAX):
                    continue
                key = (start, end)
            else:  # instant (balance-sheet item)
                key = (None, end)
            prev = by_period.get(key)
            if prev is None or pd.Timestamp(filed) > pd.Timestamp(prev["filed"]):
                by_period[key] = ob
    if not by_period:
        return pd.Series(dtype=float)
    data = {pd.Timestamp(ob["end"]): float(ob["val"]) for ob in by_period.values()}
    s = pd.Series(data).sort_index()
    return s[~s.index.duplicated(keep="last")]


@dataclass
class Fundamentals:
    ticker: str
    as_of: pd.Timestamp
    revenue_q: pd.Series
    gross_profit_q: pd.Series
    cogs_q: pd.Series
    inventory: pd.Series
    eps_q: pd.Series
    shares: pd.Series
    cash: pd.Series
    ocf_q: pd.Series

    @property
    def n_quarters(self) -> int:
        return int(len(self.revenue_q))

    @property
    def available(self) -> bool:
        return self.n_quarters >= 2

    def gross_margin_q(self) -> pd.Series:
        """Quarterly gross margin; derive GP = Revenue - COGS if GP not tagged."""
        gp = self.gross_profit_q
        if gp.empty and not self.revenue_q.empty and not self.cogs_q.empty:
            common = self.revenue_q.index.intersection(self.cogs_q.index)
            gp = (self.revenue_q[common] - self.cogs_q[common]).sort_index()
        if gp.empty:
            return pd.Series(dtype=float)
        common = gp.index.intersection(self.revenue_q.index)
        if len(common) == 0:
            return pd.Series(dtype=float)
        return (gp[common] / self.revenue_q[common]).sort_index()


def pit_fundamentals(ticker: str, T, cf: Optional[dict] = None) -> Fundamentals:
    cf = cf if cf is not None else edgar.companyfacts(ticker)
    T = pd.Timestamp(T)
    shares = _merged_series(cf, SHARES_CONCEPTS, T, "instant", ("shares",))
    if shares.empty:
        shares = _merged_series(cf, SHARES_DEI, T, "instant", ("shares",), taxonomy="dei")
    return Fundamentals(
        ticker=ticker,
        as_of=T,
        revenue_q=_merged_series(cf, REVENUE_CONCEPTS, T, "duration", ("USD",)),
        gross_profit_q=_merged_series(cf, GROSS_PROFIT_CONCEPTS, T, "duration", ("USD",)),
        cogs_q=_merged_series(cf, COGS_CONCEPTS, T, "duration", ("USD",)),
        inventory=_merged_series(cf, INVENTORY_CONCEPTS, T, "instant", ("USD",)),
        eps_q=_merged_series(cf, EPS_CONCEPTS, T, "duration", ("USD/shares",)),
        shares=shares,
        cash=_merged_series(cf, CASH_CONCEPTS, T, "instant", ("USD",)),
        ocf_q=_merged_series(cf, OCF_CONCEPTS, T, "duration", ("USD",)),
    )
