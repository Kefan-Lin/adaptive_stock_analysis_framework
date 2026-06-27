"""Shared configuration: cache location, SEC politeness, HTTP settings."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# On-disk cache for SEC payloads and (optionally) price frames. Gitignored.
CACHE_DIR = Path(os.environ.get("INFLECTION_CACHE", REPO_ROOT / ".cache_inflection"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# SEC fair-access policy requires a descriptive User-Agent with contact info
# and asks for <= 10 requests/second. Override via env for real use.
SEC_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", "inflection-discovery-research contact@example.com"
)
SEC_MIN_INTERVAL = float(os.environ.get("SEC_MIN_INTERVAL", "0.18"))  # ~5.5 req/s

HTTP_TIMEOUT = int(os.environ.get("INFLECTION_HTTP_TIMEOUT", "30"))
HTTP_RETRIES = int(os.environ.get("INFLECTION_HTTP_RETRIES", "3"))
