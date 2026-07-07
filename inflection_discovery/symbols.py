"""Canonical-symbol bridge (decision-records contract, spec §Canonical Symbol Form).

Providers speak bare codes (akshare: 600519); the framework's records layer
speaks canonical identities (600519.SH). SYMBOL_PATTERNS mirrors
scripts/validate_records.py verbatim; a contract test keeps them in lockstep.
"""
from __future__ import annotations

import re
from typing import Tuple

SYMBOL_PATTERNS = {
    "US": re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,2})?$"),
    "HK": re.compile(r"^\d{4,5}\.HK$"),
    "CN": re.compile(r"^\d{6}\.(SH|SZ|BJ)$"),
    "KR": re.compile(r"^\d{6}\.(KS|KQ)$"),
    "AU": re.compile(r"^[A-Z0-9]{1,6}\.AX$"),
}

_CN_SUFFIX = {"SSE": ".SH", "SZSE": ".SZ", "BSE": ".BJ"}


def canonical_symbol(code: str, exchange: str = "") -> Tuple[str, str]:
    """Return (canonical_symbol, market) for a provider code + exchange hint."""
    code = code.strip().upper()
    if exchange in _CN_SUFFIX and code.isdigit() and len(code) == 6:
        return code + _CN_SUFFIX[exchange], "CN"
    if exchange in ("HKEX", "SEHK") and code.isdigit():
        sym = code.zfill(4) + ".HK" if len(code) <= 4 else code + ".HK"
        return sym, "HK"
    for market, pattern in SYMBOL_PATTERNS.items():
        if pattern.match(code):
            return code, market
    raise ValueError(f"cannot canonicalize {code!r} (exchange={exchange!r})")
