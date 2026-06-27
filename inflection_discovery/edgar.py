"""SEC EDGAR client: CIK lookup, companyfacts, submissions.

Polite by construction: descriptive User-Agent, rate limiting, on-disk cache,
and retries with backoff. All callers go through `get_json`.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Optional

import requests

from .config import (
    CACHE_DIR,
    HTTP_RETRIES,
    HTTP_TIMEOUT,
    SEC_MIN_INTERVAL,
    SEC_USER_AGENT,
)

_lock = threading.Lock()
_last_call = [0.0]


def _throttle() -> None:
    with _lock:
        dt = time.time() - _last_call[0]
        if dt < SEC_MIN_INTERVAL:
            time.sleep(SEC_MIN_INTERVAL - dt)
        _last_call[0] = time.time()


def _cache_path(url: str) -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    tail = url.split("//", 1)[-1].replace("/", "_").replace("?", "_")[:80]
    return CACHE_DIR / f"{tail}.{h}.json"


def get_json(url: str, use_cache: bool = True) -> Any:
    """GET a JSON document with cache, rate limit, and retries."""
    cp = _cache_path(url)
    if use_cache and cp.exists():
        return json.loads(cp.read_text())
    last_err: Optional[str] = None
    for attempt in range(HTTP_RETRIES):
        try:
            _throttle()
            r = requests.get(
                url,
                headers={
                    "User-Agent": SEC_USER_AGENT,
                    "Accept-Encoding": "gzip, deflate",
                },
                timeout=HTTP_TIMEOUT,
            )
            if r.status_code == 200:
                data = r.json()
                cp.write_text(json.dumps(data))
                return data
            if r.status_code in (403, 429) or r.status_code >= 500:
                last_err = f"HTTP {r.status_code}"
                time.sleep(1.0 * (attempt + 1))
                continue
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001 - retry on any transport error
            last_err = str(e)
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"SEC fetch failed for {url}: {last_err}")


_TICKER_MAP: Optional[dict] = None


def _load_ticker_map() -> dict:
    global _TICKER_MAP
    if _TICKER_MAP is None:
        data = get_json("https://www.sec.gov/files/company_tickers.json")
        m: dict = {}
        # data is {"0": {"cik_str":..., "ticker":..., "title":...}, ...}
        for row in data.values():
            m[str(row["ticker"]).upper()] = str(row["cik_str"]).zfill(10)
        _TICKER_MAP = m
    return _TICKER_MAP


def cik_for(ticker: str) -> Optional[str]:
    """Return 10-digit zero-padded CIK for a ticker, or None if unknown.

    Note: the SEC ticker map reflects *current* listings, so delisted names
    (BBBY, FFAI history) may be absent — callers must treat None as a
    data-availability signal, not an error.
    """
    return _load_ticker_map().get(ticker.upper())


_CF_MEMO: dict = {}
_SUB_MEMO: dict = {}


def companyfacts(ticker: str) -> Optional[dict]:
    key = ticker.upper()
    if key in _CF_MEMO:
        return _CF_MEMO[key]
    cik = cik_for(ticker)
    res = None
    if cik:
        try:
            res = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        except RuntimeError:
            res = None
    _CF_MEMO[key] = res
    return res


def submissions(ticker: str) -> Optional[dict]:
    key = ticker.upper()
    if key in _SUB_MEMO:
        return _SUB_MEMO[key]
    cik = cik_for(ticker)
    res = None
    if cik:
        try:
            res = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        except RuntimeError:
            res = None
    _SUB_MEMO[key] = res
    return res
