"""pit_universe — the candidate pool at T and the data-availability gate.

For the executed backtest the universe is the benchmark names plus a random
control sample of depressed-base names (an unbiased forward-return denominator).
A full historical-filer universe is a production concern; this probe pool is
sufficient and documented as such.

Survivorship caveat: the SEC ticker map is current, so the random control arm
cannot include names that delisted before today. The benchmark's curated
delisted negatives (BBBY, FFAI) exercise the survivorship canary instead.
"""
from __future__ import annotations

import random
from typing import List, Sequence

from .. import edgar
from .fundamentals import pit_fundamentals
from .prices import pit_prices


def all_tickers() -> List[str]:
    return list(edgar._load_ticker_map().keys())


def random_control_tickers(n: int, seed: int = 42, exclude: Sequence[str] = ()) -> List[str]:
    pool = [t for t in all_tickers() if t not in set(exclude)]
    rnd = random.Random(seed)
    rnd.shuffle(pool)
    return pool[:n]


def data_available(ticker: str, T, min_price_rows: int = 60) -> bool:
    """True iff a name has reconstructable PIT prices and fundamentals at T.

    Non-operating tickers (ETFs/funds) fail the fundamentals check naturally
    (no us-gaap facts), which keeps the control arm to operating companies.
    """
    p = pit_prices(ticker, T)
    if p is None or p.empty or len(p) < min_price_rows:
        return False
    f = pit_fundamentals(ticker, T)
    return f.available
