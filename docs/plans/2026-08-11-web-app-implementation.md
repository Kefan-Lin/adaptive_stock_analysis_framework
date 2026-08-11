# Web App (Read-Only Projection Layer) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the static-site projection layer approved in
`docs/plans/2026-08-11-web-app-design.md`: `scripts/export_web.py` (vault →
`web-export/v1` JSON) + `scripts/build_webapp.py` (JSON → Zone Board index +
per-symbol Thesis Timeline pages), private `file://` build and sanitized
GitHub Pages demo build.

**Architecture:** Two-stage pipeline with the JSON dataset as the contract
seam. The exporter reuses the P0/P1/P2 loaders (`validate_records.py`,
`morning_check.py`, `outcome_score.py` as a library) and computes every
judgment-free mechanical signal Python-side; the builder inlines data +
vendored ECharts into static pages ported from the two user-approved
prototypes. Zero network in the browser, zero node in the toolchain.

**Tech Stack:** Python 3 (repo `.venv`), PyYAML, `markdown` (lazy,
export-path only), yfinance/akshare (lazy, live path only), vendored ECharts
5.6.0, GitHub Actions `deploy-pages` for the demo.

---

## Context for the executing engineer

- **Run everything with the repo venv:** `.venv/bin/python`. Global numpy is
  broken on this machine; never use system python.
- **Tests are stdlib `unittest`**, run as
  `.venv/bin/python -m unittest tests.test_<name> -v`. The main CI job
  installs **only pyyaml**, so any test needing `markdown`/`yfinance` must
  `skipUnless` on importability (existing pattern: see
  `tests/test_outcome_score.py` live tests).
- **The design doc is the spec:** `docs/plans/2026-08-11-web-app-design.md`.
  Read it first.
- **The two prototypes are the approved UI reference** (real data, private,
  never copy their *data* into the repo). Absolute paths on this machine:
  - Board: `/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.scratch/stock-analysis-web-app/prototypes/06-zone-board/`
  - Timeline: `/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.scratch/stock-analysis-web-app/prototypes/07-thesis-timeline/`
  Their `template.html` files contain the exact CSS/JS the user approved.
  Porting them (Tasks 10–11) means copying code *you* (the project) wrote,
  minus the rejected variants — it is not a placeholder shortcut. Do **not**
  copy `data.json` or screenshots.
- **Vocabulary single-source:** enums live in `scripts/validate_records.py`
  and are pinned by `tests/test_decision_records.py` string-match tests
  against `skills/analyzing-stocks/references/decision-records.md` and
  `skills/investment-decision-workflow/SKILL.md`. Task 1 touches all four in
  one commit or the suite goes red.
- **`MODE_PRIORITY` in `validate_records.py` is rank-ascending**
  (`position-review: 0` is highest). Same-day double records: the **min**
  priority value wins band attribution.

## File structure

```
scripts/export_web.py          # vault → web-export/v1 JSON (Tasks 2–8)
scripts/build_webapp.py        # JSON → static site (Tasks 9–12)
scripts/make_demo_vault.py     # seeded fictional vault generator (Task 13)
webapp/assets/echarts.min.js   # vendored 5.6.0 (Task 9)
webapp/assets/NOTICE.md        # ECharts provenance + license note (Task 9)
webapp/templates/board.html    # ported 06 variant A (Task 10)
webapp/templates/symbol.html   # ported 07 variant B (Task 11)
demo/state-home/               # committed fictional vault (Task 13)
demo/prices.yaml               # committed synthetic closes+splits (Task 13)
tests/fixtures/webapp-home/    # fixture vault (Task 2)
tests/fixtures/webapp-prices.yaml
tests/test_export_web.py
tests/test_build_webapp.py
.github/workflows/deploy-demo.yml  # Task 14
```

---

### Task 1: Vocabulary patches — `Missing Inputs` zone + `JP` market

Real vault records already carry `valuation_zone: Missing Inputs` and a
`JP` market symbol (`NNNN.T`); the validator enums are behind reality
(design doc, contract patches 1–2).

**Files:**
- Modify: `scripts/validate_records.py:34` (VALUATION_ZONES), `:51-57`
  (SYMBOL_PATTERNS)
- Modify: `skills/analyzing-stocks/references/decision-records.md:79` (market
  comment), `:135` (zone vocabulary line)
- Modify: `skills/investment-decision-workflow/SKILL.md:346`
- Modify: `tests/test_decision_records.py:53` (pinned string)
- Test: `tests/test_decision_records.py` (add cases near the existing
  vocabulary tests)

- [ ] **Step 1: Write the failing tests**

In `tests/test_decision_records.py`, find the record-builder helper (`:133`,
`def record(... symbol: str, market: str ...)`) and the Checker acceptance
tests that use it. Add to the same class:

```python
    def test_missing_inputs_zone_is_legal(self) -> None:
        # Real vault records carry this fifth value (web-app design, patch 1).
        self.assertIn("Missing Inputs", vr.VALUATION_ZONES)

    def test_jp_market_symbol_is_canonical(self) -> None:
        # Real vault contains a JP record (web-app design, patch 2).
        self.assertTrue(vr.SYMBOL_PATTERNS["JP"].match("6501.T"))
        self.assertFalse(vr.SYMBOL_PATTERNS["JP"].match("65010.T"))
        self.assertFalse(vr.SYMBOL_PATTERNS["JP"].match("ABCD.T"))
```

(`vr` is the module's existing import alias for `validate_records`; if the
file imports it under another name, match that name.)

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_decision_records -v`
Expected: the two new tests FAIL (`'Missing Inputs' not found`, `KeyError:
'JP'`); everything else passes.

- [ ] **Step 3: Implement**

`scripts/validate_records.py`:

```python
VALUATION_ZONES = ("Accumulation", "Hold", "Exhaustion", "Invalidation",
                   "Missing Inputs")
```

```python
SYMBOL_PATTERNS = {
    "US": re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,2})?$"),
    "HK": re.compile(r"^\d{4,5}\.HK$"),
    "CN": re.compile(r"^\d{6}\.(SH|SZ|BJ)$"),
    "KR": re.compile(r"^\d{6}\.(KS|KQ)$"),
    "AU": re.compile(r"^[A-Z0-9]{1,6}\.AX$"),
    "JP": re.compile(r"^\d{4}\.T$"),
}
```

`skills/analyzing-stocks/references/decision-records.md`: line 79 comment
becomes `US                    # US | CN | HK | KR | AU | JP`; line 135
becomes:

```
  - `valuation_zone`: `Accumulation / Hold / Exhaustion / Invalidation / Missing Inputs` (workflow)
```

`skills/investment-decision-workflow/SKILL.md:346`:

```
- `Valuation Zone`: `Accumulation / Hold / Exhaustion / Invalidation / Missing Inputs`
```

`tests/test_decision_records.py:53`:

```python
        expected = "`Accumulation / Hold / Exhaustion / Invalidation / Missing Inputs`"
```

- [ ] **Step 4: Run the full suite**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: PASS. If any other test string-pins the old vocab or market list,
`grep -rn "Exhaustion / Invalidation" tests/ skills/` and update the pin the
same way.

- [ ] **Step 5: Verify against the real vault (manual sanity)**

Run: `.venv/bin/python scripts/validate_records.py`
Expected: the previously-failing `Missing Inputs` / JP records now validate
(or at minimum, no *new* errors versus a pre-change run).

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_records.py skills/analyzing-stocks/references/decision-records.md skills/investment-decision-workflow/SKILL.md tests/test_decision_records.py
git commit -m "feat(vocab): add Missing Inputs valuation zone and JP market (web-app patches 1-2)"
```

---

### Task 2: Exporter skeleton — fixture vault, record/ghost/action loading

**Files:**
- Create: `scripts/export_web.py`
- Create: `tests/fixtures/webapp-home/` (fixture vault below)
- Create: `tests/test_export_web.py`

- [ ] **Step 1: Create the fixture vault**

`tests/fixtures/webapp-home/portfolio.yaml`:

```yaml
holdings:
  - symbol: ACME
    qty: 40
    avg_cost: 59.0
    currency: USD
option_legs:
  - kind: cash-secured-put
    underlying: ACME
    strike: 64
    expiry: 2026-09-10
    qty: -1
    multiplier: 100
```

`tests/fixtures/webapp-home/records/ACME/2026-03-02-new-idea.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-03-02
mode: new-idea
price_at_decision: 100.0
currency: USD
stance: Buy
review_by: 2026-06-01
next_earnings: 2026-08-20
weighted_fair_value: 150.0
scenarios: {bear: 80.0, base: 150.0, bull: 200.0}
scenario_probabilities: {bear: 0.25, base: 0.5, bull: 0.25}
position_size: Starter
confidence: Medium
candidate_tier: Core Candidate
valuation_zone: Accumulation
execution_method: Stage buy
triggers:
  add_on:
    - {type: price, level: 140.0, direction: below}
  trim_exit:
    - {type: price, level: 190.0, direction: above}
source_report: ../../reports/2026-03-02-acme-initiation.md
---

ACME initial thesis: category leader entering an accumulation window. Body
line two for the summary extractor.
```

`tests/fixtures/webapp-home/records/ACME/2026-06-20-position-review.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-06-20
mode: position-review
price_at_decision: 120.0
currency: USD
stance: Hold
review_by: 2026-12-01
weighted_fair_value: 160.0
scenarios: {bear: 90.0, base: 160.0, bull: 210.0}
position_size: Starter
confidence: Medium
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: No Action
triggers:
  add_on:
    - {type: price, level: 100.0, direction: below}
action_taken: {action: added, date: 2026-06-20, instrument: shares, note: topped up}
source_report: ../../reports/2026-06-20-basket.md
---

Position review after the run-up; thesis intact, valuation now fair.
```

`tests/fixtures/webapp-home/records/ACME/2026-06-20-event-review.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-06-20
mode: event-review
price_at_decision: 121.0
currency: USD
stance: Hold
review_by: 2026-12-01
weighted_fair_value: 160.0
scenarios: {bear: 90.0, base: 160.0, bull: 210.0}
position_size: Starter
confidence: Medium
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: No Action
triggers:
  add_on:
    - {type: price, level: 100.0, direction: below}
---

Same-day event note: guidance reaffirmed, no change to the review stance.
```

`tests/fixtures/webapp-home/records/ACME/INDEX.md`:

```markdown
# ACME — decision index

| date | mode | stance | zone | wfv | price | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-11-10 | historical | Hold | — | — | — | — | [pre-record thesis](../../reports/2025-11-10-acme-history.md) |
| 2026-03-02 | new-idea | Buy | Accumulation | 150.0 | 100.0 | [record](2026-03-02-new-idea.md) | [report](../../reports/2026-03-02-acme-initiation.md) |
| 2026-06-20 | position-review | Hold | Hold | 160.0 | 120.0 | [record](2026-06-20-position-review.md) | [report](../../reports/2026-06-20-basket.md) |
| 2026-06-20 | event-review | Hold | Hold | 160.0 | 121.0 | [record](2026-06-20-event-review.md) | — |
```

`tests/fixtures/webapp-home/records/BOLT/2026-07-15-research.md` (the
`Missing Inputs` / no-valuation-group card):

```markdown
---
schema: decision-record/v1
symbol: BOLT
market: US
date: 2026-07-15
mode: research
price_at_decision: 42.0
currency: USD
stance: Hold
review_by: 2026-10-15
candidate_tier: Tactical Candidate
valuation_zone: Missing Inputs
execution_method: Wait
triggers:
  add_on:
    - {type: event, description: next 10-Q segment disclosure}
---

Position data unavailable at decision time; zone recorded as Missing Inputs.
```

`tests/fixtures/webapp-home/records/BOLT/INDEX.md`:

```markdown
# BOLT — decision index

| date | mode | stance | zone | wfv | price | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-15 | research | Hold | Missing Inputs | — | 42.0 | [record](2026-07-15-research.md) | — |
```

`tests/fixtures/webapp-home/records/7203.T/2026-07-01-new-idea.md` (JP path;
same frontmatter shape as ACME's new-idea with: symbol `7203.T`, market `JP`,
currency `JPY`, price_at_decision `2500.0`, wfv `3200.0`, scenarios
`{bear: 2000.0, base: 3200.0, bull: 4000.0}`, stance `Buy`, review_by
`2026-12-01`, zone `Accumulation`, candidate_tier `Core Candidate`,
execution_method `Stage buy`, triggers add_on price `2200.0` below, no
source_report, body `JP market coverage record.`) and a matching
`records/7203.T/INDEX.md` single-row index.

`tests/fixtures/webapp-home/records/GONE/2026-05-10-existing-report.md` (the
no-price card; frontmatter shape as ACME's new-idea with: symbol `GONE`,
market `US`, currency `USD`, date `2026-05-10`, mode `existing-report`,
price_at_decision `10.0`, wfv `18.0`, scenarios `{bear: 6.0, base: 18.0,
bull: 25.0}`, stance `Hold`, review_by `2026-11-01`, zone `Accumulation`,
candidate_tier `Tactical Candidate`, execution_method `Wait`, triggers
add_on price `8.0` below, body `Delisted-from-provider fixture.`) plus its
single-row `INDEX.md`.

`tests/fixtures/webapp-home/reports/2026-03-02-acme-initiation.md`:

```markdown
# ACME Initiation — Deep Dive

## 1. Business

Body of block one.

## 2. Valuation

| item | value |
| --- | --- |
| WFV | 150 |
```

`tests/fixtures/webapp-home/reports/2026-06-20-basket.md` (basket report —
note the h1 *title* contains "ACME" on purpose, to pin the
title-block-exclusion rule):

```markdown
# ACME & BOLT — Basket Re-Evaluation

Preamble paragraph.

# Part I — ACME

ACME part body.

# Part II — BOLT (Bolt Industries)

BOLT part body.
```

`tests/fixtures/webapp-home/reports/2025-11-10-acme-history.md`:

```markdown
# ACME Pre-Record History

Ghost-era thesis text.
```

- [ ] **Step 2: Write the failing tests**

`tests/test_export_web.py`:

```python
import datetime
import json
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import export_web as ew  # noqa: E402

FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "webapp-home"
PRICES = REPO_ROOT / "tests" / "fixtures" / "webapp-prices.yaml"
AS_OF = datetime.date(2026, 8, 11)

D = datetime.date


class LoadingTests(unittest.TestCase):
    def test_loads_all_records_per_symbol_in_chain_order(self):
        recs = ew.load_symbol_records(FIXTURE_HOME, "ACME")
        self.assertEqual([r["_file"] for r in recs], [
            "2026-03-02-new-idea.md",
            "2026-06-20-position-review.md",
            "2026-06-20-event-review.md",
        ])
        self.assertIn("initial thesis", recs[0]["_body"])

    def test_ghost_rows_come_from_index_only(self):
        ghosts = ew.load_ghost_rows(FIXTURE_HOME / "records" / "ACME" / "INDEX.md")
        self.assertEqual(len(ghosts), 1)
        self.assertEqual(ghosts[0]["date"], "2025-11-10")
        self.assertEqual(ghosts[0]["mode"], "historical")
        self.assertTrue(ghosts[0]["reports"][0]["path"].endswith(
            "2025-11-10-acme-history.md"))

    def test_actions_extracted_with_record_date(self):
        recs = ew.load_symbol_records(FIXTURE_HOME, "ACME")
        actions = ew.extract_actions(recs)
        self.assertEqual(actions, [{
            "date": "2026-06-20", "action": "added", "instrument": "shares",
            "note": "topped up", "record_date": "2026-06-20"}])

    def test_same_day_band_attribution_prefers_position_review(self):
        recs = ew.load_symbol_records(FIXTURE_HOME, "ACME")
        winner = ew.band_record_for_date(recs, D(2026, 6, 20))
        self.assertEqual(winner["mode"], "position-review")

    def test_symbol_universe_is_every_records_dir(self):
        self.assertEqual(ew.list_symbols(FIXTURE_HOME),
                         ["7203.T", "ACME", "BOLT", "GONE"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: FAIL at import (`No module named export_web`).

- [ ] **Step 4: Implement the loading layer**

Create `scripts/export_web.py`:

```python
#!/usr/bin/env python3
"""Web-app export: vault -> web-export/v1 JSON dataset.

Design:   docs/plans/2026-08-11-web-app-design.md
Contract: read-only projection; zones are recorded values, never recomputed;
all mechanical signals are computed here so the frontend holds zero judgment
logic. Heavy deps (markdown, yfinance, akshare, requests) are imported lazily
so the pyyaml-only test job stays dependency-free.

Exit codes: 0 clean run, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("export_web.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

from validate_records import (  # noqa: E402
    FRONTMATTER,
    MODE_PRIORITY,
    SYMBOL_PATTERNS,
    as_date,
    is_number,
    resolve_home,
)
import outcome_score as osc  # noqa: E402

SCHEMA = "web-export/v1"
PRICE_BASIS = "current share basis (split-adjusted, ex-dividend)"
WINDOWS = osc.WINDOWS_DEFAULT
PUT_MONEYNESS = 1.05   # short-put badge: spot <= strike * this ...
PUT_DTE = 45           # ... and 0 <= days-to-expiry <= this
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


# ----------------------------- vault loading -----------------------------

def list_symbols(home: Path) -> "list[str]":
    root = home / "records"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def load_symbol_records(home: Path, symbol: str) -> "list[dict]":
    """Every decision-record/v1 for one symbol, chain-ordered
    (date ascending, then MODE_PRIORITY rank so position-review leads a
    same-day pair), with `_body` (markdown after frontmatter) and `_file`."""
    records = []
    for path in sorted((home / "records" / symbol).glob("*.md")):
        if path.name == "INDEX.md":
            continue
        text = path.read_text(encoding="utf-8-sig")
        match = FRONTMATTER.match(text)
        if not match:
            continue
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict) or meta.get("schema") != "decision-record/v1":
            continue
        meta["_body"] = text[match.end():]
        meta["_file"] = path.name
        records.append(meta)
    records.sort(key=lambda m: (str(m.get("date")),
                                MODE_PRIORITY.get(m.get("mode"), 99)))
    return records


def load_ghost_rows(index_path: Path) -> "list[dict]":
    """INDEX.md rows with no record link (historical / context pre-history)."""
    ghosts = []
    if not index_path.exists():
        return ghosts
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8 or cells[0] == "date":
            continue
        date, mode, record_cell, report_cell = cells[0], cells[1], cells[6], cells[7]
        if _LINK.search(record_cell):
            continue  # a real record row; the file itself is the source
        reports = [{"title": title,
                    "path": str((index_path.parent / rel).resolve())}
                   for title, rel in
                   _LINK.findall(report_cell) + _LINK.findall(record_cell)]
        if reports:
            ghosts.append({"date": date, "mode": mode, "reports": reports})
    return ghosts


def extract_actions(records: "list[dict]") -> "list[dict]":
    actions = []
    for meta in records:
        taken = meta.get("action_taken")
        if isinstance(taken, dict) and taken.get("action"):
            actions.append({
                "date": str(taken.get("date")), "action": taken.get("action"),
                "instrument": taken.get("instrument"), "note": taken.get("note"),
                "record_date": str(meta.get("date")),
            })
    return actions


def band_record_for_date(records: "list[dict]", day: datetime.date) -> "dict | None":
    """Same-day double records: min MODE_PRIORITY rank (position-review) wins."""
    same_day = [m for m in records if as_date(m.get("date")) == day]
    if not same_day:
        return None
    return min(same_day, key=lambda m: MODE_PRIORITY.get(m.get("mode"), 99))


def load_portfolio(home: Path) -> "tuple[dict, dict]":
    path = home / "portfolio.yaml"
    if not path.exists():
        return {}, {}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    holdings = {h["symbol"]: h for h in doc.get("holdings") or []
                if isinstance(h, dict) and (h.get("qty") or 0) > 0}
    legs: "dict[str, list]" = {}
    for leg in doc.get("option_legs") or []:
        if isinstance(leg, dict) and leg.get("underlying"):
            legs.setdefault(leg["underlying"], []).append(leg)
    return holdings, legs
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add scripts/export_web.py tests/test_export_web.py tests/fixtures/webapp-home
git commit -m "feat(webapp): export_web loading layer + fixture vault"
```

---

### Task 3: Mechanical signals + board card assembly

**Files:**
- Modify: `scripts/export_web.py` (append)
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Write the failing tests** (append to `tests/test_export_web.py`)

```python
class CardSignalTests(unittest.TestCase):
    def setUp(self):
        self.holdings, self.legs = ew.load_portfolio(FIXTURE_HOME)
        self.meta = ew.load_symbol_records(FIXTURE_HOME, "ACME")[1]
        self.assertEqual(self.meta["mode"], "position-review")

    def _card(self, price=66.0, factor=2.0, **kw):
        args = dict(price=price, price_as_of="2026-08-10", price_stale=False,
                    no_price_reason=None, factor=factor,
                    holdings=self.holdings, legs=self.legs, today=AS_OF)
        args.update(kw)
        return ew.build_card("ACME", self.meta, **args)

    def test_adjusted_ruler_and_cursor(self):
        card = self._card()
        # raw 90/160/210 wfv 160 at factor 2 -> 45/80/105 wfv 80
        self.assertEqual((card["bear"], card["base"], card["bull"], card["wfv"]),
                         (45.0, 80.0, 105.0, 80.0))
        self.assertAlmostEqual(card["cursor"], (66.0 - 45.0) / 60.0)

    def test_discount_is_price_over_wfv_minus_one(self):
        self.assertAlmostEqual(self._card()["discount"], 66.0 / 80.0 - 1.0)

    def test_trigger_touch_adjusted(self):
        # add_on 100 below -> adjusted 50; price 66 > 50 -> not touched
        self.assertEqual(self._card()["triggers_touched"], [])
        touched = self._card(price=49.0)["triggers_touched"]
        self.assertEqual([(t["group"], t["level"]) for t in touched],
                         [("add_on", 50.0)])

    def test_scenario_breach_below_bear(self):
        self.assertIsNone(self._card()["scenario_breach"])
        self.assertEqual(self._card(price=44.0)["scenario_breach"], "below_bear")
        self.assertEqual(self._card(price=106.0)["scenario_breach"], "above_bull")

    def test_stale_days_zero_when_review_by_future(self):
        self.assertEqual(self._card()["stale_days"], 0)  # review_by 2026-12-01

    def test_drawdown_vs_adjusted_decision_price(self):
        # price_at_decision 120 raw -> 60 adjusted; 66/60 - 1 = +10%
        self.assertAlmostEqual(self._card()["drawdown"], 0.10)

    def test_badges_held_and_put_risk(self):
        card = self._card()
        self.assertTrue(card["held"])
        self.assertEqual(card["qty"], 40)
        self.assertEqual(card["option_legs"], 1)
        # spot 66 <= 64 * 1.05 = 67.2 and expiry 2026-09-10 is 30 DTE
        self.assertTrue(card["put_assignment_risk"])
        self.assertFalse(self._card(price=70.0)["put_assignment_risk"])

    def test_stale_and_earnings_on_new_idea(self):
        meta = ew.load_symbol_records(FIXTURE_HOME, "ACME")[0]
        card = ew.build_card("ACME", meta, price=66.0, price_as_of="2026-08-10",
                             price_stale=False, no_price_reason=None, factor=2.0,
                             holdings=self.holdings, legs=self.legs, today=AS_OF)
        self.assertEqual(card["stale_days"], (AS_OF - D(2026, 6, 1)).days)
        self.assertEqual(card["earnings_in"], 9)  # 2026-08-20

    def test_no_price_card_degrades(self):
        card = ew.build_card("ACME", self.meta, price=None, price_as_of=None,
                             price_stale=False, no_price_reason="no data from provider",
                             factor=2.0, holdings=self.holdings, legs=self.legs,
                             today=AS_OF)
        self.assertIsNone(card["cursor"])
        self.assertIsNone(card["discount"])
        self.assertIsNone(card["drawdown"])
        self.assertEqual(card["triggers_touched"], [])
        self.assertEqual(card["no_price_reason"], "no data from provider")

    def test_missing_valuation_group_card(self):
        meta = ew.load_symbol_records(FIXTURE_HOME, "BOLT")[0]
        card = ew.build_card("BOLT", meta, price=41.0, price_as_of="2026-08-10",
                             price_stale=False, no_price_reason=None, factor=1.0,
                             holdings={}, legs={}, today=AS_OF)
        self.assertEqual(card["valuation_zone"], "Missing Inputs")
        self.assertIsNone(card["wfv"])
        self.assertIsNone(card["cursor"])
        self.assertIsNone(card["discount"])
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.CardSignalTests -v`
Expected: FAIL (`build_card` not defined).

- [ ] **Step 3: Implement** (append to `scripts/export_web.py`)

```python
# ----------------------------- mechanical signals -----------------------------

def _adj(value, factor):
    return round(float(value) / factor, 4) if is_number(value) else None


def price_triggers(meta: dict, factor: float) -> "list[dict]":
    out = []
    for group in ("add_on", "trim_exit"):
        for trig in (meta.get("triggers") or {}).get(group) or []:
            if isinstance(trig, dict) and trig.get("type") == "price" \
                    and is_number(trig.get("level")):
                out.append({"group": group, "level": _adj(trig["level"], factor),
                            "direction": trig.get("direction")})
    return out


def build_card(symbol: str, meta: dict, *, price, price_as_of, price_stale,
               no_price_reason, factor, holdings, legs, today) -> dict:
    """One Zone Board card. All numbers on the current share basis."""
    scen = meta.get("scenarios") or {}
    bear, base, bull = (_adj(scen.get(k), factor) for k in ("bear", "base", "bull"))
    wfv = _adj(meta.get("weighted_fair_value"), factor)
    p_dec = _adj(meta.get("price_at_decision"), factor)

    cursor = discount = drawdown = None
    breach = None
    touched: "list[dict]" = []
    if price is not None:
        if bear is not None and bull is not None and bull != bear:
            cursor = (price - bear) / (bull - bear)
        if wfv:
            discount = price / wfv - 1.0
        if p_dec:
            drawdown = price / p_dec - 1.0
        for trig in price_triggers(meta, factor):
            hit = (trig["direction"] == "below" and price <= trig["level"]) or \
                  (trig["direction"] == "above" and price >= trig["level"])
            if hit:
                touched.append(trig)
        if bear is not None and price < bear:
            breach = "below_bear"
        elif bull is not None and price > bull:
            breach = "above_bull"

    review_by = as_date(meta.get("review_by")) if meta.get("review_by") else None
    stale_days = (today - review_by).days if review_by and review_by < today else 0

    nxt = as_date(meta.get("next_earnings")) if meta.get("next_earnings") else None
    earnings_in = (nxt - today).days if nxt and nxt >= today else None

    holding = holdings.get(symbol)
    symbol_legs = legs.get(symbol) or []
    put_risk = False
    for leg in symbol_legs:
        if leg.get("kind") != "cash-secured-put" or price is None:
            continue
        strike = leg.get("strike")
        expiry = as_date(leg.get("expiry")) if leg.get("expiry") else None
        if not is_number(strike) or expiry is None:
            continue
        dte = (expiry - today).days
        if 0 <= dte <= PUT_DTE and price <= float(strike) * PUT_MONEYNESS:
            put_risk = True

    return {
        "symbol": symbol, "market": meta.get("market"),
        "currency": meta.get("currency"),
        "record_date": str(meta.get("date")), "mode": meta.get("mode"),
        "stance": meta.get("stance"), "confidence": meta.get("confidence"),
        "position_size": meta.get("position_size"),
        "valuation_zone": meta.get("valuation_zone"),
        "wfv": wfv, "bear": bear, "base": base, "bull": bull,
        "price": price, "price_as_of": price_as_of, "price_stale": price_stale,
        "no_price_reason": no_price_reason,
        "price_at_decision": p_dec, "split_factor": factor,
        "cursor": cursor, "discount": discount,
        "triggers_touched": touched, "scenario_breach": breach,
        "stale_days": stale_days, "review_by": str(meta.get("review_by")),
        "earnings_in": earnings_in,
        "next_earnings": str(nxt) if nxt else None,
        "drawdown": drawdown,
        "held": bool(holding), "qty": (holding or {}).get("qty"),
        "avg_cost": (holding or {}).get("avg_cost"),
        "option_legs": len(symbol_legs), "put_assignment_risk": put_risk,
    }
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/export_web.py tests/test_export_web.py
git commit -m "feat(webapp): mechanical signals + zone board card builder"
```

---

### Task 4: History provider seam — file provider, split factors, provider symbols

**Files:**
- Modify: `scripts/export_web.py` (append)
- Create: `tests/fixtures/webapp-prices.yaml`
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Create the prices fixture**

`tests/fixtures/webapp-prices.yaml` — **raw nominal** closes; ACME has a 2:1
split on 2026-07-01 so pre-split closes are ~2x scale:

```yaml
ACME:
  splits:
    - [2026-07-01, 2.0]
  closes:
    2026-03-02: 100.0
    2026-05-29: 130.0
    2026-06-20: 120.0
    2026-06-30: 132.0
    2026-07-01: 67.0
    2026-08-10: 66.0
BOLT:
  splits: []
  closes:
    2026-07-15: 42.0
    2026-08-10: 41.0
7203.T:
  splits: []
  closes:
    2026-07-01: 2500.0
    2026-08-08: 2800.0
```

(No `GONE` key → its no-price state.)

- [ ] **Step 2: Write the failing tests** (append)

```python
class HistoryProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = ew.FileHistoryProvider(PRICES)

    def test_series_and_as_of(self):
        series = self.provider.series("ACME")
        self.assertEqual(series[D(2026, 8, 10)], 66.0)
        self.assertEqual(self.provider.as_of("ACME"), D(2026, 8, 10))

    def test_splits_parsed(self):
        self.assertEqual(self.provider.splits("ACME"), [(D(2026, 7, 1), 2.0)])
        self.assertEqual(self.provider.splits("BOLT"), [])

    def test_unknown_symbol_is_empty(self):
        self.assertEqual(self.provider.series("GONE"), {})
        self.assertIsNone(self.provider.as_of("GONE"))


class SplitFactorTests(unittest.TestCase):
    SPLITS = [(D(2026, 7, 1), 2.0)]

    def test_factor_before_split_is_ratio(self):
        self.assertEqual(ew.factor_for(self.SPLITS, D(2026, 6, 20)), 2.0)

    def test_factor_on_or_after_ex_date_is_one(self):
        self.assertEqual(ew.factor_for(self.SPLITS, D(2026, 7, 1)), 1.0)

    def test_factor_none_when_splits_unknown(self):
        self.assertIsNone(ew.factor_for(None, D(2026, 6, 20)))

    def test_adjusted_series_is_continuous(self):
        provider = ew.FileHistoryProvider(PRICES)
        dates, closes = ew.adjusted_series(provider.series("ACME"),
                                           provider.splits("ACME"))
        by_date = dict(zip(dates, closes))
        self.assertEqual(by_date["2026-06-30"], 66.0)   # 132 / 2
        self.assertEqual(by_date["2026-07-01"], 67.0)   # post-split, factor 1


class ProviderSymbolTests(unittest.TestCase):
    def test_us_dot_class_maps_to_dash(self):
        self.assertEqual(ew.provider_symbol("BRK.B", "US"), "BRK-B")

    def test_hk_five_digit_strips_leading_zero(self):
        self.assertEqual(ew.provider_symbol("02513.HK", "HK"), "2513.HK")

    def test_jp_kr_au_pass_through(self):
        self.assertEqual(ew.provider_symbol("7203.T", "JP"), "7203.T")
        self.assertEqual(ew.provider_symbol("000660.KS", "KR"), "000660.KS")
        self.assertEqual(ew.provider_symbol("RGL.AX", "AU"), "RGL.AX")
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.HistoryProviderTests tests.test_export_web.SplitFactorTests tests.test_export_web.ProviderSymbolTests -v`
Expected: FAIL (names not defined).

- [ ] **Step 4: Implement** (append to `scripts/export_web.py`)

```python
# ----------------------------- price history -----------------------------
# A provider serves RAW nominal closes plus split events; adjustment to the
# current share basis happens at export time (factor_for / adjusted_series),
# so cached nominal history stays valid across future splits.

def factor_for(splits, day: datetime.date) -> "float | None":
    """Cumulative split factor from `day` to today. None = splits unknown
    (degrade to explicit warning, never silently unadjusted)."""
    if splits is None:
        return None
    factor = 1.0
    for ex_date, ratio in splits:
        if ex_date > day and ratio:
            factor *= float(ratio)
    return factor


def adjusted_series(series: "dict[datetime.date, float]", splits):
    """(dates, closes) ISO-sorted, divided by each date's forward factor."""
    dates, closes = [], []
    for day in sorted(series):
        factor = factor_for(splits, day) or 1.0
        dates.append(day.isoformat())
        closes.append(round(series[day] / factor, 4))
    return dates, closes


def provider_symbol(symbol: str, market: str) -> str:
    """Canonical vault symbol -> yfinance symbol (CN goes to akshare via
    morning_check.provider_for and never hits this normalization)."""
    if market == "US":
        return symbol.replace(".", "-")
    if market == "HK":
        code, suffix = symbol.split(".")
        return code.lstrip("0").zfill(4) + "." + suffix
    return symbol


class FileHistoryProvider:
    """{SYM: {closes: {date: close}, splits: [[date, ratio]]}} YAML/JSON file.
    Offline runs, tests, and the frozen demo dataset."""

    def __init__(self, path) -> None:
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        self._series: "dict[str, dict]" = {}
        self._splits: "dict[str, list]" = {}
        for symbol, entry in doc.items():
            closes = (entry or {}).get("closes") or {}
            self._series[symbol] = {as_date(d): float(v) for d, v in closes.items()}
            self._splits[symbol] = [(as_date(d), float(r))
                                    for d, r in (entry or {}).get("splits") or []]

    def series(self, symbol: str) -> "dict[datetime.date, float]":
        return self._series.get(symbol) or {}

    def splits(self, symbol: str) -> "list | None":
        return self._splits.get(symbol, [])

    def as_of(self, symbol: str) -> "datetime.date | None":
        series = self.series(symbol)
        return max(series) if series else None

    def stale(self, symbol: str) -> bool:
        return False

    def failure_reason(self, symbol: str) -> "str | None":
        return None if self.series(symbol) else "no data from provider"
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/export_web.py tests/test_export_web.py tests/fixtures/webapp-prices.yaml
git commit -m "feat(webapp): history provider seam, split-factor adjustment, provider symbols"
```

---

### Task 5: Live provider with incremental cache + stale fallback

**Files:**
- Modify: `scripts/export_web.py` (append)
- Modify: `.gitignore` (add cache + output dirs)
- Test: `tests/test_export_web.py` (append)

The live provider is unit-tested by injecting a fake fetch function — no
network in the main suite; one network-gated smoke test at the end.

- [ ] **Step 1: Write the failing tests** (append)

```python
class _FakeFetch:
    """Stands in for LiveHistoryProvider._fetch(symbol, market, start)."""

    def __init__(self, result=None, error=False):
        self.result, self.error, self.calls = result, error, []

    def __call__(self, symbol, market, start):
        self.calls.append((symbol, market, start))
        if self.error:
            raise RuntimeError("provider down")
        return self.result


class LiveCacheTests(unittest.TestCase):
    def _provider(self, tmp_name, fetch, today=AS_OF):
        cache = pathlib.Path(self.cache_dir.name) / tmp_name
        return ew.LiveHistoryProvider(cache_path=cache, fetch=fetch, today=today)

    def setUp(self):
        import tempfile
        self.cache_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.cache_dir.cleanup)

    def test_fresh_fetch_populates_cache(self):
        fetch = _FakeFetch(result=({D(2026, 8, 7): 10.0, D(2026, 8, 10): 11.0},
                                   [(D(2026, 1, 2), 2.0)]))
        provider = self._provider("c1.json", fetch)
        provider.load("ACME", "US")
        self.assertEqual(provider.series("ACME")[D(2026, 8, 10)], 11.0)
        self.assertEqual(provider.splits("ACME"), [(D(2026, 1, 2), 2.0)])
        self.assertFalse(provider.stale("ACME"))
        # cache written
        provider2 = self._provider("c1.json", _FakeFetch(error=True))
        provider2.load("ACME", "US")
        self.assertEqual(provider2.series("ACME")[D(2026, 8, 10)], 11.0)

    def test_incremental_fetch_starts_near_cache_tail(self):
        fetch = _FakeFetch(result=({D(2026, 8, 10): 11.0}, []))
        provider = self._provider("c2.json", fetch)
        provider._cache["symbols"]["ACME"] = {
            "closes": {"2026-08-01": 9.5}, "splits": [],
            "fetched_through": "2026-08-05"}
        provider.load("ACME", "US")
        # start = fetched_through - overlap, not 5 years ago
        self.assertGreaterEqual(fetch.calls[0][2], D(2026, 7, 29))
        self.assertEqual(provider.series("ACME")[D(2026, 8, 1)], 9.5)

    def test_failed_fetch_serves_cache_and_marks_stale(self):
        provider = self._provider("c3.json", _FakeFetch(error=True))
        provider._cache["symbols"]["ACME"] = {
            "closes": {"2026-08-01": 9.5}, "splits": [],
            "fetched_through": "2026-08-05"}
        provider.load("ACME", "US")
        self.assertTrue(provider.stale("ACME"))
        self.assertEqual(provider.as_of("ACME"), D(2026, 8, 1))

    def test_failed_fetch_no_cache_is_no_price(self):
        provider = self._provider("c4.json", _FakeFetch(error=True))
        provider.load("GONE", "US")
        self.assertEqual(provider.series("GONE"), {})
        self.assertIsNotNone(provider.failure_reason("GONE"))

    def test_schema_mismatched_cache_is_discarded(self):
        cache = pathlib.Path(self.cache_dir.name) / "c5.json"
        cache.write_text(json.dumps({"schema": "web-export/v0", "symbols": {
            "ACME": {"closes": {"2026-08-01": 9.5}, "splits": [],
                     "fetched_through": "2026-08-05"}}}), encoding="utf-8")
        provider = ew.LiveHistoryProvider(cache_path=cache,
                                          fetch=_FakeFetch(error=True), today=AS_OF)
        provider.load("ACME", "US")
        self.assertEqual(provider.series("ACME"), {})  # old cache refused
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.LiveCacheTests -v`
Expected: FAIL (`LiveHistoryProvider` not defined).

- [ ] **Step 3: Implement** (append to `scripts/export_web.py`)

```python
CACHE_OVERLAP_DAYS = 7
HISTORY_YEARS = 5


def _default_fetch(symbol: str, market: str, start: datetime.date):
    """Live fetch: (series {date: close}, splits [(date, ratio)] | None).
    yfinance for every market except CN A-shares (akshare). Heavy imports stay
    inside. Raises on provider failure — caller handles fallback."""
    if SYMBOL_PATTERNS["CN"].match(symbol):
        import akshare as ak

        code = symbol.split(".")[0]
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start.strftime("%Y%m%d"),
                                end_date=datetime.date.today().strftime("%Y%m%d"),
                                adjust="")  # fqt=0 nominal; fqt=1 (qfq) is banned
        series = {as_date(str(row["日期"])[:10]): float(row["收盘"])
                  for _, row in df.iterrows()}
        splits = _cn_splits(code)
        return series, splits
    import yfinance as yf

    ticker = yf.Ticker(provider_symbol(symbol, market))
    hist = ticker.history(start=start.isoformat(), auto_adjust=False)
    series = {}
    for ts, row in hist.iterrows():
        close = row.get("Close")
        if close is not None and close == close:  # NaN guard
            series[ts.date()] = float(close)
    try:
        splits = [(d.date(), float(r)) for d, r in ticker.splits.items()
                  if float(r) > 0]
    except Exception:
        splits = None  # factor unknown -> explicit warning downstream
    return series, splits


def _cn_splits(code: str):
    """CN share-expansion factor events from eastmoney 分红送配 via akshare:
    ratio = 1 + (送股 + 转增) / 10 per ex-date. Cash dividends are ignored on
    purpose (price basis excludes dividends). None on failure."""
    try:
        import akshare as ak

        df = ak.stock_fhps_detail_em(symbol=code)
        events = []
        for _, row in df.iterrows():
            ex = row.get("除权除息日")
            if ex is None or str(ex) in ("", "NaT", "nan"):
                continue
            send = float(row.get("送转股份-送股比例") or 0)
            bonus = float(row.get("送转股份-转股比例") or 0)
            if send or bonus:
                events.append((as_date(str(ex)[:10]), 1.0 + (send + bonus) / 10.0))
        return sorted(events)
    except Exception:
        return None


class LiveHistoryProvider:
    """Live daily history with a local incremental cache of RAW closes.

    Cache file: {"schema": SCHEMA, "symbols": {SYM: {"closes": {iso: px},
    "splits": [[iso, ratio]] | null, "fetched_through": iso}}}.
    A schema-mismatched cache is discarded (design: the generator refuses
    mismatched caches). Fetch failure falls back to cache and marks stale.
    """

    def __init__(self, cache_path: Path, fetch=_default_fetch, today=None) -> None:
        self._path = Path(cache_path)
        self._fetch = fetch
        self._today = today or datetime.date.today()
        self._cache = {"schema": SCHEMA, "symbols": {}}
        if self._path.exists():
            try:
                loaded = json.loads(self._path.read_text(encoding="utf-8"))
                if loaded.get("schema") == SCHEMA:
                    self._cache = loaded
            except (json.JSONDecodeError, OSError):
                pass
        self._stale: "set[str]" = set()
        self._failed: "dict[str, str]" = {}

    def _entry(self, symbol: str) -> dict:
        return self._cache["symbols"].setdefault(
            symbol, {"closes": {}, "splits": [], "fetched_through": None})

    def load(self, symbol: str, market: str) -> None:
        entry = self._entry(symbol)
        tail = entry.get("fetched_through")
        start = (as_date(tail) - datetime.timedelta(days=CACHE_OVERLAP_DAYS)
                 if tail else
                 self._today - datetime.timedelta(days=HISTORY_YEARS * 365))
        try:
            series, splits = self._fetch(symbol, market, start)
        except Exception as exc:
            if entry["closes"]:
                self._stale.add(symbol)
            else:
                self._failed[symbol] = f"fetch failed: {exc}"
            return
        if not series and not entry["closes"]:
            self._failed[symbol] = "no data from provider"
            return
        entry["closes"].update({d.isoformat(): px for d, px in series.items()})
        if splits is not None:
            entry["splits"] = [[d.isoformat(), r] for d, r in splits]
        else:
            entry["splits"] = None  # unknown -> factor_for returns None
        entry["fetched_through"] = self._today.isoformat()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache), encoding="utf-8")

    def series(self, symbol: str) -> "dict[datetime.date, float]":
        closes = self._entry(symbol)["closes"]
        return {as_date(d): float(px) for d, px in closes.items()}

    def splits(self, symbol: str) -> "list | None":
        raw = self._entry(symbol)["splits"]
        if raw is None:
            return None
        return sorted((as_date(d), float(r)) for d, r in raw)

    def as_of(self, symbol: str) -> "datetime.date | None":
        series = self.series(symbol)
        return max(series) if series else None

    def stale(self, symbol: str) -> bool:
        return symbol in self._stale

    def failure_reason(self, symbol: str) -> "str | None":
        return self._failed.get(symbol)
```

- [ ] **Step 4: Gitignore the cache and outputs**

Append to `.gitignore`:

```
.webapp_cache/
webapp_out/
webapp_demo_out/
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/export_web.py tests/test_export_web.py .gitignore
git commit -m "feat(webapp): live history provider with incremental cache + stale fallback"
```

---

### Task 6: Markdown rendering, block anchors, basket Part anchor

**Files:**
- Modify: `scripts/export_web.py` (append)
- Modify: `.github/workflows/ci.yml` (inflection job: add `markdown` +
  the export test file so CI exercises the renderer)
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Write the failing tests** (append)

```python
try:
    import markdown  # noqa: F401
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


@unittest.skipUnless(HAS_MARKDOWN, "markdown not installed (pyyaml-only job)")
class RenderTests(unittest.TestCase):
    def test_blocks_get_sequential_anchors(self):
        html, blocks = ew.render_md("# Part I — 深度\n\n## 估值\n\ntext\n")
        self.assertEqual([b["id"] for b in blocks], ["blk-0", "blk-1"])
        self.assertEqual([b["level"] for b in blocks], [1, 2])
        self.assertIn('<h1 id="blk-0">', html)
        self.assertIn('<h2 id="blk-1">', html)

    def test_tables_and_fences_render(self):
        html, _ = ew.render_md("| a | b |\n| --- | --- |\n| 1 | 2 |\n")
        self.assertIn("<table>", html)

    def test_part_anchor_skips_title_block(self):
        basket = (REPO_ROOT / "tests" / "fixtures" / "webapp-home" /
                  "reports" / "2026-06-20-basket.md").read_text(encoding="utf-8")
        _, blocks = ew.render_md(basket)
        # h1 title contains "ACME" but must NOT match; Part I must.
        self.assertEqual(ew.part_anchor(blocks, "ACME"), "blk-1")
        self.assertEqual(ew.part_anchor(blocks, "BOLT"), "blk-2")

    def test_part_anchor_none_without_part_structure(self):
        _, blocks = ew.render_md("# Single Report ACME\n\n## Block\n\nbody\n")
        self.assertIsNone(ew.part_anchor(blocks, "ACME"))
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.RenderTests -v`
Expected: FAIL (`render_md` not defined). If `markdown` is missing in the
venv, first run `uv add markdown` (adds to `pyproject.toml` dependencies) —
that edit is part of this task.

- [ ] **Step 3: Implement** (append to `scripts/export_web.py`)

```python
# ----------------------------- markdown rendering -----------------------------

_MD = None


def _get_md():
    """Lazy `markdown` import: export-path dependency only, so the pyyaml-only
    CI job never needs it (mirrors the yfinance/akshare pattern)."""
    global _MD
    if _MD is None:
        try:
            import markdown
        except ImportError:  # pragma: no cover
            print("export_web.py needs the 'markdown' package for report "
                  "rendering: uv add markdown", file=sys.stderr)
            raise SystemExit(2)
        _MD = markdown.Markdown(extensions=["tables", "fenced_code"])
    return _MD


_HEADING = re.compile(r"<h([1-4])>(.*?)</h\1>", re.S)


def render_md(text: str):
    """Markdown -> (html, blocks). h1–h4 get sequential ids `blk-N` because
    CJK headings cannot slugify; blocks drive the in-page navigation."""
    renderer = _get_md()
    renderer.reset()
    html = renderer.convert(text)
    blocks: "list[dict]" = []

    def _tag(match):
        index = len(blocks)
        level = int(match.group(1))
        title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        blocks.append({"id": f"blk-{index}", "level": level, "title": title})
        return f'<h{level} id="blk-{index}">{match.group(2)}</h{level}>'

    return _HEADING.sub(_tag, html), blocks


def part_anchor(blocks: "list[dict]", symbol: str) -> "str | None":
    """Basket report -> anchor of this symbol's `Part` block. Level-1 blocks
    only, and the FIRST level-1 block (the document title) is excluded — doc
    titles routinely contain the symbol and would false-match. None when the
    report has no per-symbol Part structure (page lands at the top)."""
    level1 = [b for b in blocks if b["level"] == 1]
    needle = symbol.upper()
    bare = needle.split(".")[0]
    for block in level1[1:]:
        title = block["title"].upper()
        if needle in title or (bare and bare in title):
            return block["id"]
    return None
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS (RenderTests run locally because the venv has `markdown`).

- [ ] **Step 5: CI wiring**

In `.github/workflows/ci.yml`, the inflection job's install line (`:49`,
`pip install -r inflection_discovery/requirements.txt pytest pyyaml`) gains
`markdown`, and its pytest line (`:51`) gains `tests/test_export_web.py` so
the renderer tests run in CI:

```yaml
          pip install -r inflection_discovery/requirements.txt pytest pyyaml markdown
```

```yaml
          python -m pytest inflection_discovery/tests tests/test_contract.py tests/test_export_web.py -v
```

- [ ] **Step 6: Run the full suite + commit**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: PASS.

```bash
git add scripts/export_web.py tests/test_export_web.py .github/workflows/ci.yml pyproject.toml uv.lock
git commit -m "feat(webapp): export-side markdown rendering, block anchors, basket part anchor"
```

(If `uv.lock` doesn't exist in this repo, commit whatever `uv add markdown`
actually changed — check `git status`.)

---

### Task 7: P2 ride-along + simulated-maturity preview

**Files:**
- Modify: `scripts/export_web.py` (append)
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Write the failing tests** (append)

```python
class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.provider = ew.FileHistoryProvider(PRICES)
        self.recs = ew.load_symbol_records(FIXTURE_HOME, "ACME")

    def test_matured_window_scored_on_adjusted_basis(self):
        outcome = ew.outcome_for(self.recs[0], self.provider, AS_OF)
        # new-idea 2026-03-02 + 90d = 2026-05-31; close_on falls back to
        # 05-29 raw 130 -> adjusted 65; p0 adjusted 50 -> return +30%.
        win = outcome["windows"]["90"]
        self.assertAlmostEqual(win["exit_price"], 65.0)
        self.assertAlmostEqual(win["return"], 0.30)
        self.assertTrue(win["direction_hit"])  # Buy, up
        self.assertEqual(win["scenario_landing"], "bear_base")  # 65 in 40..75

    def test_unmatured_windows_pending_with_maturity_date(self):
        outcome = ew.outcome_for(self.recs[0], self.provider, AS_OF)
        pending = {p["window"]: p["matures_on"] for p in outcome["pending"]}
        self.assertEqual(set(pending), {180, 365})
        self.assertEqual(pending[180], "2026-08-29")

    def test_sim_outcome_reuses_real_formulas(self):
        sim = ew.simulate_outcome(self.recs[0], self.provider, AS_OF)
        self.assertEqual(set(sim), {"90", "180", "365"})
        # 90d sim exit = latest adjusted close (66); drift toward base later.
        self.assertAlmostEqual(sim["90"]["exit_price"], 66.0)
        self.assertIn("direction_hit", sim["90"])

    def test_sim_outcome_none_without_base_scenario(self):
        bolt = ew.load_symbol_records(FIXTURE_HOME, "BOLT")[0]
        self.assertIsNone(ew.simulate_outcome(bolt, self.provider, AS_OF))
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.OutcomeTests -v`
Expected: FAIL (`outcome_for` not defined).

- [ ] **Step 3: Implement** (append to `scripts/export_web.py`)

```python
# ----------------------------- P2 ride-along -----------------------------

class _AdjustedHistory:
    """Adapter giving outcome_score's close_on/low_high over one symbol's
    split-adjusted closes (closes only — low==high==close, same fidelity as
    P2's own FileHistory)."""

    def __init__(self, provider, symbol: str) -> None:
        dates, closes = adjusted_series(provider.series(symbol),
                                        provider.splits(symbol))
        self._series = {as_date(d): (px, px, px)
                        for d, px in zip(dates, closes)}

    def close_on(self, symbol: str, target: datetime.date):
        return osc._pick_close(self._series, target)

    def low_high(self, symbol: str, start, end):
        return osc._pick_low_high(self._series, start, end)


def _meta_adjusted(meta: dict, factor: float) -> dict:
    """Copy of the record with every price-denominated field moved to the
    current share basis, so P2 formulas compare like with like."""
    adjusted = dict(meta)
    adjusted["price_at_decision"] = _adj(meta.get("price_at_decision"), factor)
    if is_number(meta.get("weighted_fair_value")):
        adjusted["weighted_fair_value"] = _adj(meta["weighted_fair_value"], factor)
    scen = meta.get("scenarios")
    if isinstance(scen, dict):
        adjusted["scenarios"] = {k: _adj(v, factor) if is_number(v) else v
                                 for k, v in scen.items()}
    trig = meta.get("triggers")
    if isinstance(trig, dict):
        new_trig = {}
        for group, items in trig.items():
            new_items = []
            for item in items or []:
                if isinstance(item, dict) and item.get("type") == "price" \
                        and is_number(item.get("level")):
                    item = dict(item, level=_adj(item["level"], factor))
                new_items.append(item)
            new_trig[group] = new_items
        adjusted["triggers"] = new_trig
    return adjusted


def outcome_for(meta: dict, provider, today: datetime.date) -> dict:
    symbol = meta["symbol"]
    factor = factor_for(provider.splits(symbol), as_date(meta["date"])) or 1.0
    history = _AdjustedHistory(provider, symbol)
    record, pending, gaps = osc.score_record(
        _meta_adjusted(meta, factor), history, today, WINDOWS)
    return {"windows": (record or {}).get("windows", {}),
            "pending": [{"window": p["window"], "matures_on": p["matures_on"]}
                        for p in pending],
            "gaps": gaps}


def simulate_outcome(meta: dict, provider, today: datetime.date) -> "dict | None":
    """Deterministic PREVIEW of matured windows (private build only): 90d exit
    = latest adjusted close; 180/365d drift 1/3, 2/3 of the way toward the
    adjusted base scenario. Reuses outcome_score's own formulas so the
    semantics match the real thing. The UI must amber-tag this."""
    symbol = meta["symbol"]
    factor = factor_for(provider.splits(symbol), as_date(meta["date"])) or 1.0
    adjusted = _meta_adjusted(meta, factor)
    scen = adjusted.get("scenarios") or {}
    base = scen.get("base")
    history = _AdjustedHistory(provider, symbol)
    last = history.close_on(symbol, today)
    p0 = adjusted.get("price_at_decision")
    if last is None or not is_number(base) or not is_number(p0):
        return None
    out = {}
    for window, drift in zip(WINDOWS, (0.0, 1 / 3, 2 / 3)):
        exit_price = round(last + (base - last) * drift, 4)
        ret = (exit_price - p0) / p0
        result = {"exit_price": exit_price, "return": round(ret, 4),
                  "direction_hit": osc._direction_hit(
                      adjusted.get("stance"), ret, exit_price, scen)}
        wfv_res = osc._wfv(p0, exit_price, adjusted.get("weighted_fair_value"))
        if wfv_res is not None:
            result["gap_closed"], result["converged"] = wfv_res
        landing = osc._scenario_landing(exit_price, scen)
        if landing is not None:
            result["scenario_landing"] = landing
        out[str(window)] = result
    return out
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/export_web.py tests/test_export_web.py
git commit -m "feat(webapp): P2 outcome ride-along + simulated-maturity preview"
```

---

### Task 8: FX snapshot, payload assembly, CLI

**Files:**
- Modify: `scripts/export_web.py` (append)
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Write the failing tests** (append)

```python
class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAS_MARKDOWN:
            raise unittest.SkipTest("markdown not installed")
        provider = ew.FileHistoryProvider(PRICES)
        cls.payload = ew.export_dataset(
            FIXTURE_HOME, provider, AS_OF, dataset="private",
            include_sim=True, fx=None)

    def test_envelope(self):
        self.assertEqual(self.payload["schema"], "web-export/v1")
        self.assertEqual(self.payload["dataset"], "private")
        self.assertEqual(self.payload["price_basis"],
                         "current share basis (split-adjusted, ex-dividend)")
        self.assertEqual(self.payload["as_of"], "2026-08-11")

    def test_board_has_one_card_per_symbol_with_latest_record(self):
        cards = {c["symbol"]: c for c in self.payload["board"]["cards"]}
        self.assertEqual(set(cards), {"ACME", "BOLT", "7203.T", "GONE"})
        # ACME latest = the same-day pair -> position-review wins the card
        self.assertEqual(cards["ACME"]["mode"], "position-review")
        self.assertEqual(cards["ACME"]["price"], 66.0)
        self.assertIsNone(cards["GONE"]["price"])
        self.assertEqual(cards["GONE"]["no_price_reason"], "no data from provider")

    def test_symbol_pages_carry_chain_and_adjusted_series(self):
        acme = self.payload["symbols"]["ACME"]
        self.assertEqual(len(acme["records"]), 3)
        self.assertEqual(acme["price"]["as_of"], "2026-08-10")
        by_date = dict(zip(acme["price"]["dates"], acme["price"]["closes"]))
        self.assertEqual(by_date["2026-06-30"], 66.0)  # adjusted
        self.assertEqual(len(acme["ghosts"]), 1)
        self.assertEqual(acme["actions"][0]["action"], "added")
        self.assertTrue(acme["held"])

    def test_records_carry_bodies_outcome_sim_and_report_refs(self):
        rec = self.payload["symbols"]["ACME"]["records"][0]
        self.assertIn("initial thesis", rec["body_html"])
        self.assertIn("summary", rec)
        self.assertEqual(rec["outcome"]["pending"][0]["window"], 180)
        self.assertIsNotNone(rec["sim_outcome"])
        self.assertIn(rec["report"], self.payload["reports"])
        basket = self.payload["symbols"]["ACME"]["records"][1]
        self.assertEqual(
            self.payload["reports"][basket["report"]]["part_anchor"]["ACME"],
            "blk-1")

    def test_delta_between_consecutive_records(self):
        second = self.payload["symbols"]["ACME"]["records"][1]
        self.assertEqual(second["delta"]["stance"], ["Buy", "Hold"])
        self.assertEqual(second["delta"]["zone"], ["Accumulation", "Hold"])

    def test_demo_dataset_excludes_sim(self):
        provider = ew.FileHistoryProvider(PRICES)
        demo = ew.export_dataset(FIXTURE_HOME, provider, AS_OF,
                                 dataset="demo", include_sim=False, fx=None)
        self.assertEqual(demo["dataset"], "demo")
        self.assertIsNone(demo["symbols"]["ACME"]["records"][0]["sim_outcome"])

    def test_split_factor_warning_when_splits_unknown(self):
        class NoSplits(ew.FileHistoryProvider):
            def splits(self, symbol):
                return None
        payload = ew.export_dataset(FIXTURE_HOME, NoSplits(PRICES), AS_OF,
                                    dataset="private", include_sim=False, fx=None)
        kinds = {(w["symbol"], w["kind"]) for w in payload["warnings"]}
        self.assertIn(("ACME", "split_factor_unavailable"), kinds)


class CliTests(unittest.TestCase):
    def test_cli_writes_dataset(self):
        if not HAS_MARKDOWN:
            raise unittest.SkipTest("markdown not installed")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "dataset.json"
            code = ew.main(["--home", str(FIXTURE_HOME), "--offline",
                            "--prices", str(PRICES), "--as-of", "2026-08-11",
                            "--dataset", "private", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "web-export/v1")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_export_web.DatasetTests tests.test_export_web.CliTests -v`
Expected: FAIL (`export_dataset` not defined).

- [ ] **Step 3: Implement** (append to `scripts/export_web.py`)

```python
# ----------------------------- FX snapshot -----------------------------

def fetch_fx(currencies: "set[str]", base: str = "USD") -> "dict | None":
    """Frankfurter snapshot at export time. None on any failure (the UI shows
    native currencies; FX is carried for future use)."""
    wanted = sorted(c for c in currencies if c and c != base)
    if not wanted:
        return {"base": base, "rates": {}, "as_of": datetime.date.today().isoformat()}
    try:
        import requests

        resp = requests.get("https://api.frankfurter.app/latest",
                            params={"from": base, "to": ",".join(wanted)},
                            timeout=10)
        resp.raise_for_status()
        doc = resp.json()
        return {"base": base, "rates": doc.get("rates") or {},
                "as_of": doc.get("date")}
    except Exception:
        return None


# ----------------------------- assembly -----------------------------

def _first_sentence(body: str, limit: int = 160) -> str:
    text = re.sub(r"[#>*`|]", "", body)
    text = re.sub(r"\s+", " ", text).strip()
    for stop in ("。", ". "):
        cut = text.find(stop)
        if 0 < cut < limit:
            return text[: cut + len(stop)].strip()
    return text[:limit].strip()


def _jsonable(value):
    """Dates -> ISO strings, recursively — YAML parses nested dates (e.g.
    inside action_taken) into datetime.date, which json.dumps rejects."""
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _public_meta(meta: dict) -> dict:
    """Full frontmatter passthrough minus internal keys."""
    return {k: _jsonable(v) for k, v in meta.items() if not k.startswith("_")}


def export_dataset(home: Path, provider, today: datetime.date, *,
                   dataset: str, include_sim: bool, fx) -> dict:
    holdings, legs = load_portfolio(home)
    warnings: "list[dict]" = []
    reports: "dict[str, dict]" = {}
    report_symbols: "dict[str, set]" = {}

    def add_report(path_str: str) -> "str | None":
        path = Path(path_str)
        if not path.exists():
            warnings.append({"symbol": None, "kind": "report_missing",
                             "detail": str(path)})
            return None
        key = str(path.resolve())
        if key not in reports:
            text = FRONTMATTER.sub("", path.read_text(encoding="utf-8-sig"))
            html, blocks = render_md(text)
            title_match = re.search(r"^#\s+(.+)$", text, re.M)
            reports[key] = {
                "title": title_match.group(1).strip() if title_match else path.stem,
                "html": html, "blocks": blocks, "part_anchor": {}}
        return key

    board_cards = []
    symbols_out: "dict[str, dict]" = {}
    for symbol in list_symbols(home):
        records = load_symbol_records(home, symbol)
        if not records:
            continue
        if hasattr(provider, "load"):
            provider.load(symbol, records[-1].get("market") or "US")
        series = provider.series(symbol)
        splits = provider.splits(symbol)
        dates, closes = adjusted_series(series, splits)
        price = closes[-1] if closes else None
        price_as_of = dates[-1] if dates else None
        as_of_day = provider.as_of(symbol)
        no_price_reason = provider.failure_reason(symbol) if price is None else None

        rec_out = []
        previous = None
        for meta in records:
            day = as_date(meta["date"])
            factor = factor_for(splits, day)
            if factor is None:
                warnings.append({"symbol": symbol,
                                 "kind": "split_factor_unavailable",
                                 "detail": f"record {day}: splits unknown, "
                                           "numbers exported unadjusted"})
                factor_effective = 1.0
            else:
                factor_effective = factor
            body_html, _ = render_md(meta["_body"])
            report_key = None
            if meta.get("source_report"):
                report_key = add_report(
                    str((home / "records" / symbol / meta["source_report"]).resolve()))
                if report_key:
                    report_symbols.setdefault(report_key, set()).add(symbol)
            delta = None
            if previous is not None:
                delta = {"stance": [previous.get("stance"), meta.get("stance")],
                         "wfv": [previous.get("weighted_fair_value"),
                                 meta.get("weighted_fair_value")],
                         "zone": [previous.get("valuation_zone"),
                                  meta.get("valuation_zone")],
                         "confidence": [previous.get("confidence"),
                                        meta.get("confidence")]}
            scen = meta.get("scenarios") or {}
            rec_out.append({
                **_public_meta(meta),
                "file": meta["_file"],
                "adj": {"bear": _adj(scen.get("bear"), factor_effective),
                        "base": _adj(scen.get("base"), factor_effective),
                        "bull": _adj(scen.get("bull"), factor_effective),
                        "wfv": _adj(meta.get("weighted_fair_value"), factor_effective),
                        "price_at_decision": _adj(meta.get("price_at_decision"),
                                                  factor_effective)},
                "split_factor": factor,
                "summary": _first_sentence(meta["_body"]),
                "delta": delta,
                "body_html": body_html,
                "report": report_key,
                "outcome": outcome_for(meta, provider, today),
                "sim_outcome": (simulate_outcome(meta, provider, today)
                                if include_sim else None),
            })
            previous = meta

        ghosts = []
        for ghost in load_ghost_rows(home / "records" / symbol / "INDEX.md"):
            kept = []
            for ref in ghost["reports"]:
                key = add_report(ref["path"])
                if key:
                    report_symbols.setdefault(key, set()).add(symbol)
                    kept.append({"title": ref["title"], "report": key})
            ghosts.append({"date": ghost["date"], "mode": ghost["mode"],
                           "reports": kept})

        latest_day = as_date(records[-1]["date"])
        card_meta = band_record_for_date(records, latest_day) or records[-1]
        latest_factor = factor_for(splits, as_date(card_meta["date"])) or 1.0
        board_cards.append(build_card(
            symbol, card_meta, price=price, price_as_of=price_as_of,
            price_stale=provider.stale(symbol), no_price_reason=no_price_reason,
            factor=latest_factor, holdings=holdings, legs=legs, today=today))

        holding = holdings.get(symbol)
        symbols_out[symbol] = {
            "market": records[-1].get("market"),
            "currency": records[-1].get("currency"),
            "held": bool(holding), "qty": (holding or {}).get("qty"),
            "avg_cost": (holding or {}).get("avg_cost"),
            "price": {"dates": dates, "closes": closes,
                      "as_of": as_of_day.isoformat() if as_of_day else None,
                      "stale": provider.stale(symbol),
                      "splits": [[d.isoformat(), r] for d, r in splits or []]},
            "records": rec_out, "ghosts": ghosts,
            "actions": extract_actions(records),
        }

    for key, symbols in report_symbols.items():
        for symbol in symbols:
            anchor = part_anchor(reports[key]["blocks"], symbol)
            if anchor:
                reports[key]["part_anchor"][symbol] = anchor

    return {
        "schema": SCHEMA, "dataset": dataset,
        "generated_at": today.isoformat(), "as_of": today.isoformat(),
        "price_basis": PRICE_BASIS,
        "fx": fx,
        "board": {"cards": board_cards},
        "symbols": symbols_out,
        "reports": reports,
        "warnings": warnings,
    }


# ----------------------------- CLI -----------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="vault -> web-export/v1 JSON")
    parser.add_argument("--home", help="state home (default: ~/.investing-home)")
    parser.add_argument("--out", required=True, help="output dataset JSON path")
    parser.add_argument("--dataset", choices=("private", "demo"),
                        default="private")
    parser.add_argument("--prices", help="closes+splits YAML (FileHistoryProvider)")
    parser.add_argument("--offline", action="store_true",
                        help="no network: requires --prices, skips FX")
    parser.add_argument("--cache", default=".webapp_cache/prices.json")
    parser.add_argument("--as-of", help="fix today for deterministic runs")
    args = parser.parse_args(argv)

    try:
        home = resolve_home(args.home)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"cannot resolve state home: {exc}", file=sys.stderr)
        return 2
    if not (home / "records").is_dir():
        print(f"no records/ under {home}", file=sys.stderr)
        return 2

    today = as_date(args.as_of) if args.as_of else datetime.date.today()
    if args.offline and not args.prices:
        print("--offline requires --prices", file=sys.stderr)
        return 2
    provider = (FileHistoryProvider(args.prices) if args.prices
                else LiveHistoryProvider(Path(args.cache), today=today))

    fx = None
    if not args.offline:
        currencies = set()
        for symbol in list_symbols(home):
            for meta in load_symbol_records(home, symbol):
                currencies.add(meta.get("currency"))
        fx = fetch_fx(currencies)

    payload = export_dataset(home, provider, today, dataset=args.dataset,
                             include_sim=(args.dataset == "private"), fx=fx)
    if isinstance(provider, LiveHistoryProvider):
        provider.save()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    n_warn = len(payload["warnings"])
    print(f"wrote {out} — {len(payload['board']['cards'])} cards, "
          f"{len(payload['reports'])} reports, {n_warn} warnings")
    for warning in payload["warnings"]:
        print(f"  warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_export_web -v`
Expected: PASS. Fix arithmetic mismatches by trusting the test numbers (they
were derived from the fixture by hand).

- [ ] **Step 5: Run the whole suite + commit**

Run: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
Expected: PASS.

```bash
git add scripts/export_web.py tests/test_export_web.py
git commit -m "feat(webapp): dataset assembly, FX snapshot, export CLI"
```

---

### Task 9: Vendor ECharts + webapp scaffolding

**Files:**
- Create: `webapp/assets/echarts.min.js` (copied from the prototype vendoring)
- Create: `webapp/assets/NOTICE.md`

- [ ] **Step 1: Copy the pinned ECharts build**

The prototypes already vendor the exact build the user approved (5.6.0). Copy
it — no network needed:

```bash
mkdir -p webapp/assets
cp "/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.scratch/stock-analysis-web-app/prototypes/06-zone-board/echarts.min.js" webapp/assets/echarts.min.js
grep -o "5\.6\.0" webapp/assets/echarts.min.js | head -1
```

Expected: `5.6.0` printed. (If the grep finds nothing, check the version
banner at the top of the file — it must be 5.6.x.)

- [ ] **Step 2: Write `webapp/assets/NOTICE.md`**

```markdown
# Vendored assets

- `echarts.min.js` — Apache ECharts 5.6.0, Apache License 2.0
  (https://echarts.apache.org). Vendored so builds are deterministic and the
  generated pages work offline over `file://` with zero CDN dependencies.
```

- [ ] **Step 3: Commit**

```bash
git add webapp/assets/echarts.min.js webapp/assets/NOTICE.md
git commit -m "chore(webapp): vendor ECharts 5.6.0"
```

---

### Task 10: Board template port + builder core

**Files:**
- Create: `webapp/templates/board.html` (ported from prototype 06)
- Create: `scripts/build_webapp.py`
- Test: `tests/test_build_webapp.py`

- [ ] **Step 1: Port the board template**

Source: `/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.scratch/stock-analysis-web-app/prototypes/06-zone-board/template.html`
(391 lines; single HTML file with inline CSS + JS; renders from a global
`DATA` object).

Create `webapp/templates/board.html` from it with exactly these changes:

1. **Keep only variant A (columnar kanban).** Delete the variant B and C
   sections, the variant-switcher floating bar, the `#A/#B/#C` hash logic,
   and the ArrowLeft/ArrowRight keyboard handler. The kanban root renders
   unconditionally.
2. **Keep the placeholder contract**: the template must contain the literal
   strings `<script src="echarts.min.js"></script>` and
   `/*__DATA_JSON__*/null` (the builder replaces both), plus
   `<!--__BANNER__-->` immediately after the `<body>` tag (demo banner slot —
   add this comment line; it is new).
3. **Data shape change**: the prototype read `DATA.cards`; the v1 dataset
   nests them at `DATA.board.cards` and adds `price_stale` /
   `no_price_reason` / `next_earnings` fields. Update the accessor
   (one line where `DATA.cards` is read) and add a `无价格` chip branch when
   `card.price === null` (the prototype already renders a no-price state —
   verify it keys off `price == null`, adjust if it used a different flag).
4. **Zone columns**: confirm the 4+1 column list is
   `["Accumulation", "Hold", "Exhaustion", "Invalidation", "Missing Inputs"]`
   and Missing Inputs renders as the narrow neutral-gray column (the
   prototype already does this — keep it).
5. **Card links**: wrap each card so clicking navigates to
   `s/<symbol>.html` (new — the prototype had no per-symbol pages):
   the card render function gains
   `card.addEventListener("click", () => location.href = "s/" + encodeURIComponent(c.symbol) + ".html");`
   and `cursor: pointer` on the card CSS class.
6. Keep everything else byte-identical where possible: the palette, Didot
   masthead, micro-ruler renderer, chips, stale styling, compact numerals.

- [ ] **Step 2: Write the failing builder tests**

`tests/test_build_webapp.py`:

```python
import json
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_webapp as bw  # noqa: E402

try:
    import markdown  # noqa: F401
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


def _dataset(dataset="private"):
    """Small hand-rolled dataset (schema-shaped, not exporter-derived) so the
    builder tests run in the pyyaml-only job without markdown."""
    return {
        "schema": "web-export/v1", "dataset": dataset,
        "generated_at": "2026-08-11", "as_of": "2026-08-11",
        "price_basis": "current share basis (split-adjusted, ex-dividend)",
        "fx": None,
        "board": {"cards": [{
            "symbol": "ACME", "market": "US", "currency": "USD",
            "record_date": "2026-06-20", "mode": "position-review",
            "stance": "Hold", "confidence": "Medium", "position_size": "Starter",
            "valuation_zone": "Hold", "wfv": 80.0, "bear": 45.0, "base": 80.0,
            "bull": 105.0, "price": 66.0, "price_as_of": "2026-08-10",
            "price_stale": False, "no_price_reason": None,
            "price_at_decision": 60.0, "split_factor": 2.0, "cursor": 0.35,
            "discount": -0.175, "triggers_touched": [], "scenario_breach": None,
            "stale_days": 0, "review_by": "2026-12-01", "earnings_in": 9,
            "next_earnings": "2026-08-20", "drawdown": 0.10, "held": True,
            "qty": 40, "avg_cost": 59.0, "option_legs": 1,
            "put_assignment_risk": True}]},
        "symbols": {"ACME": {
            "market": "US", "currency": "USD", "held": True, "qty": 40,
            "avg_cost": 59.0,
            "price": {"dates": ["2026-08-10"], "closes": [66.0],
                      "as_of": "2026-08-10", "stale": False, "splits": []},
            "records": [{"schema": "decision-record/v1", "symbol": "ACME",
                         "market": "US", "date": "2026-06-20",
                         "mode": "position-review", "stance": "Hold",
                         "currency": "USD", "price_at_decision": 120.0,
                         "review_by": "2026-12-01", "valuation_zone": "Hold",
                         "weighted_fair_value": 160.0,
                         "scenarios": {"bear": 90.0, "base": 160.0, "bull": 210.0},
                         "file": "2026-06-20-position-review.md",
                         "adj": {"bear": 45.0, "base": 80.0, "bull": 105.0,
                                 "wfv": 80.0, "price_at_decision": 60.0},
                         "split_factor": 2.0, "summary": "Review.",
                         "delta": None, "body_html": "<p>Review.</p>",
                         "report": None,
                         "outcome": {"windows": {}, "pending": [
                             {"window": 90, "matures_on": "2026-09-18"}],
                             "gaps": []},
                         "sim_outcome": None}],
            "ghosts": [], "actions": []}},
        "reports": {},
        "warnings": [],
    }


class BuildTests(unittest.TestCase):
    def _build(self, dataset=None, demo=False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = pathlib.Path(tmp.name) / "site"
        data = dataset or _dataset("demo" if demo else "private")
        src = pathlib.Path(tmp.name) / "dataset.json"
        src.write_text(json.dumps(data), encoding="utf-8")
        code = bw.main(["--data", str(src), "--out", str(out)] +
                       (["--demo"] if demo else []))
        return code, out

    def test_builds_index_and_symbol_pages(self):
        code, out = self._build()
        self.assertEqual(code, 0)
        index = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("echarts", index.lower())
        self.assertNotIn("__DATA_JSON__", index)
        self.assertNotIn('src="echarts.min.js"', index)  # inlined, not linked
        self.assertIn('"ACME"', index)
        symbol_page = (out / "s" / "ACME.html").read_text(encoding="utf-8")
        self.assertIn('"2026-06-20"', symbol_page)

    def test_symbol_page_only_gets_its_slice(self):
        data = _dataset()
        data["symbols"]["OTHER"] = json.loads(
            json.dumps(data["symbols"]["ACME"]).replace("ACME", "OTHER"))
        data["board"]["cards"].append(
            dict(data["board"]["cards"][0], symbol="OTHER"))
        code, out = self._build(dataset=data)
        self.assertEqual(code, 0)
        acme = (out / "s" / "ACME.html").read_text(encoding="utf-8")
        self.assertNotIn('"OTHER"', acme)

    def test_schema_mismatch_refused(self):
        data = _dataset()
        data["schema"] = "web-export/v2"
        code, _ = self._build(dataset=data)
        self.assertEqual(code, 2)

    def test_demo_flag_refuses_private_dataset(self):
        # privacy rail: a private dataset must never enter the demo pipeline
        code, _ = self._build(dataset=_dataset("private"), demo=True)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m unittest tests.test_build_webapp -v`
Expected: FAIL at import (`No module named build_webapp`).

- [ ] **Step 4: Implement the builder core**

Create `scripts/build_webapp.py`:

```python
#!/usr/bin/env python3
"""Static-site builder: web-export/v1 JSON -> webapp_out/.

Design: docs/plans/2026-08-11-web-app-design.md. Pages are the two
user-approved prototype templates (06 variant A board, 07 variant B timeline)
with data + vendored ECharts inlined, so the output opens over file:// with
zero network. Exit codes: 0 ok, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "web-export/v1"
REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "webapp" / "templates"
ASSETS = REPO / "webapp" / "assets"

DEMO_BANNER = (
    '<div class="demo-banner">DEMO — fictional data plus same-day sample '
    'records; nothing here is investment advice.</div>'
)


def _inline(template: str, data: dict, banner: str) -> str:
    echarts = (ASSETS / "echarts.min.js").read_text(encoding="utf-8")
    page = template.replace(
        '<script src="echarts.min.js"></script>',
        "<script>/* echarts 5.6.0 inlined */\n" + echarts + "\n</script>")
    blob = json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")
    if "/*__DATA_JSON__*/null" not in page:
        raise ValueError("template missing /*__DATA_JSON__*/null placeholder")
    page = page.replace("/*__DATA_JSON__*/null", blob)
    return page.replace("<!--__BANNER__-->", banner)


def _symbol_slice(payload: dict, symbol: str) -> dict:
    entry = payload["symbols"][symbol]
    report_keys = {r["report"] for r in entry["records"] if r.get("report")}
    for ghost in entry["ghosts"]:
        report_keys.update(ref["report"] for ref in ghost["reports"])
    return {
        "schema": payload["schema"], "dataset": payload["dataset"],
        "as_of": payload["as_of"], "price_basis": payload["price_basis"],
        "symbol": symbol, "data": entry,
        "reports": {k: payload["reports"][k] for k in sorted(report_keys)
                    if k in payload["reports"]},
    }


def build(payload: dict, out_dir: Path, demo: bool) -> None:
    banner = DEMO_BANNER if demo else ""
    board_template = (TEMPLATES / "board.html").read_text(encoding="utf-8")
    symbol_template = (TEMPLATES / "symbol.html").read_text(encoding="utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    board_data = {"schema": payload["schema"], "dataset": payload["dataset"],
                  "as_of": payload["as_of"],
                  "price_basis": payload["price_basis"],
                  "board": payload["board"], "warnings": payload["warnings"]}
    (out_dir / "index.html").write_text(
        _inline(board_template, board_data, banner), encoding="utf-8")

    pages_dir = out_dir / "s"
    pages_dir.mkdir(exist_ok=True)
    for symbol in sorted(payload["symbols"]):
        page = _inline(symbol_template, _symbol_slice(payload, symbol), banner)
        (pages_dir / f"{symbol}.html").write_text(page, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="web-export/v1 JSON -> static site")
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="webapp_out")
    parser.add_argument("--demo", action="store_true",
                        help="demo build: requires a dataset tagged demo, "
                             "adds the fictional/not-advice banner")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(Path(args.data).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read dataset: {exc}", file=sys.stderr)
        return 2
    if payload.get("schema") != SCHEMA:
        print(f"dataset schema {payload.get('schema')!r} != {SCHEMA}; refusing",
              file=sys.stderr)
        return 2
    if args.demo and payload.get("dataset") != "demo":
        print("--demo build requires a dataset tagged dataset=demo; refusing "
              "(privacy rail: private datasets never enter the demo pipeline)",
              file=sys.stderr)
        return 2
    if not args.demo and payload.get("dataset") == "demo":
        print("note: building a demo-tagged dataset without --demo "
              "(banner omitted)", file=sys.stderr)

    build(payload, Path(args.out), demo=args.demo)
    n_pages = 1 + len(payload["symbols"])
    print(f"built {args.out} — {n_pages} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Until Task 11 lands, create `webapp/templates/symbol.html` as a minimal
stand-in so the builder runs (Task 11 replaces it with the real port):

```html
<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>symbol</title></head>
<body><!--__BANNER__-->
<script src="echarts.min.js"></script>
<script>const DATA = /*__DATA_JSON__*/null; document.title = DATA.symbol;
document.body.insertAdjacentText("beforeend", JSON.stringify(DATA.data.records.map(r => r.date)));</script>
</body></html>
```

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m unittest tests.test_build_webapp -v`
Expected: PASS. (`test_builds_index_and_symbol_pages` asserts the record date
string appears in the symbol page — the stand-in satisfies that via the
inlined data blob.)

- [ ] **Step 6: Eyeball the board against the prototype (manual)**

```bash
.venv/bin/python scripts/export_web.py --home tests/fixtures/webapp-home --offline --prices tests/fixtures/webapp-prices.yaml --as-of 2026-08-11 --dataset private --out /tmp/webapp-fixture.json
.venv/bin/python scripts/build_webapp.py --data /tmp/webapp-fixture.json --out /tmp/webapp-site
open /tmp/webapp-site/index.html
```

Expected: the kanban renders with 4+1 columns; ACME sits in Hold with ruler
45—◆80—105, price 66, 折价 −17.5%, held/put badges, earnings chip; BOLT in
the Missing Inputs narrow column with dashed ruler; GONE shows the 无价格
chip; the JP card renders. Compare side-by-side with
`prototypes/06-zone-board/zone-board-prototype.html` (`#A`) for visual
parity of card anatomy.

- [ ] **Step 7: Commit**

```bash
git add webapp/templates/board.html webapp/templates/symbol.html scripts/build_webapp.py tests/test_build_webapp.py
git commit -m "feat(webapp): builder core + zone board page (ported prototype 06 variant A)"
```

---

### Task 11: Thesis Timeline template port

**Files:**
- Replace: `webapp/templates/symbol.html` (ported from prototype 07)
- Test: `tests/test_build_webapp.py` (append)

- [ ] **Step 1: Port the timeline template**

Source: `/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.scratch/stock-analysis-web-app/prototypes/07-thesis-timeline/template.html`
(992 lines). Replace the Task 10 stand-in with a port applying exactly these
changes:

1. **Keep only variant B (双栏账房).** Delete variants A and C, the
   variant-switcher bar, hash routing, and the `,`/`.` step-through handler
   (that was variant C's). Variant B's root renders unconditionally.
2. **Single-symbol pages.** The prototype had a three-symbol masthead tab
   bar reading `DATA.symbols[sym]`; the v1 page payload is
   `{schema, dataset, as_of, price_basis, symbol, data, reports}` for ONE
   symbol. Replace the tab logic with: `const SYM = DATA.symbol; const S =
   DATA.data;` and delete the tab UI. Add a masthead link back to the board:
   `<a href="../index.html">← Zone Board</a>`.
3. **Report lookup**: the prototype resolved `record.report_path` against
   `DATA.reports`; v1 uses `record.report` (key into `DATA.reports`) and
   ghost rows carry `reports: [{title, report}]`. `part_anchor` moved from a
   per-record field to `DATA.reports[key].part_anchor[SYM]` — update the
   drawer-open call site to
   `const anchor = (rep.part_anchor || {})[SYM];`.
4. **Keep, verbatim:** the chart factory (stepped band by zone, three-channel
   reference-line styles, right-edge point papers + selected-segment labels
   with the 8.5% de-collision, default zoom window, dataZoom), bidirectional
   linkage, rail rendering (new→old, deltas, ghost ○ and action ▼ rows, held
   dot), P2 chips + 复盘明细 table (pending rows `未到期 —— YYYY-MM-DD 出分`),
   the sim-preview masthead toggle with amber warning strip (render the
   toggle only when any record has non-null `sim_outcome` — that is already
   the private-build signal), the report drawer with block nav, the ☰ 图例
   legend overlay, and all CJK typography CSS.
5. **Placeholder contract** as in Task 10: keep
   `<script src="echarts.min.js"></script>`, `/*__DATA_JSON__*/null`, and add
   `<!--__BANNER__-->` after `<body>`.
6. **Field-name sweep.** The exporter renamed nothing else, but three
   prototype fields differ: `wfv` on records is now
   `weighted_fair_value` in the raw passthrough (use `record.adj.wfv` for
   plotting — the prototype already plotted from `adj`); `record.file`
   replaces `_file`; `price.stale` is new (render the stale flag next to
   `as_of` in the masthead when true). Grep the ported JS for `DATA.symbols`,
   `report_path`, `_file` — all three must have zero remaining hits.

- [ ] **Step 2: Extend the builder tests** (append to
  `tests/test_build_webapp.py`)

```python
class SymbolPageTests(unittest.TestCase):
    def _page(self, mutate=None):
        data = _dataset()
        if mutate:
            mutate(data)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = pathlib.Path(tmp.name) / "d.json"
        src.write_text(json.dumps(data), encoding="utf-8")
        out = pathlib.Path(tmp.name) / "site"
        self.assertEqual(bw.main(["--data", str(src), "--out", str(out)]), 0)
        return (out / "s" / "ACME.html").read_text(encoding="utf-8")

    def test_page_has_timeline_scaffolding(self):
        page = self._page()
        # markers that live in the template itself (not the data blob):
        # the legend button, the P2 detail-table label, the inlined chart lib
        for marker in ("echarts", "复盘明细", "图例"):
            self.assertIn(marker, page)
        self.assertNotIn("__DATA_JSON__", page)
        self.assertNotIn("DATA.symbols", page)   # single-symbol contract
        self.assertNotIn("report_path", page)

    def test_report_slice_included_when_referenced(self):
        def mutate(data):
            data["reports"]["/r/basket.md"] = {
                "title": "Basket", "html": "<h1 id=\"blk-0\">T</h1>",
                "blocks": [{"id": "blk-0", "level": 1, "title": "T"}],
                "part_anchor": {"ACME": "blk-0"}}
            data["symbols"]["ACME"]["records"][0]["report"] = "/r/basket.md"
        page = self._page(mutate)
        self.assertIn("Basket", page)

    def test_demo_banner_present_only_for_demo_build(self):
        data = _dataset("demo")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = pathlib.Path(tmp.name) / "d.json"
        src.write_text(json.dumps(data), encoding="utf-8")
        out = pathlib.Path(tmp.name) / "site"
        self.assertEqual(bw.main(["--data", str(src), "--out", str(out),
                                  "--demo"]), 0)
        page = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("demo-banner", page)
        private_page = self._page()
        self.assertNotIn("demo-banner", private_page)
```

- [ ] **Step 3: Run to verify the new tests fail against the stand-in**

Run: `.venv/bin/python -m unittest tests.test_build_webapp.SymbolPageTests -v`
Expected: FAIL (`图例` / `blk-` not in the stand-in page).

- [ ] **Step 4: Finish the port until tests pass**

Run: `.venv/bin/python -m unittest tests.test_build_webapp -v`
Expected: PASS.

- [ ] **Step 5: Eyeball against the prototype (manual)**

Rebuild the fixture site (same commands as Task 10 Step 6) and open
`/tmp/webapp-site/s/ACME.html`. Expected: left sticky chart with stepped
band (Accumulation green segment then Hold blue from 06-20, attributed to
position-review), WFV long-dash / base micro-dot / amber cost line at 59,
right-edge point papers; right rail new→old with the ghost ○ 2025-11-10 row,
▼ added action row, delta blocks Buy→Hold; P2 chips show one matured 90d ✓
and pending rows; report drawer opens the basket report and jumps to
`Part I — ACME`; ☰ 图例 overlay opens. Compare with
`prototypes/07-thesis-timeline/thesis-timeline-prototype.html` (`#B`).

- [ ] **Step 6: Commit**

```bash
git add webapp/templates/symbol.html tests/test_build_webapp.py
git commit -m "feat(webapp): thesis timeline page (ported prototype 07 variant B)"
```

---

### Task 12: Live smoke test (network-gated)

**Files:**
- Test: `tests/test_export_web.py` (append)

- [ ] **Step 1: Add the gated smoke test**

```python
def _network_available():
    import socket
    try:
        socket.create_connection(("query1.finance.yahoo.com", 443), timeout=5).close()
        return True
    except OSError:
        return False


try:
    import yfinance  # noqa: F401
    HAS_YF = True
except ImportError:
    HAS_YF = False


@unittest.skipUnless(HAS_YF, "yfinance not installed (pyyaml-only job)")
class LiveSmokeTests(unittest.TestCase):
    def test_live_fetch_one_symbol(self):
        if not _network_available():
            self.skipTest("no network")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            provider = ew.LiveHistoryProvider(
                cache_path=pathlib.Path(tmp) / "cache.json")
            provider.load("AAPL", "US")
            if not provider.series("AAPL"):
                self.skipTest("provider unavailable/rate-limited")  # smoke, not a flake
            self.assertGreater(len(provider.series("AAPL")), 100)
            self.assertIsNotNone(provider.as_of("AAPL"))
            provider.save()
            reloaded = ew.LiveHistoryProvider(
                cache_path=pathlib.Path(tmp) / "cache.json",
                fetch=lambda *a: (_ for _ in ()).throw(RuntimeError("down")))
            reloaded.load("AAPL", "US")
            self.assertTrue(reloaded.stale("AAPL"))  # cache served, marked stale
```

- [ ] **Step 2: Run it (venv has yfinance)**

Run: `.venv/bin/python -m unittest tests.test_export_web.LiveSmokeTests -v`
Expected: PASS (or SKIP offline).

- [ ] **Step 3: Commit**

```bash
git add tests/test_export_web.py
git commit -m "test(webapp): network-gated live history smoke"
```

---

### Task 13: Demo vault + demo build

**Files:**
- Create: `scripts/make_demo_vault.py`
- Create: `demo/state-home/` + `demo/prices.yaml` (generated, committed)
- Test: `tests/test_export_web.py` (append one test)

- [ ] **Step 1: Write the generator**

`scripts/make_demo_vault.py` — deterministic (seeded; the only time input is
the `--as-of` argument), writes a fictional vault the exporter can consume
with `--offline --prices demo/prices.yaml`:

```python
#!/usr/bin/env python3
"""Generate the committed fictional demo vault (design doc: Demo dataset).

Two fictional symbols with deep multi-mode timelines + synthetic prices from
a seeded piecewise drift/vol random walk. Real non-position sample records
are added later by actually running the framework (never backfilled). Regenerate:
  .venv/bin/python scripts/make_demo_vault.py --as-of 2026-08-11
"""
from __future__ import annotations

import argparse
import datetime
import random
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "demo"
SEED = 20260811

FICTION = {
    "ORCA": {
        "currency": "USD", "market": "US", "start_price": 40.0,
        "segments": [(160, 0.0008, 0.018), (120, -0.002, 0.03), (240, 0.0012, 0.02)],
        "records": [
            # (offset days from series start, mode, stance, zone, wfv_mult,
            #  bear_mult, bull_mult, action or None)
            (30, "new-idea", "Buy", "Accumulation", 1.5, 0.8, 1.9, None),
            (170, "event-review", "Hold", "Hold", 1.3, 0.75, 1.7, None),
            (300, "position-review", "Add", "Accumulation", 1.6, 0.85, 2.0, "added"),
            (420, "position-review", "Hold", "Hold", 1.4, 0.8, 1.8, None),
        ],
    },
    "BEACON": {
        "currency": "USD", "market": "US", "start_price": 120.0,
        "segments": [(200, 0.0015, 0.015), (180, -0.0005, 0.025), (140, 0.0, 0.02)],
        "records": [
            (45, "new-idea", "Buy", "Accumulation", 1.4, 0.85, 1.8, "bought"),
            (240, "position-review", "Hold", "Exhaustion", 1.1, 0.7, 1.3, None),
            (380, "position-review", "Reduce", "Exhaustion", 1.05, 0.7, 1.2, "reduced"),
        ],
    },
}

RECORD_TEMPLATE = """---
schema: decision-record/v1
symbol: {symbol}
market: {market}
date: {date}
mode: {mode}
price_at_decision: {price}
currency: {currency}
stance: {stance}
review_by: {review_by}
weighted_fair_value: {wfv}
scenarios: {{bear: {bear}, base: {wfv}, bull: {bull}}}
position_size: Starter
confidence: Medium
candidate_tier: Core Candidate
valuation_zone: {zone}
execution_method: No Action
triggers:
  add_on:
    - {{type: price, level: {add_level}, direction: below}}
{action_block}source_report: ../../reports/{date}-{symbol}-{mode}.md
---

[FICTIONAL] {symbol} {mode} note: deterministic demo record. All figures are
invented; this is not investment advice.
"""

REPORT_TEMPLATE = """# {symbol} — {mode} ({date}) [FICTIONAL]

## 1. Summary

Deterministic demo report for {symbol}. Every number is invented.

## 2. Valuation

| scenario | value |
| --- | --- |
| bear | {bear} |
| base | {wfv} |
| bull | {bull} |
"""


def walk(start_price, segments, start_day, rng):
    prices, day, price = {}, start_day, start_price
    for length, drift, vol in segments:
        for _ in range(length):
            if day.weekday() < 5:
                price = max(1.0, price * (1 + rng.gauss(drift, vol)))
                prices[day] = round(price, 2)
            day += datetime.timedelta(days=1)
    return prices


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True, help="series end date, ISO")
    args = parser.parse_args()
    as_of = datetime.date.fromisoformat(args.as_of)
    rng = random.Random(SEED)

    closes_doc = {}
    for symbol, spec in FICTION.items():
        total_days = sum(length for length, _, _ in spec["segments"])
        start_day = as_of - datetime.timedelta(days=total_days)
        series = walk(spec["start_price"], spec["segments"], start_day, rng)
        closes_doc[symbol] = {
            "splits": [],
            "closes": {d.isoformat(): px for d, px in sorted(series.items())}}

        rec_dir = DEMO / "state-home" / "records" / symbol
        rep_dir = DEMO / "state-home" / "reports"
        rec_dir.mkdir(parents=True, exist_ok=True)
        rep_dir.mkdir(parents=True, exist_ok=True)
        index_rows = []
        trading_days = sorted(series)
        last_offset = spec["records"][-1][0]
        for offset, mode, stance, zone, wfv_m, bear_m, bull_m, action in spec["records"]:
            day = min((d for d in trading_days
                       if d >= start_day + datetime.timedelta(days=offset)),
                      default=trading_days[-1])
            price = series[day]
            wfv = round(price * wfv_m, 2)
            bear = round(price * bear_m, 2)
            bull = round(price * bull_m, 2)
            action_block = ""
            if action:
                action_block = (f"action_taken: {{action: {action}, "
                                f"date: {day.isoformat()}, instrument: shares, "
                                f"note: demo action}}\n")
            # the latest record stays un-stale so the demo board isn't a wall
            # of dashed cards; earlier records age out naturally
            review_by = (as_of + datetime.timedelta(days=60) if offset == last_offset
                         else day + datetime.timedelta(days=120))
            record = RECORD_TEMPLATE.format(
                symbol=symbol, market=spec["market"], date=day.isoformat(),
                mode=mode, price=price, currency=spec["currency"],
                stance=stance, review_by=review_by.isoformat(),
                wfv=wfv, bear=bear, bull=bull, zone=zone,
                add_level=round(bear * 1.05, 2), action_block=action_block)
            (rec_dir / f"{day.isoformat()}-{mode}.md").write_text(
                record, encoding="utf-8")
            (rep_dir / f"{day.isoformat()}-{symbol}-{mode}.md").write_text(
                REPORT_TEMPLATE.format(symbol=symbol, mode=mode,
                                       date=day.isoformat(), bear=bear,
                                       wfv=wfv, bull=bull), encoding="utf-8")
            index_rows.append(
                f"| {day.isoformat()} | {mode} | {stance} | {zone} | {wfv} | "
                f"{price} | [record]({day.isoformat()}-{mode}.md) | "
                f"[report](../../reports/{day.isoformat()}-{symbol}-{mode}.md) |")
        (rec_dir / "INDEX.md").write_text(
            f"# {symbol} — decision index\n\n"
            "| date | mode | stance | zone | wfv | price | record | report |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
            + "\n".join(index_rows) + "\n", encoding="utf-8")

    (DEMO / "state-home" / "portfolio.yaml").write_text(yaml.safe_dump({
        "holdings": [{"symbol": "ORCA", "qty": 100, "avg_cost": 42.0,
                      "currency": "USD"}],
        "option_legs": [],
    }, sort_keys=False), encoding="utf-8")
    (DEMO / "prices.yaml").write_text(
        yaml.safe_dump(closes_doc, sort_keys=True), encoding="utf-8")
    print(f"demo vault written under {DEMO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Generate and build the demo**

```bash
.venv/bin/python scripts/make_demo_vault.py --as-of 2026-08-11
.venv/bin/python scripts/export_web.py --home demo/state-home --offline --prices demo/prices.yaml --as-of 2026-08-11 --dataset demo --out demo/dataset.json
.venv/bin/python scripts/build_webapp.py --data demo/dataset.json --out webapp_demo_out --demo
open webapp_demo_out/index.html
```

Expected: board with ORCA/BEACON across zones, demo banner on every page;
ORCA timeline shows matured P2 chips (records are old enough) — the honest
matured rendering the private build won't show until 2026-10. Note
`demo/dataset.json` is a build artifact — do **not** commit it; add
`demo/dataset.json` to `.gitignore`.

- [ ] **Step 3: Add a regression test** (append to `tests/test_export_web.py`)

```python
class DemoVaultTests(unittest.TestCase):
    def test_demo_vault_exports_clean(self):
        if not HAS_MARKDOWN:
            raise unittest.SkipTest("markdown not installed")
        demo_home = REPO_ROOT / "demo" / "state-home"
        demo_prices = REPO_ROOT / "demo" / "prices.yaml"
        if not demo_home.exists():
            raise unittest.SkipTest("demo vault not generated")
        provider = ew.FileHistoryProvider(demo_prices)
        payload = ew.export_dataset(demo_home, provider,
                                    datetime.date(2026, 8, 11),
                                    dataset="demo", include_sim=False, fx=None)
        self.assertEqual(payload["dataset"], "demo")
        self.assertGreaterEqual(len(payload["board"]["cards"]), 2)
        self.assertEqual(payload["warnings"], [])
        blob = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("investing-home", blob)
```

Run: `.venv/bin/python -m unittest tests.test_export_web.DemoVaultTests -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/make_demo_vault.py demo/ tests/test_export_web.py .gitignore
git commit -m "feat(webapp): seeded fictional demo vault + demo build path"
```

---

### Task 14: GitHub Pages demo workflow

**Files:**
- Create: `.github/workflows/deploy-demo.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: deploy-demo

on:
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - "demo/**"
      - "webapp/**"
      - "scripts/export_web.py"
      - "scripts/build_webapp.py"
      - ".github/workflows/deploy-demo.yml"

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install
        run: pip install pyyaml markdown
      - name: Export demo dataset (offline, committed fictional vault)
        run: |
          python scripts/export_web.py --home demo/state-home --offline \
            --prices demo/prices.yaml --dataset demo --out demo/dataset.json
      - name: Build demo site
        run: python scripts/build_webapp.py --data demo/dataset.json --out webapp_demo_out --demo
      - name: Privacy check — no private strings in the artifact
        run: |
          python - <<'EOF'
          import json, pathlib, sys
          payload = json.loads(pathlib.Path("demo/dataset.json").read_text())
          assert payload["dataset"] == "demo", "refusing: dataset not tagged demo"
          bad = ["investing-home", "personal_projects/investment"]
          for page in pathlib.Path("webapp_demo_out").rglob("*.html"):
              text = page.read_text(encoding="utf-8")
              for needle in bad:
                  assert needle not in text, f"{needle} leaked into {page}"
          print("privacy check ok")
          EOF
      - uses: actions/upload-pages-artifact@v3
        with:
          path: webapp_demo_out
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Validate the YAML locally**

Run: `.venv/bin/python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/deploy-demo.yml').read_text()); print('yaml ok')"`
Expected: `yaml ok`. (The workflow itself is exercised on the first
manual dispatch after merge — enabling GitHub Pages for the repo is a
one-time Settings step the owner does by hand.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy-demo.yml
git commit -m "ci(webapp): GitHub Pages demo deploy (manual dispatch + demo-path pushes)"
```

---

### Task 15: Final verification + docs

**Files:**
- Modify: `README.md` (short webapp section)
- Verify: everything

- [ ] **Step 1: Full suite + repo validation**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: all green. (`validate_repo` needs no registration changes — no new
skill was added.)

- [ ] **Step 2: Fixture end-to-end**

Re-run Task 10 Step 6's three commands. Expected: site opens over `file://`,
both views render, browser devtools network tab shows zero external requests.

- [ ] **Step 3: Real end-to-end (manual, private — design doc Verification 4)**

```bash
.venv/bin/python scripts/export_web.py --dataset private --out .webapp_cache/private-dataset.json
.venv/bin/python scripts/build_webapp.py --data .webapp_cache/private-dataset.json --out webapp_out
open webapp_out/index.html
```

Expected against the retained prototypes
(`.scratch/stock-analysis-web-app/prototypes/`): same cards/bands/report
rendering; Missing Inputs column populated; the JP symbol renders; the
delisted symbol shows 无价格; extreme-discount card clamps; basket reports
anchor-jump; P2 chips all-pending with maturity dates; sim toggle works and
is amber-tagged. Fix discrepancies before closing.

- [ ] **Step 4: README section**

Add to `README.md`, after the monitoring/scoring pipeline sections (match the
document's existing tone; include the zh-CN mirror if the README maintains
one):

```markdown
## Web view (read-only projection)

Two static views over the private state home — a Zone Board (which symbols
sit in which recorded valuation zone, with mechanical signals) and a
per-symbol Thesis Timeline (price vs the scenario bands each record drew,
with the full report chain). The vault stays the only source of truth; the
site is regenerated by hand and opens over `file://` with zero network.

    .venv/bin/python scripts/export_web.py --dataset private --out .webapp_cache/private-dataset.json
    .venv/bin/python scripts/build_webapp.py --data .webapp_cache/private-dataset.json --out webapp_out

A sanitized fictional demo (same pipeline, committed demo vault) deploys to
GitHub Pages via `.github/workflows/deploy-demo.yml`. Design:
`docs/plans/2026-08-11-web-app-design.md`.
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: webapp section in README"
```

---

## Self-review notes (already applied)

- Same-day double record: card + band both resolve via `band_record_for_date`
  (min `MODE_PRIORITY` rank — `validate_records` semantics, **not** the
  inverted prototype-06 map).
- All P2 scoring runs on the split-adjusted basis (`_meta_adjusted`), fixing
  a latent factor-mismatch the prototypes never hit (their factors were 1).
- `markdown` is lazy + `skipUnless`-gated, so the pyyaml-only CI job stays
  clean; renderer tests run in the venv and the inflection CI job.
- Builder tests use a hand-rolled dataset so they run without `markdown`.
- Prototype directories are **retained** (user decision 2026-08-11,
  overriding the earlier delete-after-landing note) as the Task 10/11/15
  comparison reference; nothing under `.scratch/` is ever committed.
