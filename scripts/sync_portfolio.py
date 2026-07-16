#!/usr/bin/env python3
"""P4 sync: merge an IBKR positions payload into the state home's portfolio.yaml.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-13-scheduled-monitoring-design.md

Deterministic core of the P4 scheduled-monitoring layer. The scheduled session
dumps the connector's get_account_positions JSON to a file; this script owns
every mapping and write decision (the LLM never edits portfolio.yaml by hand).
Merging is pinned to one account (--account); rows in other accounts are never
matched, updated, or closed. Absent rows are quarantined to suspected_closed:,
never deleted. Pure stdlib + PyYAML.

Exit codes: 0 clean run (with or without changes), 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("sync_portfolio.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse the decision-records vocabulary so the two never drift.
from validate_records import (  # noqa: E402
    SYMBOL_PATTERNS,
    as_date,
    is_canonical,
    is_number,
    resolve_home,
)


# ----------------------------- payload parsing -----------------------------

_MONTHS = {m: i + 1 for i, m in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}

_STOCK_RE = re.compile(r"^(?P<ticker>[A-Z0-9][A-Z0-9.\-]{0,9})(?: @(?P<exch>[A-Z]+))?$")
_OPTION_RE = re.compile(
    r"^(?P<u>[A-Z0-9][A-Z0-9.\-]{0,9}) "
    r"(?P<mon>[A-Z][a-z]{2})(?P<day>\d{1,2})'(?P<yy>\d{2}) "
    r"(?P<strike>\d+(?:\.\d+)?) "
    r"(?P<right>CALL|PUT)(?: @(?P<exch>[A-Z]+))?$")


def parse_description(desc: object) -> "dict | None":
    """Structure an IBKR contract_description, or None when unparseable."""
    if not isinstance(desc, str):
        return None
    match = _OPTION_RE.match(desc)
    if match:
        month = _MONTHS.get(match.group("mon"))
        if month is None:
            return None
        try:
            expiry = datetime.date(2000 + int(match.group("yy")), month,
                                   int(match.group("day")))
        except ValueError:
            return None
        return {"asset": "option", "underlying": match.group("u"),
                "expiry": expiry, "strike": float(match.group("strike")),
                "right": match.group("right"), "exchange": match.group("exch")}
    match = _STOCK_RE.match(desc)
    if match:
        return {"asset": "stock", "ticker": match.group("ticker"),
                "exchange": match.group("exch")}
    return None


def canonical_for(parsed: "dict | None", existing_symbols: "set[str]") -> "str | None":
    """Deterministic canonical symbol for a parsed stock description.

    Bare ticker -> US; @ASX -> .AX; @KRX -> adopt an existing row's .KS/.KQ
    suffix for the same 6-digit code (KOSPI/KOSDAQ is not inferable from the
    payload); @SEHK -> zero-padded .HK (assumed form — unverified until an HK
    row is observed live; see design §mapping). Anything else, or a result
    that is not canonical, -> None (caller emits needs_mapping).
    """
    if not parsed or parsed.get("asset") != "stock":
        return None
    ticker, exch = parsed["ticker"], parsed.get("exchange")
    candidate: "str | None" = None
    if exch is None:
        candidate = ticker
    elif exch == "ASX":
        candidate = f"{ticker}.AX"
    elif exch == "KRX":
        for suffix in (".KS", ".KQ"):
            if f"{ticker}{suffix}" in existing_symbols:
                candidate = f"{ticker}{suffix}"
                break
    elif exch == "SEHK":
        if ticker.isdigit():
            candidate = f"{ticker.zfill(4)}.HK"
    if candidate is not None and is_canonical(candidate):
        return candidate
    return None


def default_kind(right: str, qty: float) -> str:
    side = "long" if qty > 0 else "short"
    return f"{side}-{right.lower()}"
