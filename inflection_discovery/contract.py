"""Candidate contract — the normalized record every engine emits.

Both Implementation A (LLM) and Implementation B (code) emit this identical
shape so they are comparable and either can feed `analyzing-stocks`. Ranking is
by ``D`` among names that pass the A gate and clear the trap_risk ceiling;
``composite`` is a transparency scalar only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

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
    return errs


def make_routing(ticker: str, exchange: str = "", currency: str = "USD") -> Dict[str, str]:
    """Pre-fill the controller's required Step-1/Step-2 fields. Every candidate
    is by construction a turnaround/special-situation, so style is set."""
    return {
        "exchange": exchange,
        "currency": currency,
        "tradable_line": ticker,
        "suggested_style": "turnaround",
    }
