"""Offline guards for the SEC EDGAR client. No network is performed: the
placeholder-UA guard must fire before any request, and a cache hit must be
served without touching the UA guard or the network at all.
"""
import json

import pytest

from inflection_discovery import edgar


def test_placeholder_user_agent_blocks_live_request(monkeypatch):
    """The default UA carries the contact@example.com placeholder, which the SEC
    throttles. A live fetch must raise before any network I/O so the operator is
    forced to set a real contact UA."""
    monkeypatch.setattr(edgar, "SEC_USER_AGENT", "inflection-discovery-research contact@example.com")

    def no_network(*args, **kwargs):
        raise AssertionError("network must not be reached with a placeholder UA")

    monkeypatch.setattr(edgar.requests, "get", no_network)

    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        edgar.get_json("https://data.sec.gov/does-not-exist-offline-guard.json", use_cache=False)


def test_cache_hit_bypasses_ua_guard(monkeypatch, tmp_path):
    """A cached payload must be served even with the placeholder UA and with no
    network — the guard applies only to the live-request branch."""
    monkeypatch.setattr(edgar, "SEC_USER_AGENT", "inflection-discovery-research contact@example.com")

    def no_network(*args, **kwargs):
        raise AssertionError("network must not be reached on a cache hit")

    monkeypatch.setattr(edgar.requests, "get", no_network)

    url = "https://data.sec.gov/cache-hit-offline-guard.json"
    cp = edgar._cache_path(url)
    cp.write_text(json.dumps({"ok": True}))
    try:
        assert edgar.get_json(url, use_cache=True) == {"ok": True}
    finally:
        cp.unlink(missing_ok=True)
