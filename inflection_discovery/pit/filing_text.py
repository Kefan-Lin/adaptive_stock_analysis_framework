"""pit_filing_text — as-of-T filing metadata and document text (resolves the
text half of MF6 that companyfacts cannot cover: dimension C + backlog).

Uses the EDGAR submissions API to list filings with ``filingDate <= T`` and, on
demand, fetches the primary document and strips it to plain text. Only the most
recent filings <= T are fetched to bound cost.

Limitation: the submissions ``recent`` block holds ~1000 most-recent filings;
very long filing histories would need the paginated overflow files. For the
2016-2025 benchmark windows this is sufficient (noted in the spec).
"""
from __future__ import annotations

import hashlib
from typing import List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .. import edgar
from ..config import CACHE_DIR, HTTP_TIMEOUT, SEC_USER_AGENT


def recent_filings(
    ticker: str,
    T,
    forms=("10-K", "10-Q", "8-K"),
    limit: Optional[int] = None,
) -> List[dict]:
    sub = edgar.submissions(ticker)
    if not sub:
        return []
    cik = edgar.cik_for(ticker)
    rec = sub.get("filings", {}).get("recent", {})
    T = pd.Timestamp(T)
    forms_set = set(forms)
    fdates = rec.get("filingDate", [])
    fforms = rec.get("form", [])
    accs = rec.get("accessionNumber", [])
    docs = rec.get("primaryDocument", [])
    rdates = rec.get("reportDate", [])
    out: List[dict] = []
    for i in range(len(fdates)):
        if fforms[i] not in forms_set:
            continue
        if pd.Timestamp(fdates[i]) > T:
            continue
        out.append(
            {
                "form": fforms[i],
                "filed": fdates[i],
                "accession": accs[i],
                "primary_doc": docs[i] if i < len(docs) else "",
                "report_date": rdates[i] if i < len(rdates) else "",
                "cik": cik,
            }
        )
    out.sort(key=lambda r: r["filed"], reverse=True)
    return out[:limit] if limit else out


def fetch_filing_text(filing: dict, max_chars: int = 400_000) -> str:
    if not filing.get("primary_doc") or not filing.get("cik"):
        return ""
    cik = str(int(filing["cik"]))
    acc = filing["accession"].replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{filing['primary_doc']}"
    cache = CACHE_DIR / f"filingtext_{hashlib.sha1(url.encode()).hexdigest()[:16]}.txt"
    if cache.exists():
        return cache.read_text()[:max_chars]
    try:
        edgar._throttle()
        r = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.content, "lxml")
        text = soup.get_text(" ", strip=True)
        cache.write_text(text)
        return text[:max_chars]
    except Exception:
        return ""


def latest_filing_text(
    ticker: str, T, forms=("10-K", "10-Q"), limit: int = 1
) -> str:
    """Concatenated plain text of the latest ``limit`` filings <= T."""
    filings = recent_filings(ticker, T, forms, limit=limit)
    return "\n".join(fetch_filing_text(f) for f in filings)
