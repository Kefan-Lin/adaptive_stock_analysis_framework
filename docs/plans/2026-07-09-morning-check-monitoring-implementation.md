# P1 Morning-Check Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manually-triggered "morning check" that sweeps the private state home, evaluates each name's price/date/assignment triggers against live prices, and emits an action brief.

**Architecture:** A deterministic `scripts/morning_check.py` (pure stdlib + PyYAML, reusing the `validate_records.py` loaders) computes structured findings; live prices arrive through an injectable `PriceSource` whose real implementation lazy-imports yfinance/akshare so the pyyaml-only CI job stays dependency-free. A new `skills/morning-check/SKILL.md` runs the script, layers LLM KPI/event judgment on top, handles the per-name price fallback, and assembles the brief.

**Tech Stack:** Python 3.9+, PyYAML, unittest (main CI job); yfinance + akshare (already in `pyproject.toml`, lazy-imported, exercised only in the network-gated `inflection-tests` job).

**Reference spec:** `docs/plans/2026-07-09-morning-check-monitoring-design.md`
**Contract consumed:** `skills/analyzing-stocks/references/decision-records.md`

---

## File structure

- Create: `scripts/morning_check.py` — the deterministic core + CLI + price sources.
- Create: `tests/test_morning_check.py` — unit tests (direct import) + CLI subprocess test.
- Create: `tests/fixtures/morning-check-home/` — a dedicated fixture state home (portfolio + records) so mutations never touch the shared `state-home` fixture.
- Create: `tests/fixtures/morning-check-quotes.yaml` — offline price snapshot for deterministic runs.
- Create: `skills/morning-check/SKILL.md` — the LLM wrapper skill.
- Create: `skills/morning-check/agents/openai.yaml` — per-skill OpenAI metadata (repo convention).
- Modify: `scripts/validate_repo.py` — register the new skill in `FULL_REQUIRED`.

All test paths are exercised in the main pyyaml-only CI job. The engineer runs commands from the repo root with the project venv:
`source .venv/bin/activate` (or prefix commands with `.venv/bin/`). If no venv, `python -m venv .venv && .venv/bin/pip install pyyaml`.

---

### Task 1: Test fixture state home + offline quote snapshot

**Files:**
- Create: `tests/fixtures/morning-check-home/portfolio.yaml`
- Create: `tests/fixtures/morning-check-home/records/ACME/2026-06-01-new-idea.md`
- Create: `tests/fixtures/morning-check-home/records/ACME/INDEX.md`
- Create: `tests/fixtures/morning-check-home/records/1234.HK/2026-07-02-research.md`
- Create: `tests/fixtures/morning-check-home/records/1234.HK/INDEX.md`
- Create: `tests/fixtures/morning-check-home/records/NVDA/2026-06-20-position-review.md`
- Create: `tests/fixtures/morning-check-home/records/NVDA/INDEX.md`
- Create: `tests/fixtures/morning-check-quotes.yaml`

The fixture is tuned for a fixed `--as-of 2026-07-09`: ACME trips a trim_exit and is stale + near earnings; 1234.HK has a null `next_earnings` (data gap); NVDA carries a short cash-secured put that is ITM, near expiry, with earnings before expiry.

- [ ] **Step 1: Create the portfolio**

`tests/fixtures/morning-check-home/portfolio.yaml`:

```yaml
schema: portfolio/v1
as_of: 2026-07-08
base_currency: USD
cash: {USD: 25000, HKD: 80000}
holdings:
  - {symbol: ACME, qty: 100, avg_cost: 150.0, currency: USD,
     opened: 2026-06-02, thesis_record: records/ACME/2026-06-01-new-idea.md}
  - {symbol: 1234.HK, qty: 2000, avg_cost: 470.0, currency: HKD,
     opened: 2026-05-02, thesis_record: records/1234.HK/2026-07-02-research.md}
option_legs:
  - {kind: cash-secured-put, underlying: NVDA, strike: 140, expiry: 2026-07-14,
     qty: -1, premium: 4.20, currency: USD, opened: 2026-06-20, multiplier: 100}
constraints:
  single_name_cap_pct: 10
  cash_reserve_floor_pct: 15
```

- [ ] **Step 2: Create the ACME record (fires a trigger, stale, near earnings)**

`tests/fixtures/morning-check-home/records/ACME/2026-06-01-new-idea.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-06-01
mode: new-idea
price_at_decision: 150.0
currency: USD
stance: Buy
position_size: Starter
confidence: Medium
weighted_fair_value: 175
scenarios: {bear: 80, base: 135, bull: 190}
candidate_tier: Core Candidate
valuation_zone: Accumulation
execution_method: Stage buy
triggers:
  add_on:
    - {type: price, level: 90, direction: below}
    - {type: kpi, text: "fictional bookings growth reaccelerates two quarters running"}
  trim_exit:
    - {type: price, level: 185, direction: above}
    - {type: event, text: "fictional regulator opens a formal antitrust probe"}
monitor:
  - {kpi: "fictional net revenue retention", threshold: "< 110%", action: "revisit Base scenario"}
next_earnings: 2026-07-12
review_by: 2026-07-01
source_report: null
action_taken: null
---

# ACME — new idea (fixture)

Fictional self-contained decision record for tests.
```

- [ ] **Step 3: Create the ACME INDEX**

`tests/fixtures/morning-check-home/records/ACME/INDEX.md`:

```markdown
# ACME — Decision Timeline

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-01 | new-idea | 150.0 USD | Buy | 175 | Stage buy | [record](2026-06-01-new-idea.md) | — |
```

- [ ] **Step 4: Create the 1234.HK record (null next_earnings → data gap)**

`tests/fixtures/morning-check-home/records/1234.HK/2026-07-02-research.md`:

```markdown
---
schema: decision-record/v1
symbol: 1234.HK
market: HK
date: 2026-07-02
mode: research
price_at_decision: 470.0
currency: HKD
stance: Hold
review_by: 2026-12-31
triggers:
  trim_exit:
    - {type: price, level: 500, direction: above}
next_earnings: null
source_report: null
action_taken: null
---

# 1234.HK — research (fixture)

Fictional standalone research record.
```

- [ ] **Step 5: Create the 1234.HK INDEX**

`tests/fixtures/morning-check-home/records/1234.HK/INDEX.md`:

```markdown
# 1234.HK — Decision Timeline

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-02 | research | 470.0 HKD | Hold | — | — | [record](2026-07-02-research.md) | — |
```

- [ ] **Step 6: Create the NVDA record (earnings before the put expiry)**

`tests/fixtures/morning-check-home/records/NVDA/2026-06-20-position-review.md`:

```markdown
---
schema: decision-record/v1
symbol: NVDA
market: US
date: 2026-06-20
mode: position-review
price_at_decision: 145.0
currency: USD
stance: Hold
position_size: Core
confidence: Medium
weighted_fair_value: 160
scenarios: {bear: 100, base: 155, bull: 210}
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: Sell cash-secured put
triggers:
  add_on:
    - {type: price, level: 120, direction: below}
next_earnings: 2026-07-11
review_by: 2026-09-30
source_report: null
action_taken: null
---

# NVDA — position review (fixture)

Fictional self-contained decision record for tests.
```

- [ ] **Step 7: Create the NVDA INDEX**

`tests/fixtures/morning-check-home/records/NVDA/INDEX.md`:

```markdown
# NVDA — Decision Timeline

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-20 | position-review | 145.0 USD | Hold | 160 | Sell cash-secured put | [record](2026-06-20-position-review.md) | — |
```

- [ ] **Step 8: Create the offline quote snapshot**

`tests/fixtures/morning-check-quotes.yaml`:

```yaml
# Fictional quotes for deterministic offline runs (--as-of 2026-07-09).
ACME: 189.20
1234.HK: 480.0
NVDA: 138.10
```

- [ ] **Step 9: Confirm the fixture validates against the P0 contract**

Run: `python scripts/validate_records.py --home tests/fixtures/morning-check-home`
Expected: `State-home validation passed: tests/fixtures/morning-check-home` (exit 0). If it fails, fix the fixture to satisfy the decision-records contract before proceeding.

- [ ] **Step 10: Commit**

```bash
git add tests/fixtures/morning-check-home tests/fixtures/morning-check-quotes.yaml
git commit -m "test: add morning-check fixture state home and quote snapshot"
```

---

### Task 2: Module skeleton, price sources, and provider mapping

**Files:**
- Create: `scripts/morning_check.py`
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

`tests/test_morning_check.py`:

```python
import datetime
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import morning_check as mc  # noqa: E402
import validate_records as vr  # noqa: E402


class ProviderMappingTests(unittest.TestCase):
    def test_us_symbol_passes_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("NVDA"), ("yfinance", "NVDA"))

    def test_hk_symbol_passes_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("0700.HK"), ("yfinance", "0700.HK"))

    def test_cn_symbol_routes_to_akshare_bare_code(self):
        self.assertEqual(mc.provider_for("600519.SH"), ("akshare", "600519"))
        self.assertEqual(mc.provider_for("300750.SZ"), ("akshare", "300750"))

    def test_kr_and_au_pass_through_to_yfinance(self):
        self.assertEqual(mc.provider_for("000660.KS"), ("yfinance", "000660.KS"))
        self.assertEqual(mc.provider_for("BC8.AX"), ("yfinance", "BC8.AX"))

    def test_symbol_patterns_are_the_validate_records_object(self):
        # Identity, not a copy: guarantees the two vocabularies cannot drift.
        self.assertIs(mc.SYMBOL_PATTERNS, vr.SYMBOL_PATTERNS)


class FilePriceSourceTests(unittest.TestCase):
    def test_returns_price_when_present_and_none_when_absent(self):
        src = mc.FilePriceSource({"ACME": 189.20})
        self.assertEqual(src.spot("ACME"), 189.20)
        self.assertIsNone(src.spot("MISSING"))

    def test_chain_falls_through_to_second_source(self):
        chain = mc.ChainSource(mc.FilePriceSource({"ACME": 1.0}), mc.FilePriceSource({"NVDA": 2.0}))
        self.assertEqual(chain.spot("ACME"), 1.0)
        self.assertEqual(chain.spot("NVDA"), 2.0)
        self.assertIsNone(chain.spot("MISSING"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'morning_check'`.

- [ ] **Step 3: Write the module skeleton**

`scripts/morning_check.py`:

```python
#!/usr/bin/env python3
"""P1 morning-check: sweep the state home and emit an action brief.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-09-morning-check-monitoring-design.md

The deterministic core (this script) checks price triggers, drawdown vs
scenarios, review_by expiry, next_earnings proximity, and cash-secured-put
assignment risk. The morning-check skill layers LLM KPI/event judgment on top.
Live price fetching (yfinance/akshare) is lazily imported so the pyyaml-only
test job stays dependency-free.

Exit codes: 0 clean run, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("morning_check.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse the decision-records loaders and symbol vocabulary so the two never drift.
from validate_records import (  # noqa: E402
    FRONTMATTER,
    MODE_PRIORITY,
    SYMBOL_PATTERNS,
    as_date,
    is_number,
    resolve_home,
)


# ----------------------------- price sources -----------------------------

def provider_for(symbol: str) -> "tuple[str, str]":
    """Map a canonical symbol to (provider, provider_symbol).

    CN A-shares (`600519.SH`) go to akshare as the bare 6-digit code; every
    other market passes through to yfinance unchanged.
    """
    if SYMBOL_PATTERNS["CN"].match(symbol):
        return "akshare", symbol.split(".")[0]
    return "yfinance", symbol


class FilePriceSource:
    """Spot prices from an in-memory {canonical_symbol: price} mapping.

    Backs both the owner-provided-quote fallback and offline tests.
    """

    def __init__(self, prices: dict) -> None:
        self._prices = {str(k): v for k, v in (prices or {}).items()}

    def spot(self, symbol: str) -> "float | None":
        value = self._prices.get(symbol)
        return float(value) if is_number(value) else None


class ChainSource:
    """Try `first`, then `second`; the first non-None spot wins."""

    def __init__(self, first, second) -> None:
        self._first = first
        self._second = second

    def spot(self, symbol: str) -> "float | None":
        value = self._first.spot(symbol)
        return value if value is not None else self._second.spot(symbol)


class LivePriceSource:
    """Live quotes via yfinance (US/HK/KR/AU) and akshare (CN A-shares).

    Heavy providers are imported lazily inside the fetch so merely importing
    this module never requires them. Any per-name failure returns None (the
    caller records a data gap) rather than raising.
    """

    def spot(self, symbol: str) -> "float | None":
        provider, provider_symbol = provider_for(symbol)
        try:
            if provider == "akshare":
                return self._akshare_spot(provider_symbol)
            return self._yfinance_spot(provider_symbol)
        except Exception:
            return None

    @staticmethod
    def _yfinance_spot(provider_symbol: str) -> "float | None":
        import yfinance as yf

        ticker = yf.Ticker(provider_symbol)
        try:
            last = ticker.fast_info.get("last_price")
            if is_number(last) and last > 0:
                return float(last)
        except Exception:
            pass
        hist = ticker.history(period="5d")
        if hist is not None and not hist.empty and "Close" in hist:
            closes = hist["Close"].dropna()
            if len(closes):
                return float(closes.iloc[-1])
        return None

    @staticmethod
    def _akshare_spot(provider_symbol: str) -> "float | None":
        import akshare as ak

        df = ak.stock_zh_a_hist(symbol=provider_symbol, period="daily", adjust="")
        if df is not None and len(df) and "收盘" in df:
            return float(df.iloc[-1]["收盘"])
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_morning_check -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/morning_check.py tests/test_morning_check.py
git commit -m "feat: morning_check price sources and canonical->provider mapping"
```

---

### Task 3: State loading — portfolio, latest records, universe

**Files:**
- Modify: `scripts/morning_check.py`
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_morning_check.py`:

```python
FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "morning-check-home"


class StateLoadingTests(unittest.TestCase):
    def test_loads_portfolio(self):
        portfolio = mc.load_portfolio(FIXTURE_HOME)
        self.assertEqual(portfolio["schema"], "portfolio/v1")
        self.assertEqual(len(portfolio["holdings"]), 2)

    def test_missing_portfolio_returns_empty_dict(self, ):
        portfolio = mc.load_portfolio(REPO_ROOT / "tests" / "fixtures")
        self.assertEqual(portfolio, {})

    def test_latest_record_per_symbol(self):
        latest = mc.load_latest_records(FIXTURE_HOME)
        self.assertEqual(set(latest), {"ACME", "1234.HK", "NVDA"})
        self.assertEqual(latest["ACME"]["mode"], "new-idea")

    def test_universe_is_union_of_holdings_options_and_records(self):
        portfolio = mc.load_portfolio(FIXTURE_HOME)
        latest = mc.load_latest_records(FIXTURE_HOME)
        universe = mc.build_universe(portfolio, latest)
        self.assertEqual(universe, {"ACME", "1234.HK", "NVDA"})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check.StateLoadingTests -v`
Expected: FAIL — `AttributeError: module 'morning_check' has no attribute 'load_portfolio'`.

- [ ] **Step 3: Implement the loaders**

Append to `scripts/morning_check.py`:

```python
# ----------------------------- state loading -----------------------------

def load_frontmatter(path: Path) -> "dict | None":
    """Parse a record's YAML frontmatter (tolerant; None if unparseable)."""
    text = path.read_text(encoding="utf-8-sig")
    match = FRONTMATTER.match(text)
    if not match:
        return None
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return meta if isinstance(meta, dict) else None


def load_portfolio(home: Path) -> dict:
    """Return the parsed portfolio.yaml, or {} when absent/unreadable."""
    path = home / "portfolio.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _latest_key(meta: dict) -> "tuple[datetime.date, int]":
    """Sort key for 'most current' record: newest date, then P0 mode priority."""
    try:
        date = as_date(meta.get("date"))
    except (ValueError, TypeError):
        date = datetime.date.min
    priority = MODE_PRIORITY.get(meta.get("mode"), 99)
    return (date, -priority)  # max() picks newest date, then lowest priority number


def load_latest_records(home: Path) -> "dict[str, dict]":
    """The latest decision record per symbol (P0 (date, mode) tie-break)."""
    latest: "dict[str, dict]" = {}
    records_root = home / "records"
    if not records_root.exists():
        return latest
    for symbol_dir in sorted(p for p in records_root.iterdir() if p.is_dir()):
        best: "dict | None" = None
        for record_path in sorted(symbol_dir.glob("*.md")):
            if record_path.name == "INDEX.md":
                continue
            meta = load_frontmatter(record_path)
            if meta is None:
                continue
            if best is None or _latest_key(meta) > _latest_key(best):
                best = meta
        if best is not None:
            latest[symbol_dir.name] = best
    return latest


def build_universe(portfolio: dict, latest: "dict[str, dict]") -> "set[str]":
    """Holdings ∪ option underlyings ∪ symbols with a current record."""
    universe: "set[str]" = set(latest)
    for holding in portfolio.get("holdings") or []:
        symbol = holding.get("symbol")
        if symbol:
            universe.add(str(symbol))
    for leg in portfolio.get("option_legs") or []:
        underlying = leg.get("underlying")
        if underlying:
            universe.add(str(underlying))
    return universe
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_morning_check.StateLoadingTests -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/morning_check.py tests/test_morning_check.py
git commit -m "feat: morning_check state loading (portfolio, latest records, universe)"
```

---

### Task 4: Equity checks — price triggers, drawdown, review_by, next_earnings

**Files:**
- Modify: `scripts/morning_check.py`
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_morning_check.py`:

```python
AS_OF = datetime.date(2026, 7, 9)


def _evaluate(prices=None, as_of=AS_OF):
    src = mc.FilePriceSource(prices if prices is not None else {
        "ACME": 189.20, "1234.HK": 480.0, "NVDA": 138.10,
    })
    return mc.evaluate_state(FIXTURE_HOME, src, as_of)


def _findings(result, symbol=None, kind=None):
    out = result["findings"]
    if symbol is not None:
        out = [f for f in out if f["symbol"] == symbol]
    if kind is not None:
        out = [f for f in out if f["kind"] == kind]
    return out


class EquityCheckTests(unittest.TestCase):
    def test_trim_exit_price_trigger_fires_act(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "price_trigger")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "act")
        self.assertEqual(hits[0]["evidence"]["level"], 185)

    def test_add_on_price_trigger_does_not_fire_above_level(self):
        # ACME add_on is 'below 90'; spot 189.20 must not trip it.
        result = _evaluate()
        levels = [f["evidence"]["level"] for f in _findings(result, "ACME", "price_trigger")]
        self.assertNotIn(90, levels)

    def test_add_on_price_trigger_fires_when_spot_below(self):
        result = _evaluate(prices={"ACME": 85.0, "1234.HK": 480.0, "NVDA": 138.10})
        levels = [f["evidence"]["level"] for f in _findings(result, "ACME", "price_trigger")]
        self.assertIn(90, levels)

    def test_review_by_passed_is_review(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "review_expiry")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "review")

    def test_review_by_far_out_produces_no_finding(self):
        result = _evaluate()
        self.assertEqual(_findings(result, "1234.HK", "review_expiry"), [])

    def test_next_earnings_soon_is_watch(self):
        result = _evaluate()
        hits = _findings(result, "ACME", "earnings_proximity")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "watch")

    def test_null_next_earnings_is_a_data_gap(self):
        result = _evaluate()
        reasons = [g for g in result["data_gaps"] if g["symbol"] == "1234.HK"]
        self.assertTrue(any("earnings date unknown" in g["reason"] for g in reasons))

    def test_missing_price_becomes_data_gap(self):
        result = _evaluate(prices={"1234.HK": 480.0, "NVDA": 138.10})  # ACME absent
        self.assertTrue(any(g["symbol"] == "ACME" for g in result["data_gaps"]))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check.EquityCheckTests -v`
Expected: FAIL — `AttributeError: module 'morning_check' has no attribute 'evaluate_state'`.

- [ ] **Step 3: Implement the equity checks and the evaluate_state entry point**

Append to `scripts/morning_check.py`:

```python
# ----------------------------- checks -----------------------------

def _finding(symbol, kind, urgency, detail, evidence):
    return {"symbol": symbol, "kind": kind, "urgency": urgency,
            "detail": detail, "evidence": evidence}


def _price_trigger_findings(symbol, meta, spot):
    out = []
    triggers = meta.get("triggers") or {}
    for group in ("add_on", "trim_exit"):
        for item in triggers.get(group) or []:
            if not isinstance(item, dict) or item.get("type") != "price":
                continue
            level, direction = item.get("level"), item.get("direction")
            if not is_number(level) or direction not in ("above", "below"):
                continue
            fired = (direction == "above" and spot >= level) or \
                    (direction == "below" and spot <= level)
            if fired:
                out.append(_finding(
                    symbol, "price_trigger", "act",
                    f"{group} level {level} crossed (spot {spot} {direction})",
                    {"group": group, "level": level, "direction": direction, "spot": spot},
                ))
    return out


def _drawdown_findings(symbol, meta, spot):
    scenarios = meta.get("scenarios")
    if not isinstance(scenarios, dict) or not is_number(scenarios.get("bear")):
        return []
    if spot < scenarios["bear"]:
        return [_finding(
            symbol, "drawdown", "review",
            f"spot {spot} below bear scenario {scenarios['bear']}",
            {"spot": spot, "bear": scenarios["bear"]},
        )]
    return []


def _review_findings(symbol, meta, as_of, review_window):
    value = meta.get("review_by")
    if value is None:
        return []
    try:
        review_by = as_date(value)
    except (ValueError, TypeError):
        return []
    if review_by < as_of:
        return [_finding(
            symbol, "review_expiry", "review",
            f"review_by {review_by.isoformat()} passed ({(as_of - review_by).days}d ago)",
            {"review_by": review_by.isoformat()},
        )]
    if (review_by - as_of).days <= review_window:
        return [_finding(
            symbol, "review_expiry", "watch",
            f"review_by {review_by.isoformat()} in {(review_by - as_of).days}d",
            {"review_by": review_by.isoformat()},
        )]
    return []


def _earnings_findings(symbol, meta, as_of, earnings_window):
    value = meta.get("next_earnings")
    if value is None:
        return [], [{"symbol": symbol, "reason": "earnings date unknown — verify"}]
    try:
        earnings = as_date(value)
    except (ValueError, TypeError):
        return [], [{"symbol": symbol, "reason": f"next_earnings not a date: {value!r}"}]
    if earnings < as_of:
        return [], []  # stale earnings date is a review_by concern, not an alert
    if (earnings - as_of).days <= earnings_window:
        return [_finding(
            symbol, "earnings_proximity", "watch",
            f"earnings in {(earnings - as_of).days}d ({earnings.isoformat()})",
            {"next_earnings": earnings.isoformat()},
        )], []
    return [], []


def _llm_todo(symbol, meta):
    out = []
    triggers = meta.get("triggers") or {}
    for group in ("add_on", "trim_exit"):
        for item in triggers.get(group) or []:
            if isinstance(item, dict) and item.get("type") in ("kpi", "event"):
                out.append({"symbol": symbol, "type": item["type"],
                            "text": item.get("text"), "trigger_group": group})
    for item in meta.get("monitor") or []:
        if isinstance(item, dict):
            out.append({"symbol": symbol, "type": "monitor", "kpi": item.get("kpi"),
                        "threshold": item.get("threshold"), "action": item.get("action")})
    return out


def evaluate_state(home, price_source, as_of, *, earnings_window=7, review_window=14,
                   assignment_watch_pct=0.03, dte_window=7) -> dict:
    portfolio = load_portfolio(home)
    latest = load_latest_records(home)
    findings: list = []
    data_gaps: list = []
    llm_todo: list = []

    for symbol in sorted(latest):
        meta = latest[symbol]
        llm_todo.extend(_llm_todo(symbol, meta))
        spot = price_source.spot(symbol)
        if spot is None:
            data_gaps.append({"symbol": symbol, "reason": "price fetch failed / unavailable"})
        else:
            findings.extend(_price_trigger_findings(symbol, meta, spot))
            findings.extend(_drawdown_findings(symbol, meta, spot))
        findings.extend(_review_findings(symbol, meta, as_of, review_window))
        earn_findings, earn_gaps = _earnings_findings(symbol, meta, as_of, earnings_window)
        findings.extend(earn_findings)
        data_gaps.extend(earn_gaps)

    findings.extend(_option_findings(portfolio, latest, price_source, as_of,
                                     assignment_watch_pct, dte_window, data_gaps))

    order = {"act": 0, "review": 1, "watch": 2}
    findings.sort(key=lambda f: (order.get(f["urgency"], 9), f["symbol"], f["kind"]))
    return {"as_of": as_of.isoformat(), "findings": findings,
            "data_gaps": data_gaps, "llm_todo": llm_todo}
```

Note: `_option_findings` is defined in Task 5; add a temporary stub now so this task's tests run, then replace it in Task 5.

Add this stub near the other check functions (it will be replaced in Task 5):

```python
def _option_findings(portfolio, latest, price_source, as_of,
                     assignment_watch_pct, dte_window, data_gaps):
    return []  # replaced in Task 5
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_morning_check.EquityCheckTests -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/morning_check.py tests/test_morning_check.py
git commit -m "feat: morning_check equity checks (triggers, drawdown, review, earnings)"
```

---

### Task 5: Cash-secured-put assignment-risk check

**Files:**
- Modify: `scripts/morning_check.py` (replace the `_option_findings` stub)
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_morning_check.py`:

```python
class OptionAssignmentTests(unittest.TestCase):
    def test_itm_near_expiry_put_with_earnings_before_expiry_is_act(self):
        result = _evaluate()
        hits = _findings(result, "NVDA", "options_assignment")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["urgency"], "act")
        ev = hits[0]["evidence"]
        self.assertEqual(ev["strike"], 140)
        self.assertEqual(ev["reserve"], 14000.0)  # 140 * 100 * 1
        self.assertTrue(ev["in_the_money"])
        self.assertTrue(ev["earnings_before_expiry"])

    def test_far_otm_put_produces_no_finding(self):
        # Spot well above strike, far from expiry window is still within DTE here,
        # so move as_of earlier to clear the DTE window and lift spot far OTM.
        result = _evaluate(prices={"ACME": 150.0, "1234.HK": 480.0, "NVDA": 300.0},
                           as_of=datetime.date(2026, 6, 25))
        self.assertEqual(_findings(result, "NVDA", "options_assignment"), [])

    def test_missing_underlying_price_is_data_gap(self):
        result = _evaluate(prices={"ACME": 189.20, "1234.HK": 480.0})  # NVDA absent
        # NVDA already gaps on its equity price; the option check must not crash.
        self.assertTrue(any(g["symbol"] == "NVDA" for g in result["data_gaps"]))
        self.assertEqual(_findings(result, "NVDA", "options_assignment"), [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check.OptionAssignmentTests -v`
Expected: FAIL — `AssertionError` (stub returns no option findings).

- [ ] **Step 3: Replace the stub with the real implementation**

In `scripts/morning_check.py`, replace the `_option_findings` stub with:

```python
def _option_findings(portfolio, latest, price_source, as_of,
                     assignment_watch_pct, dte_window, data_gaps):
    out = []
    seen_gap = {g["symbol"] for g in data_gaps}
    for leg in portfolio.get("option_legs") or []:
        if not isinstance(leg, dict) or leg.get("kind") != "cash-secured-put":
            continue
        qty = leg.get("qty")
        if not is_number(qty) or qty >= 0:
            continue  # only short puts carry assignment risk
        underlying = leg.get("underlying")
        strike = leg.get("strike")
        if not underlying or not is_number(strike):
            continue
        try:
            expiry = as_date(leg.get("expiry"))
        except (ValueError, TypeError):
            continue
        dte = (expiry - as_of).days
        if dte < 0:
            continue  # expired leg; stale portfolio, not a live alert
        spot = price_source.spot(underlying)
        if spot is None:
            if underlying not in seen_gap:
                data_gaps.append({"symbol": underlying,
                                  "reason": "option underlying price unavailable"})
            continue
        multiplier = leg.get("multiplier") if is_number(leg.get("multiplier")) else 100
        reserve = float(strike) * float(multiplier) * abs(qty)
        in_the_money = spot <= strike
        near_strike = spot <= strike * (1 + assignment_watch_pct)
        near_expiry = dte <= dte_window
        earnings_before_expiry = False
        under_meta = latest.get(underlying)
        if under_meta and under_meta.get("next_earnings") is not None:
            try:
                earnings_before_expiry = as_date(under_meta["next_earnings"]) <= expiry
            except (ValueError, TypeError):
                earnings_before_expiry = False
        if not (in_the_money or near_strike or near_expiry or earnings_before_expiry):
            continue
        urgency = "act" if (in_the_money and near_expiry) else "watch"
        out.append(_finding(
            underlying, "options_assignment", urgency,
            f"cash-secured put {strike} (exp {expiry.isoformat()}): "
            f"spot {spot}, {dte} DTE, reserve {reserve:g}",
            {"strike": strike, "expiry": expiry.isoformat(), "dte": dte, "spot": spot,
             "reserve": reserve, "in_the_money": in_the_money, "near_strike": near_strike,
             "near_expiry": near_expiry, "earnings_before_expiry": earnings_before_expiry},
        ))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_morning_check.OptionAssignmentTests tests.test_morning_check.EquityCheckTests -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/morning_check.py tests/test_morning_check.py
git commit -m "feat: morning_check cash-secured-put assignment-risk check"
```

---

### Task 6: CLI, rendering, and offline end-to-end test

**Files:**
- Modify: `scripts/morning_check.py` (CLI + markdown renderer + `main`)
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_morning_check.py`:

```python
import json  # noqa: E402
import subprocess  # noqa: E402

SCRIPT = REPO_ROOT / "scripts" / "morning_check.py"
QUOTES = REPO_ROOT / "tests" / "fixtures" / "morning-check-quotes.yaml"


class CliTests(unittest.TestCase):
    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "2026-07-09", "--offline", "--prices", str(QUOTES), *extra],
            capture_output=True, text=True,
        )

    def test_json_output_has_expected_findings(self):
        result = self._run("--format", "json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2026-07-09")
        kinds = {(f["symbol"], f["kind"]) for f in payload["findings"]}
        self.assertIn(("ACME", "price_trigger"), kinds)
        self.assertIn(("ACME", "review_expiry"), kinds)
        self.assertIn(("ACME", "earnings_proximity"), kinds)
        self.assertIn(("NVDA", "options_assignment"), kinds)
        self.assertTrue(any(g["symbol"] == "1234.HK" for g in payload["data_gaps"]))

    def test_markdown_output_groups_by_urgency(self):
        result = self._run("--format", "md")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("# Morning Check — 2026-07-09", result.stdout)
        self.assertIn("## Act now", result.stdout)
        self.assertIn("## Data gaps", result.stdout)

    def test_missing_state_home_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home",
             str(REPO_ROOT / "tests" / "fixtures" / "does-not-exist"), "--offline"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check.CliTests -v`
Expected: FAIL — the script has no CLI yet (argparse error / no `main`).

- [ ] **Step 3: Implement the renderer and CLI**

Append to `scripts/morning_check.py`:

```python
# ----------------------------- rendering + CLI -----------------------------

_URGENCY_HEADERS = [("act", "Act now"), ("review", "Review"), ("watch", "Watch")]


def render_markdown(result: dict) -> str:
    lines = [f"# Morning Check — {result['as_of']}", ""]
    for key, header in _URGENCY_HEADERS:
        hits = [f for f in result["findings"] if f["urgency"] == key]
        if hits:
            lines.append(f"## {header}")
            for f in hits:
                lines.append(f"- **{f['symbol']}** — {f['detail']}")
            lines.append("")
    if result["llm_todo"]:
        lines.append("## KPI / event checks (LLM)")
        for todo in result["llm_todo"]:
            if todo["type"] == "monitor":
                lines.append(f"- **{todo['symbol']}** — monitor {todo.get('kpi')} "
                             f"({todo.get('threshold')}): {todo.get('action')}")
            else:
                lines.append(f"- **{todo['symbol']}** — {todo['trigger_group']} "
                             f"{todo['type']}: {todo.get('text')}")
        lines.append("")
    if result["data_gaps"]:
        lines.append("## Data gaps")
        for gap in result["data_gaps"]:
            lines.append(f"- **{gap['symbol']}** — {gap['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_prices_file(path_str: str) -> dict:
    data = yaml.safe_load(Path(path_str).expanduser().read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _build_source(args):
    prices = _load_prices_file(args.prices) if args.prices else {}
    if args.offline:
        return FilePriceSource(prices)
    if prices:
        return ChainSource(FilePriceSource(prices), LivePriceSource())
    return LivePriceSource()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Morning-check sweep of an investing state home.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--as-of", help="evaluation date YYYY-MM-DD (default: today)")
    parser.add_argument("--earnings-window", type=int, default=7)
    parser.add_argument("--review-window", type=int, default=14)
    parser.add_argument("--prices", help="YAML/JSON {symbol: price} for offline / fallback quotes")
    parser.add_argument("--offline", action="store_true", help="use only --prices, never the network")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2

    as_of = as_date(args.as_of) if args.as_of else datetime.date.today()
    result = evaluate_state(
        home, _build_source(args), as_of,
        earnings_window=args.earnings_window, review_window=args.review_window,
    )
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_morning_check.CliTests -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the whole test module and eyeball a real brief**

Run: `python -m unittest tests.test_morning_check -v`
Expected: PASS (all tests).
Run: `python scripts/morning_check.py --home tests/fixtures/morning-check-home --as-of 2026-07-09 --offline --prices tests/fixtures/morning-check-quotes.yaml`
Expected: a markdown brief with ACME under "Act now" and "Review", NVDA put under "Act now", ACME earnings under "Watch", and 1234.HK under "Data gaps".

- [ ] **Step 6: Commit**

```bash
git add scripts/morning_check.py tests/test_morning_check.py
git commit -m "feat: morning_check CLI, markdown brief, and offline e2e test"
```

---

### Task 7: The morning-check skill + registration

**Files:**
- Create: `skills/morning-check/SKILL.md`
- Create: `skills/morning-check/agents/openai.yaml`
- Modify: `scripts/validate_repo.py`
- Test: `tests/test_morning_check.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_morning_check.py`:

```python
class SkillWiringTests(unittest.TestCase):
    def test_skill_and_openai_metadata_exist(self):
        self.assertTrue((REPO_ROOT / "skills" / "morning-check" / "SKILL.md").exists())
        self.assertTrue((REPO_ROOT / "skills" / "morning-check" / "agents" / "openai.yaml").exists())

    def test_skill_is_registered_in_validate_repo(self):
        text = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("skills/morning-check/SKILL.md", text)
        self.assertIn("skills/morning-check/agents/openai.yaml", text)

    def test_skill_references_the_script_and_state_contract(self):
        skill = (REPO_ROOT / "skills" / "morning-check" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/morning_check.py", skill)
        self.assertIn("decision-records.md", skill)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_morning_check.SkillWiringTests -v`
Expected: FAIL — files do not exist / not registered.

- [ ] **Step 3: Create the skill**

`skills/morning-check/SKILL.md` (frontmatter has no unquoted colons in values — the description avoids `: ` per the `SkillMetadataContractTests` contract):

```markdown
---
name: morning-check
description: Use when the user wants a morning check, portfolio monitoring sweep, or 晨检 across their tracked names — reads the private state home (portfolio.yaml plus decision records), flags crossed price triggers, stale review dates, upcoming earnings, and cash-secured-put assignment risk, judges the free-text KPI/event triggers live, and emits one action brief. Manual trigger; scheduling is out of scope.
---

# Morning Check

## Overview

The manual morning sweep of the private **state home** (see
`skills/analyzing-stocks/references/decision-records.md`). It combines a
deterministic script for the checkable facts with live LLM judgment for the
free-text triggers, then hands back one action brief grouped by urgency.

Deterministic facts come from `scripts/morning_check.py`; this skill never
re-derives price-trigger or date math by hand.

## Steps

1. **Resolve the state home.** Read `~/.investing-home`. If it is missing or the
   directory is unreadable, say so and stop — there is nothing to monitor. Never
   invent state.

2. **Run the deterministic sweep.** Run:

   ```bash
   python scripts/morning_check.py --home "$STATE_HOME" --format json
   ```

   Capture `findings`, `data_gaps`, and `llm_todo` from the JSON.

3. **Fill price gaps (fallback).** For each `data_gaps` entry whose reason is a
   failed/unavailable price, ask the user for a current quote. Write the
   collected quotes to a temporary YAML `{symbol: price}` file and re-run with
   `--prices <file>` so those names are checked rather than dropped. A
   `data_gaps` entry reading "earnings date unknown" is not a price gap — carry
   it into the brief as a "verify earnings date" item instead.

4. **Judge the free-text triggers.** For each `llm_todo` item (KPI/event
   triggers and `monitor` KPIs), do live research (recent news/filings) and
   decide fired / not-fired / uncertain, each with a one-line citation. Fired
   triggers become "Act now" items; uncertain ones become "Watch" items.

5. **Assemble the action brief.** Merge the deterministic findings and the LLM
   judgments into one brief grouped by urgency: **Act now**, **Review**,
   **Watch**, **KPI / event checks**, **Data gaps**. Lead with the most urgent.

6. **Offer to save.** Offer to write the brief to
   `<state-home>/monitoring/YYYY-MM-DD-morning-check.md`. Only write it if the
   user agrees.

## Scope

- Manual trigger only. Scheduling / cron is a later phase.
- Earnings proximity uses the stored `next_earnings` field; do not fetch an
  earnings calendar.
- All price comparisons are in each instrument's native currency; no FX.
```

- [ ] **Step 4: Create the OpenAI metadata**

`skills/morning-check/agents/openai.yaml`:

```yaml
interface:
  display_name: "Morning Check"
  short_description: "Manual morning monitoring sweep of the private state home that flags crossed triggers, stale reviews, upcoming earnings, and put-assignment risk"
  default_prompt: "Use $morning-check to sweep my tracked names, flag any crossed price triggers, stale review dates, upcoming earnings, and cash-secured-put assignment risk, and give me one action brief."
```

- [ ] **Step 5: Register the skill in validate_repo.py**

In `scripts/validate_repo.py`, add to the `FULL_REQUIRED` list (next to the other skills):

```python
    "skills/morning-check/SKILL.md",
    "skills/morning-check/agents/openai.yaml",
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m unittest tests.test_morning_check.SkillWiringTests -v`
Expected: PASS (3 tests).
Run: `python scripts/validate_repo.py --profile full`
Expected: `Repository validation passed for profile: full`.

- [ ] **Step 7: Commit**

```bash
git add skills/morning-check scripts/validate_repo.py tests/test_morning_check.py
git commit -m "feat: add morning-check skill and register it in the repo contract"
```

---

### Task 8: Network-gated live-source smoke test

**Files:**
- Test: `tests/test_morning_check.py`

The live path must never run in the pyyaml-only job (yfinance/akshare are not installed there). Guard it so it skips unless the deps import.

- [ ] **Step 1: Write the guarded smoke test**

Append to `tests/test_morning_check.py`:

```python
class LiveSourceSmokeTests(unittest.TestCase):
    def test_live_source_returns_a_price_for_a_liquid_name(self):
        try:
            import yfinance  # noqa: F401
        except Exception:
            self.skipTest("yfinance not installed (pyyaml-only job)")
        price = mc.LivePriceSource().spot("AAPL")
        # Network may be unavailable; accept None but never an exception.
        self.assertTrue(price is None or (isinstance(price, float) and price > 0))
```

- [ ] **Step 2: Run it in the pyyaml-only environment**

Run: `python -m unittest tests.test_morning_check.LiveSourceSmokeTests -v`
Expected: `skipped` (yfinance not installed) — the test must not fail or hit the network in the main job.

- [ ] **Step 3: Commit**

```bash
git add tests/test_morning_check.py
git commit -m "test: network-gated live-source smoke test for morning_check"
```

---

### Task 9: Full-suite verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full main suite**

Run: `python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: all green (existing tests + the new `tests/test_morning_check.py`), the live smoke test skipped.

- [ ] **Step 2: Run repo structure validation**

Run: `python scripts/validate_repo.py --profile full`
Expected: `Repository validation passed for profile: full`.

- [ ] **Step 3: Confirm the fixture still passes the P0 contract**

Run: `python scripts/validate_records.py --home tests/fixtures/morning-check-home`
Expected: exit 0.

- [ ] **Step 4: Final commit if anything is uncommitted**

```bash
git status --short
# commit any stragglers, otherwise nothing to do
```

---

## Self-review checklist (completed during planning)

- **Spec coverage:** hybrid script+skill (Tasks 2–7); universe union (Task 3); price triggers/drawdown/review_by/next_earnings (Task 4); cash-secured-put assignment (Task 5); provider mapping + fallback + data-gaps (Tasks 2, 4, 6); windows 7/14 defaults (Task 6 argparse); session brief + offer-to-save (Task 7 skill); pyyaml-only tests + provider-mapping identity test + network-gated live test (Tasks 2, 8); skill registration (Task 7). Out-of-scope items (scheduling, live earnings calendar, FX) are excluded by construction.
- **Placeholder scan:** the only intentional forward reference is the `_option_findings` stub in Task 4, explicitly replaced in Task 5.
- **Type consistency:** `evaluate_state(...) -> {"as_of","findings","data_gaps","llm_todo"}`; finding keys `symbol/kind/urgency/detail/evidence`; `provider_for -> (provider, symbol)`; `PriceSource.spot(symbol) -> float | None` — used consistently across tasks.
