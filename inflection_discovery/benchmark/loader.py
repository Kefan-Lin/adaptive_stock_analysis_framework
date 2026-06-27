"""Labeled benchmark loader.

Label unit is (ticker, as-of-date, label) — the same ticker can carry opposite
labels at different dates (INTC: negative 2022-2024, positive 2025). Positives
store ``t_star`` (the fundamentals-confirmed turn) and are evaluated as-of
``t_star - {6,3,1}`` months; non-positives store an explicit ``as_of``.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd

BENCH_CSV = Path(__file__).with_name("benchmark.csv")

LEADS_MONTHS = (6, 3, 1)
HIT_LEAD_MONTHS = 3  # the fixed scoring date for a positive's "hit" (review SC2)


@dataclass
class BenchmarkRow:
    ticker: str
    label: str  # positive | negative | control | borderline
    t_star: Optional[pd.Timestamp]
    as_of: Optional[pd.Timestamp]
    inflection_type: str
    notes: str

    def as_of_dates(self) -> List[pd.Timestamp]:
        if self.label == "positive" and self.t_star is not None:
            return [self.t_star - pd.DateOffset(months=m) for m in LEADS_MONTHS]
        if self.as_of is not None:
            return [self.as_of]
        return []

    def hit_date(self) -> Optional[pd.Timestamp]:
        """The single fixed as-of date used for the symmetric hit/trap count."""
        if self.label == "positive" and self.t_star is not None:
            return self.t_star - pd.DateOffset(months=HIT_LEAD_MONTHS)
        return self.as_of


def load_benchmark(path: Path = BENCH_CSV) -> List[BenchmarkRow]:
    rows: List[BenchmarkRow] = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(
                BenchmarkRow(
                    ticker=r["ticker"].strip(),
                    label=r["label"].strip(),
                    t_star=pd.Timestamp(r["t_star"]) if r.get("t_star") else None,
                    as_of=pd.Timestamp(r["as_of"]) if r.get("as_of") else None,
                    inflection_type=r.get("inflection_type", "").strip(),
                    notes=r.get("notes", "").strip(),
                )
            )
    return rows
