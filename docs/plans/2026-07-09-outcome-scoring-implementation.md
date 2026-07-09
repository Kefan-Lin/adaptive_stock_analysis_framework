# P2 Outcome-Scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a forward-only measurement harness that scores past decision records against realized prices and reports calibration by the record fields already stored.

**Architecture:** A deterministic, pyyaml-only `scripts/outcome_score.py` loads every real decision record, fetches historical closes through an injectable `PriceHistory` seam, scores each matured 90/180/365-day window (absolute native-currency return, direction-hit vs stance, WFV/scenario convergence, price-trigger touch), and aggregates a calibration report grouped by `stance`/`confidence`/`valuation_zone`/`market`. A `skills/outcome-scoring` LLM wrapper runs it, fills data gaps, narrates, and opt-in saves the report. It reuses the P0 (`validate_records.py`) loaders and the P1 (`morning_check.py`) provider mapping, mirroring the P1 build exactly.

**Tech Stack:** Python 3.9+ (stdlib + PyYAML only in the main test job); yfinance / akshare lazily imported for live history; `unittest`; existing repo test/validator conventions.

**Spec:** `docs/plans/2026-07-09-outcome-scoring-design.md`

---

## File Structure

- **Create `scripts/outcome_score.py`** — the deterministic core: price-history seam, record loading, per-record scoring, calibration aggregation, rendering, CLI. One file, mirroring `scripts/morning_check.py`.
- **Create `skills/outcome-scoring/SKILL.md`** — LLM wrapper (runs the script, fills gaps, narrates, opt-in save).
- **Create `skills/outcome-scoring/agents/openai.yaml`** — OpenAI parity metadata, mirroring `skills/morning-check/agents/openai.yaml`.
- **Create `tests/test_outcome_score.py`** — the deterministic test suite (mirrors `tests/test_morning_check.py`).
- **Create `tests/fixtures/scoring-home/`** — fictional fixture state home (records + one INDEX.md + one malformed record).
- **Create `tests/fixtures/scoring-closes.yaml`** — fictional `{symbol: {date: close}}` history for offline runs.
- **Modify `scripts/validate_repo.py`** — add the two new skill files to `FULL_REQUIRED`.

Reused (imported, not copied): from `validate_records.py` — `as_date`, `is_number`, `resolve_home`, `SYMBOL_PATTERNS`; from `morning_check.py` — `provider_for`, `load_frontmatter`.

Conventions to copy from `morning_check.py`: `from __future__ import annotations`; a PyYAML import guard that `sys.exit(2)` on ImportError; `sys.path`-free imports (the script lives in `scripts/`, and tests insert `scripts/` on `sys.path`); exit codes `0` clean / `2` environment error.

---

### Task 1: Price-history seam (`FileHistory`, helpers, constants)

**Files:**
- Create: `scripts/outcome_score.py`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_outcome_score.py`:

```python
import datetime
import json
import pathlib
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import outcome_score as os_  # noqa: E402
import validate_records as vr  # noqa: E402

FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "scoring-home"
SCRIPT = REPO_ROOT / "scripts" / "outcome_score.py"
CLOSES = REPO_ROOT / "tests" / "fixtures" / "scoring-closes.yaml"

D = datetime.date


class PriceHistoryTests(unittest.TestCase):
    def _hist(self):
        return os_.FileHistory({"ACME": {
            "2026-01-05": 100.0, "2026-04-03": 118.0, "2026-07-03": 135.0,
        }})

    def test_close_on_exact_date(self):
        self.assertEqual(self._hist().close_on("ACME", D(2026, 1, 5)), 100.0)

    def test_close_on_nearest_prior_trading_day_within_lookback(self):
        # 2026-04-05 is a weekend; the 04-03 close is 2 days prior.
        self.assertEqual(self._hist().close_on("ACME", D(2026, 4, 5)), 118.0)

    def test_close_on_returns_none_beyond_lookback(self):
        self.assertIsNone(self._hist().close_on("ACME", D(2026, 6, 1)))

    def test_close_on_unknown_symbol_is_none(self):
        self.assertIsNone(self._hist().close_on("MISSING", D(2026, 1, 5)))

    def test_low_high_over_window(self):
        lo, hi = self._hist().low_high("ACME", D(2026, 1, 1), D(2026, 7, 4))
        self.assertEqual((lo, hi), (100.0, 135.0))

    def test_low_high_empty_window_is_none_pair(self):
        self.assertEqual(self._hist().low_high("ACME", D(2025, 1, 1), D(2025, 2, 1)),
                         (None, None))

    def test_symbol_patterns_are_the_validate_records_object(self):
        self.assertIs(os_.SYMBOL_PATTERNS, vr.SYMBOL_PATTERNS)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'outcome_score'`.

- [ ] **Step 3: Write minimal implementation**

Create `scripts/outcome_score.py`:

```python
#!/usr/bin/env python3
"""P2 outcome-scoring: score past decision records against realized prices.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-09-outcome-scoring-design.md

Forward-only measurement harness. The deterministic core (this script) loads
every real decision record, fetches historical closes through an injectable
PriceHistory, scores each matured 90/180/365-day window (absolute
native-currency return, direction-hit vs stance, WFV/scenario convergence,
price-trigger touch), and aggregates a calibration report grouped by fields the
records already carry. The outcome-scoring skill narrates on top. Live history
(yfinance/akshare) is lazily imported so the pyyaml-only test job stays
dependency-free.

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
    print("outcome_score.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse P0 loaders/vocabulary and the P1 provider mapping so nothing drifts.
from validate_records import (  # noqa: E402
    SYMBOL_PATTERNS,
    as_date,
    is_number,
    resolve_home,
)
from morning_check import load_frontmatter, provider_for  # noqa: E402

WINDOWS_DEFAULT = (90, 180, 365)
CLOSE_LOOKBACK_DAYS = 7   # nearest prior trading day tolerance for close_on
HOLD_BAND = 0.10          # |return| band for a Hold with no scenarios
LOW_N = 3                 # calibration buckets below this are flagged low_n


# ----------------------------- price history -----------------------------
# A per-symbol series is {date: (close, low, high)}. FileHistory sets
# low == high == close; LiveHistory carries the true daily range.

def _pick_close(series: dict, target: datetime.date) -> "float | None":
    candidates = [d for d in series
                  if d <= target and (target - d).days <= CLOSE_LOOKBACK_DAYS]
    return series[max(candidates)][0] if candidates else None


def _pick_low_high(series: dict, start: datetime.date, end: datetime.date):
    rows = [v for d, v in series.items() if start <= d <= end]
    if not rows:
        return (None, None)
    return (min(r[1] for r in rows), max(r[2] for r in rows))


class FileHistory:
    """Historical closes from a {symbol: {YYYY-MM-DD: close}} mapping.

    Backs offline tests and the owner-provided-close fallback. Window low/high
    are approximated by the min/max of the supplied closes in range.
    """

    def __init__(self, closes: dict) -> None:
        self._series: "dict[str, dict]" = {}
        for symbol, points in (closes or {}).items():
            series: dict = {}
            for day, price in (points or {}).items():
                if not is_number(price):
                    continue
                try:
                    d = as_date(day)
                except (ValueError, TypeError):
                    continue
                series[d] = (float(price), float(price), float(price))
            self._series[str(symbol)] = series

    def prefetch(self, symbol: str, start: datetime.date, end: datetime.date) -> None:
        return None  # nothing to fetch; data is already in memory

    def close_on(self, symbol: str, target: datetime.date) -> "float | None":
        return _pick_close(self._series.get(symbol) or {}, target)

    def low_high(self, symbol: str, start: datetime.date, end: datetime.date):
        return _pick_low_high(self._series.get(symbol) or {}, start, end)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py -q`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: price-history seam (FileHistory + close_on/low_high)"
```

---

### Task 2: Record loading (`load_all_records`)

**Files:**
- Modify: `scripts/outcome_score.py`
- Create: `tests/fixtures/scoring-home/` (records)
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Create the fixture state home**

Create `tests/fixtures/scoring-home/records/GAINR/2026-01-05-new-idea.md`:

```markdown
---
schema: decision-record/v1
symbol: GAINR
market: US
date: 2026-01-05
mode: new-idea
price_at_decision: 100.0
currency: USD
stance: Buy
position_size: Starter
confidence: High
weighted_fair_value: 140
scenarios: {bear: 80, base: 130, bull: 190}
candidate_tier: Core Candidate
valuation_zone: Accumulation
execution_method: Stage buy
triggers:
  add_on:
    - {type: price, level: 85, direction: below}
  trim_exit:
    - {type: price, level: 130, direction: above}
next_earnings: 2026-02-10
review_by: 2026-06-01
source_report: null
action_taken: null
---

# GAINR — new idea (fixture)

Fictional self-contained decision record for tests.
```

Create `tests/fixtures/scoring-home/records/FADE/2026-01-10-position-review.md`:

```markdown
---
schema: decision-record/v1
symbol: FADE
market: US
date: 2026-01-10
mode: position-review
price_at_decision: 200.0
currency: USD
stance: Reduce
position_size: Core
confidence: Medium
weighted_fair_value: 150
scenarios: {bear: 120, base: 160, bull: 210}
candidate_tier: Tactical Candidate
valuation_zone: Exhaustion
execution_method: Reduce
triggers:
  trim_exit:
    - {type: price, level: 205, direction: above}
next_earnings: null
review_by: 2026-06-01
source_report: null
action_taken: null
---

# FADE — position review (fixture)

Fictional self-contained decision record for tests.
```

Create `tests/fixtures/scoring-home/records/HOLDR/2026-02-01-position-review.md`:

```markdown
---
schema: decision-record/v1
symbol: HOLDR
market: US
date: 2026-02-01
mode: position-review
price_at_decision: 50.0
currency: USD
stance: Hold
position_size: Core
confidence: Medium
weighted_fair_value: 55
scenarios: {bear: 40, base: 50, bull: 65}
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: No Action
triggers: {}
next_earnings: null
review_by: 2026-06-01
source_report: null
action_taken: null
---

# HOLDR — position review (fixture)

Fictional self-contained decision record for tests.
```

Create `tests/fixtures/scoring-home/records/NOPRICE/2026-01-05-research.md` (must be **ignored** — no `price_at_decision`):

```markdown
---
schema: decision-record/v1
symbol: NOPRICE
market: US
date: 2026-01-05
mode: research
currency: USD
stance: Hold
review_by: 2026-06-01
---

# NOPRICE — malformed fixture (no price_at_decision, must be skipped)
```

Create `tests/fixtures/scoring-home/records/GAINR/INDEX.md` (must be **ignored** by the loader):

```markdown
# GAINR — decision timeline

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-09-01 | historical | 70 USD | Buy | — | — | — | [report](../../equity_research_2025-09-01/gainr-note.md) |
| 2026-01-05 | new-idea | 100 USD | Buy | 140 | Stage buy | [record](2026-01-05-new-idea.md) | — |
```

- [ ] **Step 2: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class LoadRecordsTests(unittest.TestCase):
    def test_loads_scorable_records_and_skips_malformed_and_index(self):
        metas = os_.load_all_records(FIXTURE_HOME)
        symbols = sorted(m["symbol"] for m in metas)
        self.assertEqual(symbols, ["FADE", "GAINR", "HOLDR"])  # NOPRICE skipped

    def test_missing_records_dir_returns_empty(self):
        empty = os_.load_all_records(REPO_ROOT / "tests" / "fixtures")
        self.assertEqual(empty, [])
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::LoadRecordsTests -q`
Expected: FAIL — `AttributeError: module 'outcome_score' has no attribute 'load_all_records'`.

- [ ] **Step 4: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
# ----------------------------- record loading -----------------------------

def load_all_records(home: Path) -> "list[dict]":
    """Every real, scorable decision record in the state home.

    Skips INDEX.md, unparseable frontmatter, and records lacking a positive
    price_at_decision or a valid date. `historical` rows live only in INDEX.md,
    so forward-only falls out for free.
    """
    out: "list[dict]" = []
    root = home / "records"
    if not root.exists():
        return out
    for symbol_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(symbol_dir.glob("*.md")):
            if path.name == "INDEX.md":
                continue
            meta = load_frontmatter(path)
            if not isinstance(meta, dict):
                continue
            price = meta.get("price_at_decision")
            if not is_number(price) or price <= 0:
                continue
            try:
                as_date(meta.get("date"))
            except (ValueError, TypeError):
                continue
            meta["symbol"] = meta.get("symbol") or symbol_dir.name
            out.append(meta)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::LoadRecordsTests -q`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py tests/fixtures/scoring-home/
git commit -m "P2: load scorable records (skip INDEX, malformed, historical)"
```

---

### Task 3: Return, maturity, and direction-hit

**Files:**
- Modify: `scripts/outcome_score.py`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class DirectionHitTests(unittest.TestCase):
    def test_buy_hit_when_up(self):
        self.assertTrue(os_._direction_hit("Buy", 0.10, 110.0, None))

    def test_buy_miss_when_down(self):
        self.assertFalse(os_._direction_hit("Add", -0.05, 95.0, None))

    def test_reduce_hit_when_down(self):
        self.assertTrue(os_._direction_hit("Reduce", -0.08, 92.0, None))

    def test_avoid_miss_when_up(self):
        self.assertFalse(os_._direction_hit("Avoid", 0.03, 103.0, None))

    def test_hold_hit_inside_scenario_band(self):
        scenarios = {"bear": 40, "base": 50, "bull": 65}
        self.assertTrue(os_._direction_hit("Hold", 0.04, 52.0, scenarios))

    def test_hold_miss_outside_scenario_band(self):
        scenarios = {"bear": 40, "base": 50, "bull": 65}
        self.assertFalse(os_._direction_hit("Hold", 0.60, 80.0, scenarios))

    def test_hold_no_scenarios_uses_return_band(self):
        self.assertTrue(os_._direction_hit("Hold", 0.05, 105.0, None))
        self.assertFalse(os_._direction_hit("Hold", 0.20, 120.0, None))

    def test_no_stance_is_none(self):
        self.assertIsNone(os_._direction_hit(None, 0.10, 110.0, None))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::DirectionHitTests -q`
Expected: FAIL — `AttributeError: ... '_direction_hit'`.

- [ ] **Step 3: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
# ----------------------------- scoring primitives -----------------------------

def _direction_hit(stance, ret, exit_price, scenarios) -> "bool | None":
    """Did the realized move vindicate the stance? None when unscoreable."""
    if stance in ("Buy", "Add"):
        return ret > 0
    if stance in ("Reduce", "Avoid"):
        return ret < 0
    if stance == "Hold":
        if isinstance(scenarios, dict) and is_number(scenarios.get("bear")) \
                and is_number(scenarios.get("bull")):
            return scenarios["bear"] <= exit_price <= scenarios["bull"]
        return abs(ret) <= HOLD_BAND
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::DirectionHitTests -q`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: direction-hit rule (Buy/Add/Reduce/Avoid/Hold)"
```

---

### Task 4: WFV convergence and scenario landing

**Files:**
- Modify: `scripts/outcome_score.py`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class WfvAndScenarioTests(unittest.TestCase):
    def test_wfv_converges_toward_fair_value(self):
        # P0 100, WFV 140 (undervalued); exit 118 moved toward WFV.
        gap_closed, converged = os_._wfv(100.0, 118.0, 140)
        self.assertAlmostEqual(gap_closed, 0.45, places=2)  # (40-22)/40
        self.assertTrue(converged)

    def test_wfv_moves_away_is_not_converged(self):
        gap_closed, converged = os_._wfv(100.0, 90.0, 140)
        self.assertLess(gap_closed, 0)
        self.assertFalse(converged)

    def test_wfv_overshoot_wrong_direction_not_converged(self):
        # Overvalued call (WFV 80 < P0 100) but price rose: wrong direction.
        gap_closed, converged = os_._wfv(100.0, 110.0, 80)
        self.assertFalse(converged)

    def test_wfv_none_when_absent(self):
        self.assertIsNone(os_._wfv(100.0, 118.0, None))

    def test_wfv_none_when_price_equals_fair_value(self):
        self.assertIsNone(os_._wfv(140.0, 150.0, 140))

    def test_scenario_landing_bands(self):
        s = {"bear": 80, "base": 130, "bull": 190}
        self.assertEqual(os_._scenario_landing(70, s), "below_bear")
        self.assertEqual(os_._scenario_landing(100, s), "bear_base")
        self.assertEqual(os_._scenario_landing(160, s), "base_bull")
        self.assertEqual(os_._scenario_landing(200, s), "above_bull")

    def test_scenario_landing_none_when_incomplete(self):
        self.assertIsNone(os_._scenario_landing(100, {"bear": 80}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::WfvAndScenarioTests -q`
Expected: FAIL — `AttributeError: ... '_wfv'`.

- [ ] **Step 3: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
def _wfv(p0, exit_price, wfv):
    """(gap_closed, converged) toward weighted_fair_value, or None.

    gap_closed is the fraction of the initial |price - WFV| gap that closed
    (1.0 = reached WFV, negative = moved away). converged requires closing the
    gap *and* moving in the WFV direction (not overshooting the wrong way).
    None when WFV is absent or the price already sits at fair value.
    """
    if not is_number(wfv) or p0 == wfv:
        return None
    before = abs(p0 - wfv)
    after = abs(exit_price - wfv)
    gap_closed = (before - after) / before
    moved_right_way = ((exit_price - p0) > 0) == ((wfv - p0) > 0)
    return (round(gap_closed, 4), bool(gap_closed > 0 and moved_right_way))


def _scenario_landing(exit_price, scenarios) -> "str | None":
    bear = scenarios.get("bear")
    base = scenarios.get("base")
    bull = scenarios.get("bull")
    if not all(is_number(x) for x in (bear, base, bull)):
        return None
    if exit_price < bear:
        return "below_bear"
    if exit_price <= base:
        return "bear_base"
    if exit_price <= bull:
        return "base_bull"
    return "above_bull"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::WfvAndScenarioTests -q`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: WFV convergence + scenario landing"
```

---

### Task 5: Price-trigger touch

**Files:**
- Modify: `scripts/outcome_score.py`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class TriggerTouchTests(unittest.TestCase):
    def test_trim_exit_above_touched_by_window_high(self):
        triggers = {"trim_exit": [{"type": "price", "level": 130, "direction": "above"}]}
        touches = os_._trigger_touches(triggers, low=100.0, high=135.0)
        self.assertEqual(touches, [{"group": "trim_exit", "level": 130,
                                    "direction": "above", "touched": True}])

    def test_add_on_below_not_touched(self):
        triggers = {"add_on": [{"type": "price", "level": 85, "direction": "below"}]}
        touches = os_._trigger_touches(triggers, low=100.0, high=135.0)
        self.assertEqual(touches[0]["touched"], False)

    def test_non_price_trigger_ignored(self):
        triggers = {"add_on": [{"type": "kpi", "text": "x"}]}
        self.assertEqual(os_._trigger_touches(triggers, 100.0, 135.0), [])

    def test_touched_is_none_when_range_unavailable(self):
        triggers = {"trim_exit": [{"type": "price", "level": 130, "direction": "above"}]}
        self.assertIsNone(os_._trigger_touches(triggers, None, None)[0]["touched"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::TriggerTouchTests -q`
Expected: FAIL — `AttributeError: ... '_trigger_touches'`.

- [ ] **Step 3: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
def _trigger_touches(triggers, low, high) -> "list[dict]":
    """Per price trigger, whether its level was touched in the window.

    `below` triggers are touched when the window low reached the level; `above`
    triggers when the window high reached it. `touched` is None when the range
    is unavailable (a data gap on the range, not a false negative).
    """
    out: "list[dict]" = []
    for group in ("add_on", "trim_exit"):
        for item in (triggers or {}).get(group) or []:
            if not isinstance(item, dict) or item.get("type") != "price":
                continue
            level = item.get("level")
            direction = item.get("direction")
            if not is_number(level) or direction not in ("above", "below"):
                continue
            if direction == "below":
                touched = None if low is None else bool(low <= level)
            else:
                touched = None if high is None else bool(high >= level)
            out.append({"group": group, "level": level,
                        "direction": direction, "touched": touched})
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::TriggerTouchTests -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: price-trigger touch via window low/high"
```

---

### Task 6: Per-record scoring + `evaluate_home` orchestrator

**Files:**
- Modify: `scripts/outcome_score.py`
- Create: `tests/fixtures/scoring-closes.yaml`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Create the closes fixture**

Create `tests/fixtures/scoring-closes.yaml` (fictional; dates chosen so 90/180/365-day targets resolve within the 7-day look-back):

```yaml
# Fictional historical closes {symbol: {YYYY-MM-DD: close}} for offline scoring.
GAINR:
  "2026-01-05": 100.0
  "2026-04-05": 118.0    # +90d: up, base_bull, converging toward WFV 140
  "2026-07-04": 135.0    # +180d
  "2027-01-05": 160.0    # +365d
FADE:
  "2026-01-10": 200.0
  "2026-04-10": 180.0    # +90d: down (Reduce hit)
  "2026-07-09": 165.0    # +180d
  "2027-01-10": 150.0    # +365d
HOLDR:
  "2026-02-01": 50.0
  "2026-05-02": 52.0     # +90d: inside [40,65] band (Hold hit)
  "2026-07-31": 48.0     # +180d
  "2027-02-01": 58.0     # +365d
```

- [ ] **Step 2: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
def _closes():
    return {
        "GAINR": {"2026-01-05": 100.0, "2026-04-05": 118.0,
                  "2026-07-04": 135.0, "2027-01-05": 160.0},
        "FADE": {"2026-01-10": 200.0, "2026-04-10": 180.0,
                 "2026-07-09": 165.0, "2027-01-10": 150.0},
        "HOLDR": {"2026-02-01": 50.0, "2026-05-02": 52.0,
                  "2026-07-31": 48.0, "2027-02-01": 58.0},
    }


class EvaluateHomeTests(unittest.TestCase):
    def test_all_windows_pending_before_maturity(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2026, 3, 1))
        self.assertEqual(result["scored"], [])
        pending_syms = {p["symbol"] for p in result["pending"]}
        self.assertEqual(pending_syms, {"GAINR", "FADE", "HOLDR"})

    def test_matured_windows_scored(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        by_symbol = {r["symbol"]: r for r in result["scored"]}
        self.assertEqual(set(by_symbol), {"GAINR", "FADE", "HOLDR"})
        gainr90 = by_symbol["GAINR"]["windows"]["90"]
        self.assertAlmostEqual(gainr90["return"], 0.18, places=4)
        self.assertTrue(gainr90["direction_hit"])
        self.assertTrue(gainr90["converged"])
        self.assertEqual(gainr90["scenario_landing"], "bear_base")
        fade90 = by_symbol["FADE"]["windows"]["90"]
        self.assertTrue(fade90["direction_hit"])   # Reduce, price fell
        hold90 = by_symbol["HOLDR"]["windows"]["90"]
        self.assertTrue(hold90["direction_hit"])    # inside band

    def test_missing_close_is_data_gap(self):
        closes = _closes()
        del closes["GAINR"]["2027-01-05"]  # drop the +365d close
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(closes),
                                   as_of=D(2027, 7, 1))
        gaps = [g for g in result["data_gaps"]
                if g["symbol"] == "GAINR" and g["window"] == 365]
        self.assertEqual(len(gaps), 1)
```

Note: GAINR +90d target is 2026-04-05; nearest prior close is the 04-05 fixture entry (exact), value 118 → return 0.18, and 118 lands in `[bear 80, base 130]` → `bear_base`.

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::EvaluateHomeTests -q`
Expected: FAIL — `AttributeError: ... 'evaluate_home'`.

- [ ] **Step 4: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
# ----------------------------- per-record scoring -----------------------------

def score_record(meta: dict, history, as_of: datetime.date, windows):
    """Score one record. Returns (record | None, pending[], data_gaps[])."""
    symbol = meta["symbol"]
    p0 = float(meta["price_at_decision"])
    d = as_date(meta["date"])
    stance = meta.get("stance")
    scenarios = meta.get("scenarios")
    wfv = meta.get("weighted_fair_value")
    triggers = meta.get("triggers") or {}

    win_results: "dict[str, dict]" = {}
    pending: "list[dict]" = []
    gaps: "list[dict]" = []
    for w in windows:
        target = d + datetime.timedelta(days=w)
        if as_of < target:
            pending.append({"symbol": symbol, "date": d.isoformat(),
                            "window": w, "matures_on": target.isoformat()})
            continue
        exit_price = history.close_on(symbol, target)
        if exit_price is None:
            gaps.append({"symbol": symbol, "date": d.isoformat(), "window": w,
                         "reason": f"no close near {target.isoformat()}"})
            continue
        ret = (exit_price - p0) / p0
        res: dict = {"exit_price": exit_price, "return": round(ret, 4),
                     "direction_hit": _direction_hit(stance, ret, exit_price, scenarios)}
        wfv_res = _wfv(p0, exit_price, wfv)
        if wfv_res is not None:
            res["gap_closed"], res["converged"] = wfv_res
        if isinstance(scenarios, dict):
            landing = _scenario_landing(exit_price, scenarios)
            if landing is not None:
                res["scenario_landing"] = landing
        low, high = history.low_high(symbol, d, target)
        touches = _trigger_touches(triggers, low, high)
        if touches:
            res["trigger_touches"] = touches
        win_results[str(w)] = res

    record = None
    if win_results:
        record = {
            "symbol": symbol, "date": d.isoformat(), "mode": meta.get("mode"),
            "stance": stance, "confidence": meta.get("confidence"),
            "valuation_zone": meta.get("valuation_zone"), "market": meta.get("market"),
            "price_at_decision": p0, "windows": win_results,
        }
    return record, pending, gaps


def evaluate_home(home: Path, history, as_of: datetime.date,
                  windows=WINDOWS_DEFAULT) -> dict:
    records = load_all_records(home)
    by_symbol: "dict[str, list[dict]]" = {}
    for meta in records:
        by_symbol.setdefault(meta["symbol"], []).append(meta)

    scored: "list[dict]" = []
    pending: "list[dict]" = []
    gaps: "list[dict]" = []
    max_window = max(windows)
    for symbol in sorted(by_symbol):
        metas = by_symbol[symbol]
        dates = [as_date(m["date"]) for m in metas]
        span_lo = min(dates)
        span_hi = min(as_of, max(d + datetime.timedelta(days=max_window) for d in dates))
        history.prefetch(symbol, span_lo, span_hi)
        for meta in sorted(metas, key=lambda m: m["date"]):
            record, p, g = score_record(meta, history, as_of, windows)
            if record is not None:
                scored.append(record)
            pending.extend(p)
            gaps.extend(g)

    return {
        "as_of": as_of.isoformat(), "windows": list(windows),
        "scored": scored, "pending": pending, "data_gaps": gaps,
        "calibration": calibrate(scored, windows),
    }
```

Note: `evaluate_home` calls `calibrate`, added in Task 7. Until then this task's tests exercise `score_record` paths; run the whole file after Task 7. To keep Task 6 green on its own, add a temporary stub at the end of the module now:

```python
def calibrate(scored, windows):  # replaced in Task 7
    return {}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::EvaluateHomeTests -q`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py tests/fixtures/scoring-closes.yaml
git commit -m "P2: per-record scoring + evaluate_home orchestrator"
```

---

### Task 7: Calibration aggregation

**Files:**
- Modify: `scripts/outcome_score.py` (replace the `calibrate` stub)
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class CalibrationTests(unittest.TestCase):
    def _cal(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        return result["calibration"]

    def test_overall_bucket_counts_all_scored_records(self):
        overall90 = self._cal()["overall"]["90"]
        self.assertEqual(overall90["n"], 3)               # GAINR, FADE, HOLDR
        self.assertAlmostEqual(overall90["hit_rate"], 1.0)  # all three hit at 90d

    def test_by_stance_buckets(self):
        by_stance = self._cal()["by_stance"]["90"]
        self.assertIn("Buy", by_stance)
        self.assertIn("Reduce", by_stance)
        self.assertEqual(by_stance["Buy"]["n"], 1)
        self.assertTrue(by_stance["Buy"]["low_n"])        # n < LOW_N

    def test_median_return_computed(self):
        overall90 = self._cal()["overall"]["90"]
        self.assertIn("median_return", overall90)

    def test_wfv_convergence_rate_over_records_with_wfv(self):
        by_stance = self._cal()["by_stance"]["90"]
        self.assertIsNotNone(by_stance["Buy"]["wfv_convergence"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::CalibrationTests -q`
Expected: FAIL — the stub returns `{}`, so `["overall"]` raises `KeyError`.

- [ ] **Step 3: Write minimal implementation**

Replace the temporary `calibrate` stub in `scripts/outcome_score.py` with:

```python
# ----------------------------- calibration -----------------------------

_DIMENSIONS = (
    ("by_stance", "stance"),
    ("by_confidence", "confidence"),
    ("by_valuation_zone", "valuation_zone"),
    ("by_market", "market"),
)


def _median(xs: "list[float]") -> "float | None":
    values = sorted(xs)
    n = len(values)
    if n == 0:
        return None
    mid = n // 2
    return values[mid] if n % 2 else (values[mid - 1] + values[mid]) / 2


def _summarize(results: "list[dict]") -> dict:
    returns = [r["return"] for r in results]
    hits = [r["direction_hit"] for r in results if r.get("direction_hit") is not None]
    convs = [r["converged"] for r in results if r.get("converged") is not None]
    return {
        "n": len(results),
        "hit_rate": round(sum(1 for h in hits if h) / len(hits), 4) if hits else None,
        "mean_return": round(sum(returns) / len(returns), 4) if returns else None,
        "median_return": round(_median(returns), 4) if returns else None,
        "wfv_convergence": round(sum(1 for c in convs if c) / len(convs), 4) if convs else None,
        "low_n": len(results) < LOW_N,
    }


def calibrate(scored: "list[dict]", windows) -> dict:
    # Flatten to (record, window, window-result) for every scored window.
    flat = [(rec, int(w), res)
            for rec in scored for w, res in rec["windows"].items()]
    out: dict = {}
    for key, field in _DIMENSIONS:
        out[key] = {}
        for w in windows:
            buckets: "dict[str, list[dict]]" = {}
            for rec, ww, res in flat:
                if ww != w:
                    continue
                bucket = rec.get(field) or "—"
                buckets.setdefault(bucket, []).append(res)
            out[key][str(w)] = {b: _summarize(v) for b, v in sorted(buckets.items())}
    out["overall"] = {}
    for w in windows:
        out["overall"][str(w)] = _summarize([res for _, ww, res in flat if ww == w])
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::CalibrationTests -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: calibration aggregation by stance/confidence/zone/market"
```

---

### Task 8: Rendering, `LiveHistory`, `ChainHistory`, and CLI

**Files:**
- Modify: `scripts/outcome_score.py`
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class RenderTests(unittest.TestCase):
    def test_markdown_has_headline_and_tables(self):
        result = os_.evaluate_home(FIXTURE_HOME, os_.FileHistory(_closes()),
                                   as_of=D(2027, 7, 1))
        md = os_.render_markdown(result)
        self.assertIn("# Outcome Scoring — 2027-07-01", md)
        self.assertIn("## Window 90d", md)
        self.assertIn("By stance", md)


class ChainHistoryTests(unittest.TestCase):
    def test_file_close_wins_then_falls_through(self):
        chain = os_.ChainHistory(os_.FileHistory({"A": {"2026-01-01": 10.0}}),
                                 os_.FileHistory({"B": {"2026-01-01": 20.0}}))
        self.assertEqual(chain.close_on("A", D(2026, 1, 1)), 10.0)
        self.assertEqual(chain.close_on("B", D(2026, 1, 1)), 20.0)
        self.assertIsNone(chain.close_on("C", D(2026, 1, 1)))


class CliTests(unittest.TestCase):
    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "2027-07-01", "--offline", "--prices", str(CLOSES), *extra],
            capture_output=True, text=True,
        )

    def test_json_output(self):
        result = self._run("--format", "json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2027-07-01")
        self.assertEqual(payload["calibration"]["overall"]["90"]["n"], 3)

    def test_markdown_output(self):
        result = self._run("--format", "md")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("# Outcome Scoring — 2027-07-01", result.stdout)

    def test_custom_windows(self):
        result = self._run("--format", "json", "--windows", "90")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["windows"], [90])

    def test_missing_state_home_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home",
             str(REPO_ROOT / "tests" / "fixtures" / "nope"), "--offline"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_bad_as_of_is_environment_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(FIXTURE_HOME),
             "--as-of", "not-a-date", "--offline"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::RenderTests tests/test_outcome_score.py::ChainHistoryTests tests/test_outcome_score.py::CliTests -q`
Expected: FAIL — `AttributeError: ... 'render_markdown'`.

- [ ] **Step 3: Write minimal implementation**

Append to `scripts/outcome_score.py`:

```python
# ----------------------------- live + chain history -----------------------------

class LiveHistory:
    """Historical closes via yfinance (US/HK/KR/AU) and akshare (CN A-shares).

    Heavy providers are imported lazily inside prefetch so importing this module
    never requires them. One fetch per symbol is cached as {date: (close, low,
    high)}; any per-name failure yields an empty series (→ data gaps).
    """

    def __init__(self) -> None:
        self._cache: "dict[str, dict]" = {}

    def prefetch(self, symbol: str, start: datetime.date, end: datetime.date) -> None:
        if symbol in self._cache:
            return
        provider, provider_symbol = provider_for(symbol)
        try:
            if provider == "akshare":
                self._cache[symbol] = self._akshare(provider_symbol, start, end)
            else:
                self._cache[symbol] = self._yfinance(provider_symbol, start, end)
        except Exception:
            self._cache[symbol] = {}

    def close_on(self, symbol: str, target: datetime.date) -> "float | None":
        return _pick_close(self._cache.get(symbol) or {}, target)

    def low_high(self, symbol: str, start: datetime.date, end: datetime.date):
        return _pick_low_high(self._cache.get(symbol) or {}, start, end)

    @staticmethod
    def _yfinance(provider_symbol: str, start: datetime.date, end: datetime.date) -> dict:
        import yfinance as yf

        # end is inclusive for our purposes; yfinance end is exclusive.
        hist = yf.Ticker(provider_symbol).history(
            start=start.isoformat(),
            end=(end + datetime.timedelta(days=1)).isoformat(),
        )
        series: dict = {}
        if hist is not None and not hist.empty:
            for ts, row in hist.iterrows():
                day = ts.date() if hasattr(ts, "date") else as_date(str(ts)[:10])
                series[day] = (float(row["Close"]), float(row["Low"]), float(row["High"]))
        return series

    @staticmethod
    def _akshare(provider_symbol: str, start: datetime.date, end: datetime.date) -> dict:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol=provider_symbol, period="daily",
            start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"),
            adjust="",
        )
        series: dict = {}
        if df is not None and len(df):
            for _, row in df.iterrows():
                day = as_date(str(row["日期"])[:10])
                series[day] = (float(row["收盘"]), float(row["最低"]), float(row["最高"]))
        return series


class ChainHistory:
    """Try `first` (e.g. owner-provided closes), then `second` (live)."""

    def __init__(self, first, second) -> None:
        self._first = first
        self._second = second

    def prefetch(self, symbol, start, end) -> None:
        self._first.prefetch(symbol, start, end)
        self._second.prefetch(symbol, start, end)

    def close_on(self, symbol, target) -> "float | None":
        value = self._first.close_on(symbol, target)
        return value if value is not None else self._second.close_on(symbol, target)

    def low_high(self, symbol, start, end):
        low, high = self._first.low_high(symbol, start, end)
        if low is not None and high is not None:
            return (low, high)
        return self._second.low_high(symbol, start, end)


# ----------------------------- rendering -----------------------------

def _fmt(value, pct=False) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%" if pct else f"{value}"


def _dimension_table(title: str, buckets: dict) -> "list[str]":
    lines = [f"**{title}**", "",
             "| bucket | N | hit-rate | mean ret | median ret | WFV conv | |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, s in buckets.items():
        flag = "low-N" if s["low_n"] else ""
        lines.append(
            f"| {name} | {s['n']} | {_fmt(s['hit_rate'], True)} | "
            f"{_fmt(s['mean_return'], True)} | {_fmt(s['median_return'], True)} | "
            f"{_fmt(s['wfv_convergence'], True)} | {flag} |")
    lines.append("")
    return lines


def render_markdown(result: dict) -> str:
    lines = [f"# Outcome Scoring — {result['as_of']}", ""]
    cal = result["calibration"]
    for w in result["windows"]:
        wk = str(w)
        overall = cal["overall"][wk]
        lines.append(f"## Window {w}d")
        lines.append(
            f"Overall: N={overall['n']}, hit-rate {_fmt(overall['hit_rate'], True)}, "
            f"mean {_fmt(overall['mean_return'], True)}, "
            f"median {_fmt(overall['median_return'], True)}, "
            f"WFV-conv {_fmt(overall['wfv_convergence'], True)}.")
        lines.append("")
        lines.extend(_dimension_table("By stance", cal["by_stance"][wk]))
        lines.extend(_dimension_table("By confidence", cal["by_confidence"][wk]))
        lines.extend(_dimension_table("By valuation zone", cal["by_valuation_zone"][wk]))
        lines.extend(_dimension_table("By market", cal["by_market"][wk]))
    if result["pending"]:
        lines.append("## Pending (not yet matured)")
        for p in result["pending"]:
            lines.append(f"- **{p['symbol']}** {p['date']} — {p['window']}d "
                         f"matures {p['matures_on']}")
        lines.append("")
    if result["data_gaps"]:
        lines.append("## Data gaps")
        for g in result["data_gaps"]:
            lines.append(f"- **{g['symbol']}** {g['date']} — {g['window']}d: {g['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ----------------------------- CLI -----------------------------

def _load_closes_file(path_str: str) -> dict:
    data = yaml.safe_load(Path(path_str).expanduser().read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _build_history(args):
    closes = _load_closes_file(args.prices) if args.prices else {}
    if args.offline:
        return FileHistory(closes)
    if closes:
        return ChainHistory(FileHistory(closes), LiveHistory())
    return LiveHistory()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Outcome-score a private investing state home's decision records.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--as-of", help="evaluation date YYYY-MM-DD (default: today)")
    parser.add_argument("--windows", default="90,180,365",
                        help="comma-separated horizon days (default: 90,180,365)")
    parser.add_argument("--prices", help="YAML/JSON {symbol: {date: close}} for offline / fallback")
    parser.add_argument("--offline", action="store_true", help="use only --prices, never the network")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2

    if args.as_of:
        try:
            as_of = as_date(args.as_of)
        except (ValueError, TypeError):
            print(f"--as-of is not an ISO date (YYYY-MM-DD): {args.as_of!r}", file=sys.stderr)
            return 2
    else:
        as_of = datetime.date.today()

    try:
        windows = tuple(int(x) for x in str(args.windows).split(",") if x.strip())
    except ValueError:
        print(f"--windows must be comma-separated integers: {args.windows!r}", file=sys.stderr)
        return 2
    if not windows:
        print("--windows produced no horizons", file=sys.stderr)
        return 2

    try:
        history = _build_history(args)
    except OSError as exc:
        print(f"could not read --prices file: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"--prices file is not valid YAML: {exc}", file=sys.stderr)
        return 2

    result = evaluate_home(home, history, as_of, windows=windows)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py -q`
Expected: PASS (all tests so far, including Render/Chain/CLI).

- [ ] **Step 5: Commit**

```bash
git add scripts/outcome_score.py tests/test_outcome_score.py
git commit -m "P2: LiveHistory, ChainHistory, markdown render, CLI"
```

---

### Task 9: Skill, OpenAI parity, and repo wiring

**Files:**
- Create: `skills/outcome-scoring/SKILL.md`
- Create: `skills/outcome-scoring/agents/openai.yaml`
- Modify: `scripts/validate_repo.py:19-76` (add to `FULL_REQUIRED`)
- Test: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_outcome_score.py`:

```python
class SkillWiringTests(unittest.TestCase):
    def test_skill_and_openai_metadata_exist(self):
        self.assertTrue((REPO_ROOT / "skills" / "outcome-scoring" / "SKILL.md").exists())
        self.assertTrue((REPO_ROOT / "skills" / "outcome-scoring" / "agents" / "openai.yaml").exists())

    def test_skill_is_registered_in_validate_repo(self):
        text = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("skills/outcome-scoring/SKILL.md", text)
        self.assertIn("skills/outcome-scoring/agents/openai.yaml", text)

    def test_skill_references_the_script_and_state_contract(self):
        skill = (REPO_ROOT / "skills" / "outcome-scoring" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/outcome_score.py", skill)
        self.assertIn("decision-records.md", skill)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::SkillWiringTests -q`
Expected: FAIL — files do not exist.

- [ ] **Step 3: Create the skill**

Create `skills/outcome-scoring/SKILL.md` (the `description` is one line with no unquoted `": "`, per the `SkillMetadataContractTests` frontmatter rule):

```markdown
---
name: outcome-scoring
description: Use when the user wants to score past decisions, measure calibration, or review how their tracked names actually turned out (成绩复盘). Reads the private state home (every decision record), computes 90/180/365-day realized outcomes against stance and weighted fair value, and reports a calibration table grouped by stance, confidence, valuation zone, and market. Forward-only; manual trigger only.
---

# Outcome Scoring

## Overview

The forward-only measurement harness over the private **state home** (see
`skills/analyzing-stocks/references/decision-records.md`). It scores every real
decision record against realized prices and reports whether the framework's own
labels — stance, confidence, valuation zone — were predictive.

Deterministic scoring comes from `scripts/outcome_score.py`; this skill never
re-derives return or convergence math by hand. Early on, most records will be
**pending** (not yet 90 days old) — that is expected.

## Steps

1. **Resolve the state home.** Read `~/.investing-home`. If it is missing or the
   directory is unreadable, say so and stop — there is nothing to score. Never
   invent state.

2. **Run the deterministic scorer.** Run:

   ```bash
   python scripts/outcome_score.py --home "$STATE_HOME" --format json
   ```

   Capture `scored`, `pending`, `data_gaps`, and `calibration` from the JSON.

3. **Fill data gaps (fallback).** Each `data_gaps` entry names a `symbol`,
   `date`, `window`, and the target date whose close was unavailable. Ask the
   user for that historical close, write the collected closes to a temporary
   YAML `{symbol: {date: close}}` file, and re-run with `--prices <file>` so the
   window is scored rather than dropped.

4. **Narrate the calibration.** Summarize what the buckets say: which cohorts
   (e.g. High-confidence, Accumulation-zone, Buy) actually realized better
   outcomes, and where `low_n` means the sample is too small to trust. Do not
   over-read a bucket flagged `low-N`.

5. **Offer to save.** Offer to write the report to
   `<state-home>/scoring/YYYY-MM-DD-outcome-scoring.md`. Only write it if the
   user agrees.

## Scope

- Manual trigger only. Scheduling / cron is a later phase.
- Absolute native-currency returns; no FX and no benchmark this pass.
- Grouping uses fields the record already carries (stance, confidence,
  valuation zone, market); sector / valuation-family grouping is deferred.
- Forward-only: `historical` index rows are never scored.
- Default windows 90/180/365 days; override with `--windows`.
```

- [ ] **Step 4: Create the OpenAI parity metadata**

Create `skills/outcome-scoring/agents/openai.yaml`:

```yaml
interface:
  display_name: "Outcome Scoring"
  short_description: "Forward-only scoring of past decision records against realized 90/180/365-day prices, with a calibration table by stance, confidence, valuation zone, and market"
  default_prompt: "Use $outcome-scoring to score my past decisions against how prices actually moved and show me a calibration table by stance, confidence, valuation zone, and market."
```

- [ ] **Step 5: Register the skill in `validate_repo.py`**

In `scripts/validate_repo.py`, inside the `FULL_REQUIRED` list, add (keep the existing `skills/morning-check/...` lines and place these right after them):

```python
    "skills/outcome-scoring/SKILL.md",
    "skills/outcome-scoring/agents/openai.yaml",
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::SkillWiringTests -q`
Expected: PASS (3 tests).

Run: `.venv/bin/python -m pytest tests/test_skill_contracts.py::SkillMetadataContractTests -q`
Expected: PASS (the new skill's frontmatter has no unquoted colon sequence).

Run: `.venv/bin/python scripts/validate_repo.py --profile full`
Expected: `Repository validation passed for profile: full`.

- [ ] **Step 7: Commit**

```bash
git add skills/outcome-scoring/ scripts/validate_repo.py tests/test_outcome_score.py
git commit -m "P2: outcome-scoring skill, OpenAI parity, repo registration"
```

---

### Task 10: Live-history smoke test (network-gated)

**Files:**
- Modify: `tests/test_outcome_score.py`

- [ ] **Step 1: Write the test**

Append to `tests/test_outcome_score.py`:

```python
class LiveHistorySmokeTests(unittest.TestCase):
    def test_live_history_returns_a_close_or_none_never_raises(self):
        try:
            import yfinance  # noqa: F401
        except Exception:
            self.skipTest("yfinance not installed (pyyaml-only job)")
        hist = os_.LiveHistory()
        end = datetime.date.today()
        start = end - datetime.timedelta(days=30)
        hist.prefetch("AAPL", start, end)
        close = hist.close_on("AAPL", end)
        # Network may be unavailable; accept None but never an exception.
        self.assertTrue(close is None or (isinstance(close, float) and close > 0))
```

- [ ] **Step 2: Run the test**

Run: `.venv/bin/python -m pytest tests/test_outcome_score.py::LiveHistorySmokeTests -q`
Expected: PASS or SKIP (skips when yfinance is absent; passes with `None`-or-positive when present).

- [ ] **Step 3: Commit**

```bash
git add tests/test_outcome_score.py
git commit -m "P2: network-gated live-history smoke test"
```

---

### Task 11: Full-suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the whole suite**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: all green (existing suite + the new `test_outcome_score.py`).

- [ ] **Step 2: Run the repo validator**

Run: `.venv/bin/python scripts/validate_repo.py --profile full`
Expected: `Repository validation passed for profile: full`.

- [ ] **Step 3: Smoke-run the CLI against the fixture**

Run:
```bash
.venv/bin/python scripts/outcome_score.py --home tests/fixtures/scoring-home \
  --offline --prices tests/fixtures/scoring-closes.yaml --as-of 2027-07-01 --format md
```
Expected: an "Outcome Scoring — 2027-07-01" report with Window 90d/180d/365d sections and By-stance/confidence/zone/market tables.

- [ ] **Step 4: Commit any final cleanup (if needed)**

```bash
git commit --allow-empty -m "P2: outcome-scoring implementation complete"
```

---

## Self-Review

**Spec coverage** (each design section → task):
- Deterministic core `scripts/outcome_score.py` → Tasks 1–8.
- `PriceHistory.close_on` + nearest-prior-trading-day + `FileHistory`/`LiveHistory`/`ChainHistory` → Tasks 1, 8.
- Load every real record, skip INDEX/malformed/historical, `research` allowed → Task 2.
- Per-record: maturity/pending, return, direction-hit (incl. bear–bull Hold rule + ±10% fallback), WFV `gap_closed`/`converged` (with `P0==WFV` omission), scenario landing, trigger touch → Tasks 3–6.
- Calibration by stance/confidence/valuation_zone/market + overall + low-N → Task 7.
- JSON + markdown output; CLI flags `--home/--as-of/--windows/--prices/--offline/--format`; exit 0/2 → Task 8.
- `skills/outcome-scoring` wrapper + OpenAI parity + `validate_repo` registration + wiring tests → Task 9.
- Live smoke test, no new main-job dependency → Task 10.
- Full-suite + validator + CLI verification → Task 11.

**Placeholder scan:** no TBD/TODO; every code step shows complete code; the Task 6 `calibrate` stub is explicitly replaced in Task 7.

**Type consistency:** `close_on(symbol, date)`, `low_high(symbol, start, end)`, `prefetch(symbol, start, end)` identical across `FileHistory`/`LiveHistory`/`ChainHistory`; `_wfv` returns `(gap_closed, converged)` consumed in `score_record`; window-result keys (`return`, `direction_hit`, `converged`, `scenario_landing`, `trigger_touches`) match what `calibrate`/`render_markdown` read; window keys are strings (`"90"`) everywhere; `_summarize` fields match the render table columns.

**Out-of-scope confirmed absent:** no benchmark/FX, no sector/valuation-family grouping, no P&L weighting, no scheduling, no scoring of `historical` rows.
