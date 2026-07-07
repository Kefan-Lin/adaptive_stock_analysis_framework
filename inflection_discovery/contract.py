"""Candidate contract — the normalized record every engine emits.

Both Implementation A (LLM) and Implementation B (code) emit this identical
shape so they are comparable and either can feed `analyzing-stocks`. Ranking is
by ``D`` among names that pass the A gate and clear the trap_risk ceiling;
``composite`` is a transparency scalar only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from .symbols import SYMBOL_PATTERNS, canonical_symbol

SCORE_KEYS = ("A", "B", "C", "trap_risk", "D")


@dataclass
class Candidate:
    ticker: str
    as_of_date: str
    passes_A_gate: bool
    scores: Dict[str, float]
    composite: float
    engine: str  # "A" | "B"
    rank: int = 0
    symbol: str = ""  # canonical decision-records identity, e.g. "600519.SH"
    market: str = ""  # SYMBOL_PATTERNS key for `symbol`, e.g. "CN"
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    routing: Dict[str, str] = field(default_factory=dict)
    thesis: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def validate(candidate: dict) -> List[str]:
    """Return a list of schema violations ([] means valid)."""
    errs: List[str] = []
    required = [
        "ticker",
        "as_of_date",
        "passes_A_gate",
        "scores",
        "composite",
        "engine",
    ]
    for key in required:
        if key not in candidate:
            errs.append(f"missing field: {key}")
    if "engine" in candidate and candidate["engine"] not in ("A", "B"):
        errs.append(f"engine must be 'A' or 'B', got {candidate['engine']!r}")
    if "scores" in candidate:
        scores = candidate["scores"]
        if not isinstance(scores, dict):
            errs.append("scores must be a dict")
        else:
            for k in SCORE_KEYS:
                if k not in scores:
                    errs.append(f"scores missing key: {k}")
                else:
                    v = scores[k]
                    if v is not None and not (isinstance(v, (int, float)) and 0.0 <= v <= 1.0):
                        errs.append(f"score {k} must be in [0,1] or None, got {v!r}")
    if "passes_A_gate" in candidate and not isinstance(candidate["passes_A_gate"], bool):
        errs.append("passes_A_gate must be bool")
    symbol = candidate.get("symbol") or ""
    if symbol:
        market = candidate.get("market") or ""
        if market not in SYMBOL_PATTERNS:
            errs.append(f"market must be one of {'/'.join(SYMBOL_PATTERNS)} when symbol set, got {market!r}")
        elif not SYMBOL_PATTERNS[market].match(symbol):
            errs.append(f"symbol {symbol!r} is not canonical for market {market}")
    return errs


def make_routing(ticker: str, exchange: str = "", currency: str = "USD") -> Dict[str, str]:
    """Pre-fill the controller's required Step-1/Step-2 fields. Every candidate
    is by construction a turnaround/special-situation, so style is set.

    Also bridges the provider code to its canonical decision-records identity
    (``symbol``/``market``). Canonicalization never crashes routing: on failure
    ``symbol``/``market`` are empty and the reason is recorded under
    ``canonicalization_error``.
    """
    routing = {
        "exchange": exchange,
        "currency": currency,
        "tradable_line": ticker,
        "suggested_style": "turnaround",
    }
    try:
        symbol, market = canonical_symbol(ticker, exchange=exchange)
        routing["symbol"] = symbol
        routing["market"] = market
    except ValueError as exc:
        routing["symbol"] = ""
        routing["market"] = ""
        routing["canonicalization_error"] = str(exc)
    return routing
