# Decision Records & Portfolio State (P0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the decision-records & portfolio-state contract from `docs/plans/2026-07-03-decision-records-design.md` — a private state home with per-symbol decision records, per-symbol INDEX timelines, and a portfolio snapshot, plus the framework-side read/write contract, validator, and contract tests.

**Architecture:** The public repo gains one normative reference doc (`decision-records.md`), contract edits to two skills, a PyYAML-based validator (`scripts/validate_records.py`) with `--reindex`, and contract/behavior tests against a fictional fixture state home. Real state lives only in the owner's private directory, discovered via the `~/.investing-home` pointer file. Tasks 9–11 are operational (private data, interactive) and must run inline with the user, not in subagents.

**Tech Stack:** Python 3.9+ (CI floor), `unittest` (repo standard, run via `discover`), PyYAML (the one new dependency), string-level contract tests in the existing `tests/test_skill_contracts.py` style.

**Spec:** `docs/plans/2026-07-03-decision-records-design.md` (normative). Read it before starting.

---

## Execution Rules

- One task per commit. Do not batch. Avoid unrelated cleanup.
- TDD for every code task: write the failing test, watch it fail, implement, watch it pass, commit.
- Local Python: create `.venv` in the repo root (Task 1) and use `.venv/bin/python` for every command below. Do NOT use the global interpreter (user's global site-packages are broken).
- Commit messages: repo style is plain imperative ("Add X", "Wire Y"). End every commit message with the harness's standard `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` footer.
- Privacy hard rule: no real tickers the owner has analyzed, no real paths from the owner's machine, and no real holdings anywhere in this repo — fixtures and doc examples use `ACME`, `1234.HK`, `600001.SH` style fictional data only.

## File Structure

| Path | Action | Responsibility |
| --- | --- | --- |
| `.github/workflows/ci.yml` | Modify | Install PyYAML before tests |
| `.gitignore` | Modify | Ignore `.venv/` |
| `skills/analyzing-stocks/references/decision-records.md` | Create | Normative contract: state home, record schema, INDEX format, portfolio schema, symbol rules |
| `scripts/validate_repo.py` | Modify | Require the new reference in the full profile |
| `scripts/validate_records.py` | Create | Validate a state home; `--reindex` rebuilds INDEX files |
| `tests/fixtures/state-home/**` | Create | Fictional good state home for validator tests |
| `tests/test_decision_records.py` | Create | Vocabulary-sync contract tests + validator behavior tests |
| `skills/investment-decision-workflow/SKILL.md` | Modify | State-home resolution, stale-check auto-anchor, Output Contract §6 |
| `skills/analyzing-stocks/SKILL.md` | Modify | Load new reference (Step 4), emit archive-ready frontmatter (Step 7) |

---

### Task 1: Dependencies — PyYAML in CI, local venv, gitignore

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitignore`

- [ ] **Step 1: Add the install step to CI**

In `.github/workflows/ci.yml`, insert between the `Show versions` step and the `Unit + contract + e2e tests` step:

```yaml
      - name: Install test dependencies
        run: pip install pyyaml
```

- [ ] **Step 2: Ignore local virtualenvs**

Append to `.gitignore` (it currently ends with `.omx/`):

```
.venv/
```

- [ ] **Step 3: Create the local venv and install PyYAML**

```bash
python3 -m venv .venv && .venv/bin/pip install --quiet pyyaml
.venv/bin/python -c "import yaml; print(yaml.__version__)"
```

Expected: a version number prints (e.g. `6.0.x`), no traceback.

- [ ] **Step 4: Confirm existing suite still passes under the venv interpreter**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all existing tests PASS (no new tests yet).

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml .gitignore
git commit -m "Add PyYAML test dependency to CI; ignore local venv"
```

---

### Task 2: `decision-records.md` reference + vocabulary contract tests + repo wiring

**Files:**
- Create: `skills/analyzing-stocks/references/decision-records.md`
- Modify: `scripts/validate_repo.py` (FULL_REQUIRED list)
- Test: `tests/test_decision_records.py` (new file, first test classes)

- [ ] **Step 1: Write the failing contract tests**

Create `tests/test_decision_records.py`:

```python
"""Contract tests for the decision-records & portfolio-state layer (P0).

Spec: docs/plans/2026-07-03-decision-records-design.md
Normative doc under test: skills/analyzing-stocks/references/decision-records.md
"""

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

DECISION_RECORDS = "skills/analyzing-stocks/references/decision-records.md"
CONTROLLER = "skills/analyzing-stocks/SKILL.md"
TEMPLATE = "skills/analyzing-stocks/references/report-template.md"
WORKFLOW = "skills/investment-decision-workflow/SKILL.md"


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class VocabularySyncTests(unittest.TestCase):
    """Every enum in decision-records.md must literally match its source skill."""

    def test_reference_exists(self) -> None:
        self.assertTrue((REPO_ROOT / DECISION_RECORDS).exists())

    def test_stance_vocabulary_matches_controller_template_and_workflow(self) -> None:
        expected = "`Buy / Add / Hold / Reduce / Avoid`"
        for path in (DECISION_RECORDS, CONTROLLER, TEMPLATE, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing stance vocabulary")

    def test_position_size_vocabulary_matches(self) -> None:
        expected = "`Core / Starter / Speculative / Watch-Avoid`"
        for path in (DECISION_RECORDS, TEMPLATE, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing position-size vocabulary")

    def test_confidence_vocabulary_matches_template(self) -> None:
        expected = "`High / Medium / Low`"
        for path in (DECISION_RECORDS, TEMPLATE):
            self.assertIn(expected, read(path), f"{path} missing confidence vocabulary")

    def test_candidate_tier_vocabulary_matches_workflow(self) -> None:
        expected = "`Core Candidate / Tactical Candidate / Reject`"
        for path in (DECISION_RECORDS, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing candidate-tier vocabulary")

    def test_valuation_zone_vocabulary_matches_workflow(self) -> None:
        expected = "`Accumulation / Hold / Exhaustion / Invalidation`"
        for path in (DECISION_RECORDS, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing valuation-zone vocabulary")

    def test_execution_method_vocabulary_pinned_to_workflow_execution_sheet(self) -> None:
        expected = "`Buy now / Stage buy / Sell cash-secured put / Wait / Reduce / Exit / No Action`"
        workflow = read(WORKFLOW)
        self.assertIn("### 5. Execution Sheet", workflow)
        self.assertIn(expected, workflow)
        self.assertIn(expected, read(DECISION_RECORDS))

    def test_mode_slug_table_maps_workflow_mode_names(self) -> None:
        doc = read(DECISION_RECORDS)
        for slug, display in [
            ("new-idea", "New Idea Decision"),
            ("existing-report", "Existing Report to Action"),
            ("position-review", "Position Review"),
            ("event-review", "Event Review"),
        ]:
            self.assertIn(slug, doc, f"mode slug {slug!r} missing")
            self.assertIn(display, doc, f"mode display {display!r} missing")
            self.assertIn(display, read(WORKFLOW))
        # research is record-only; historical is index-only.
        self.assertIn("research", doc)
        self.assertIn("historical", doc)

    def test_record_identity_and_tiebreak_are_stated(self) -> None:
        doc = read(DECISION_RECORDS)
        self.assertIn("(symbol, date, mode)", doc)
        self.assertIn("position-review > event-review > existing-report > new-idea > research", doc)

    def test_canonical_symbol_rules_are_stated(self) -> None:
        doc = read(DECISION_RECORDS)
        for expected in ("`NVDA`", "`0700.HK`", "`600519.SH`", "related_symbols"):
            self.assertIn(expected, doc)


class RepoWiringTests(unittest.TestCase):
    def test_full_profile_requires_decision_records_reference(self) -> None:
        validator = read("scripts/validate_repo.py")
        self.assertIn(
            "skills/analyzing-stocks/references/decision-records.md", validator
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
```

Expected: FAIL — `test_reference_exists` and the vocabulary tests fail (file missing), `RepoWiringTests` fails (string absent).

- [ ] **Step 3: Create the normative reference doc**

Create `skills/analyzing-stocks/references/decision-records.md` with exactly this content:

````markdown
# Decision Records & Portfolio State

## Objective

Give the framework memory. Every decision persists as a machine-readable record
in a private **state home**; holdings live in one `portfolio.yaml`; each symbol
gets a chronological timeline. Skills read this state instead of asking the user
to re-dictate holdings and paste old reports.

All examples in this file are fictional.

## State Home Resolution

The state home is a private directory outside this repository. Skills locate it
via the pointer file `~/.investing-home` (one line: the absolute path).

1. Read `~/.investing-home`; trim whitespace; the result is the state-home path.
2. If the pointer file is missing, ask the user once per session, offer to
   create the pointer and the state-home skeleton, then continue. A user who
   declines runs stateless; a later session may ask again.
3. If the pointer exists but the directory is missing or unreadable, say so and
   fall back to stateless behavior (ask for inputs, emit `Missing Inputs`).
   Never invent state.

## State Home Layout

```
<state-home>/
├── portfolio.yaml              # single portfolio snapshot
└── records/
    └── <SYMBOL>/               # canonical symbol, one dir per name
        ├── INDEX.md            # per-symbol decision timeline
        └── YYYY-MM-DD-<mode>.md    # one decision record
```

## Canonical Symbol Form

Directory names and the `symbol:` field use one canonical form:

- US: bare ticker, uppercase — `NVDA`
- Hong Kong: HKEX code zero-padded to 4 digits + `.HK` — `0700.HK`
  (normalize `00700` / `00883-HK` input forms); genuine 5-digit codes
  (e.g. RMB counters) stay 5 digits
- China A-share: 6-digit code + `.SH` / `.SZ` / `.BJ` — `600519.SH`

The canonical form is an internal identity (human-dominant convention), not a
data-provider format: yfinance wants `600519.SS` for Shanghai, akshare wants
bare `600519`. Later phases own a canonical→provider mapping.

**Dual listings / ADRs:** a record anchors to the tradable line actually
analyzed, so related lines get separate directories. Link them with the
optional `related_symbols:` frontmatter field; the validator mirrors it as a
`See also:` line in both symbols' `INDEX.md` headers. Do not merge directories.

## Decision Record

One markdown file per **symbol × decision**. Record identity is
`(symbol, date, mode)` — also the INDEX row key and the filename
(`YYYY-MM-DD-<mode>.md`). A rerun with the same identity updates the record and
its row in place. For "latest record" on a same-date tie, use mode priority
`position-review > event-review > existing-report > new-idea > research`.

Write a record when the session produced at least a `stance` or an
`execution_method` for the symbol; a pure `Missing Inputs` / conditional-only
outcome creates no record.

The body must be self-contained: for single-name runs, the full report; for
multi-name runs, that symbol's complete per-name sections. `source_report`
links the full session report when it exists in the state home (else `null`).

### Frontmatter schema (`decision-record/v1`)

```yaml
---
schema: decision-record/v1
symbol: ACME                  # canonical form
market: US                    # US | CN | HK
date: 2026-06-01
mode: new-idea                # new-idea | existing-report | position-review | event-review | research
price_at_decision: 100.0
currency: USD

# Research & valuation (required when a full valuation backs the decision)
stance: Buy
position_size: Starter
confidence: Medium
weighted_fair_value: 140
scenarios: {bear: 80, base: 135, bull: 190}

# Decision & execution (required when the decision workflow ran)
candidate_tier: Core Candidate
valuation_zone: Accumulation
execution_method: Stage buy
triggers:
  add_on:
    - {type: price, level: 90, direction: below}
    - {type: kpi, text: "fictional KPI recovers two quarters running"}
  trim_exit:
    - {type: price, level: 185, direction: above}
monitor:
  - {kpi: "fictional revenue growth", threshold: "< 5%", action: "revisit Base"}

next_earnings: 2026-08-20     # null if unknown
review_by: 2026-09-01         # staleness date, always required
related_symbols: []           # optional cross-listing links
source_report: null           # relative to state home; null if absent
action_taken: null            # backfilled after confirmed execution
---
```

### Field rules

- Required always: `schema, symbol, market, date, mode, price_at_decision,
  currency, stance, review_by`.
- Required together when a full valuation backs the decision:
  `weighted_fair_value, scenarios, position_size, confidence`.
- Required together when the decision workflow ran: `candidate_tier,
  valuation_zone, execution_method, triggers`.
- `mode: research` marks a standalone `analyzing-stocks` run saved without the
  decision workflow; workflow-only fields stay absent. The writing skill sets
  `review_by` explicitly; default when the user states none:
  `min(next_earnings, date + 90 days)`.
- Enum fields store the skills' display strings verbatim. Vocabulary (sources
  in parentheses):
  - `stance`: `Buy / Add / Hold / Reduce / Avoid` (controller, template, workflow)
  - `position_size`: `Core / Starter / Speculative / Watch-Avoid` (template, workflow)
  - `confidence`: `High / Medium / Low` (template)
  - `candidate_tier`: `Core Candidate / Tactical Candidate / Reject` (workflow)
  - `valuation_zone`: `Accumulation / Hold / Exhaustion / Invalidation` (workflow)
  - `execution_method`: `Buy now / Stage buy / Sell cash-secured put / Wait / Reduce / Exit / No Action`
    (workflow Output Contract, `### 5. Execution Sheet` line; `Reduce` and
    `Exit` are distinct values here)
- The one slugged exception is `mode` (it appears in filenames). Slug ↔ display
  mapping onto the workflow's modes:
  - `new-idea` ↔ `New Idea Decision`
  - `existing-report` ↔ `Existing Report to Action`
  - `position-review` ↔ `Position Review`
  - `event-review` ↔ `Event Review`
  - `research` — record-only, no workflow counterpart
  - `historical` — index-only (see below), never a record mode
- Price-type triggers are structured (`{type: price, level: <number>,
  direction: above|below}`) so scripts can check them; `kpi`/`event` triggers
  carry free text for LLM checking.
- `action_taken` starts `null`; backfill only after the user confirms an
  execution. `action_taken.action` vocabulary (v1):
  `bought | added | reduced | exited | sold-put | put-assigned | put-closed`;
  a `date` is required alongside.
- Amounts are in `currency`; no FX conversion inside records.

## Per-Symbol Timeline: `INDEX.md`

One table row per decision, oldest first, so the file reads as the thesis
evolution timeline:

```markdown
# ACME — Decision Timeline

See also: [1234.HK](../1234.HK/INDEX.md)

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-01 | historical | — | — | — | — | — | [report](../../equity_research_2026-05-01/acme-note.md) |
| 2026-06-01 | new-idea | 100.0 USD | Buy | 140 | Stage buy | [record](2026-06-01-new-idea.md) | — |
```

- The writing skill appends/updates the row keyed by `(symbol, date, mode)`
  whenever it writes a record.
- Record rows are derived data: `scripts/validate_records.py` checks the
  record ↔ row bijection and `--reindex` rebuilds them from frontmatter.
- Sort key: `date` ascending; same-date ties order `historical` rows first,
  then record rows by mode priority. `--reindex` applies the same key.
- `historical` rows are index-only backfill entries for old reports: preserved
  verbatim by `--reindex`; their only integrity check is that the report link
  resolves. If an old report is later hand-converted into a real record, the
  conversion replaces its `historical` row.
- Obsidian note: nested frontmatter renders as non-editable "complex"
  properties — harmless; INDEX tables and links are the browsing surface.

## Portfolio State: `portfolio.yaml`

```yaml
schema: portfolio/v1
as_of: 2026-07-01
base_currency: USD
cash: {USD: 10000, HKD: 20000}
holdings:
  - {symbol: ACME, qty: 10, avg_cost: 101.5, currency: USD,
     opened: 2026-06-02, thesis_record: records/ACME/2026-06-01-new-idea.md}
option_legs:
  - {kind: cash-secured-put, underlying: ACME, strike: 90, expiry: 2026-09-18,
     qty: -1, premium: 3.5, currency: USD, opened: 2026-06-15, multiplier: 100}
constraints:
  single_name_cap_pct: 10
  cash_reserve_floor_pct: 15
```

- Skills treat `portfolio.yaml` as the source of truth when present, but an
  explicit in-session user statement overrides it; write the correction back
  after user confirmation.
- Assignment reserve for cash-secured puts is computed
  (`strike × multiplier × |qty|`), not stored. `multiplier` defaults to 100 and
  must be set explicitly for other contract sizes. `underlying` and `symbol`
  use the canonical form.
- `constraints` feeds the workflow's Portfolio Risk Budget verbatim.

## Validation

```
python scripts/validate_records.py --home <state-home>   # check
python scripts/validate_records.py --home <state-home> --reindex   # rebuild INDEX files, then check
```

Without `--home`, the script resolves `~/.investing-home`. Exit code 0 = clean;
1 = violations (printed one per line); 2 = environment error.
````

- [ ] **Step 4: Wire the reference into the repo validator**

In `scripts/validate_repo.py`, in `FULL_REQUIRED`, insert after the
`capital-allocation.md` line:

```python
    "skills/analyzing-stocks/references/decision-records.md",
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: all new tests PASS; validator prints `Repository validation passed for profile: full`.

- [ ] **Step 6: Commit**

```bash
git add skills/analyzing-stocks/references/decision-records.md scripts/validate_repo.py tests/test_decision_records.py
git commit -m "Add decision-records reference with vocabulary contract tests"
```

---

### Task 3: Fixture state home + record-level validation in `validate_records.py`

**Files:**
- Create: `tests/fixtures/state-home/` (7 files, below)
- Create: `scripts/validate_records.py`
- Test: `tests/test_decision_records.py` (append `RecordValidationTests`)

- [ ] **Step 1: Create the fixture state home (fictional data)**

`tests/fixtures/state-home/portfolio.yaml`:

```yaml
schema: portfolio/v1
as_of: 2026-07-01
base_currency: USD
cash: {USD: 10000, HKD: 20000}
holdings:
  - {symbol: ACME, qty: 10, avg_cost: 101.5, currency: USD,
     opened: 2026-06-02, thesis_record: records/ACME/2026-06-01-new-idea.md}
option_legs:
  - {kind: cash-secured-put, underlying: ACME, strike: 90, expiry: 2026-09-18,
     qty: -1, premium: 3.5, currency: USD, opened: 2026-06-15, multiplier: 100}
constraints:
  single_name_cap_pct: 10
  cash_reserve_floor_pct: 15
```

`tests/fixtures/state-home/records/ACME/2026-06-01-new-idea.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-06-01
mode: new-idea
price_at_decision: 100.0
currency: USD
stance: Buy
position_size: Starter
confidence: Medium
weighted_fair_value: 140
scenarios: {bear: 80, base: 135, bull: 190}
candidate_tier: Core Candidate
valuation_zone: Accumulation
execution_method: Stage buy
triggers:
  add_on:
    - {type: price, level: 90, direction: below}
  trim_exit:
    - {type: price, level: 185, direction: above}
    - {type: kpi, text: "fictional KPI deteriorates two quarters running"}
monitor:
  - {kpi: "fictional revenue growth", threshold: "< 5%", action: "revisit Base"}
next_earnings: 2026-08-20
review_by: 2026-09-01
related_symbols: [1234.HK]
source_report: null
action_taken: {action: bought, qty: 10, price: 101.5, date: 2026-06-02}
---

# ACME — new idea (fixture)

Fictional record body for validator tests.
```

`tests/fixtures/state-home/records/ACME/2026-07-01-position-review.md`:

```markdown
---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-07-01
mode: position-review
price_at_decision: 110.0
currency: USD
stance: Hold
position_size: Starter
confidence: Medium
weighted_fair_value: 140
scenarios: {bear: 80, base: 135, bull: 190}
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: No Action
triggers:
  add_on:
    - {type: price, level: 90, direction: below}
  trim_exit:
    - {type: price, level: 185, direction: above}
next_earnings: 2026-08-20
review_by: 2026-10-01
related_symbols: [1234.HK]
source_report: null
action_taken: null
---

# ACME — position review (fixture)

Fictional record body.
```

`tests/fixtures/state-home/records/ACME/INDEX.md`:

```markdown
# ACME — Decision Timeline

See also: [1234.HK](../1234.HK/INDEX.md)

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-01 | new-idea | 100.0 USD | Buy | 140 | Stage buy | [record](2026-06-01-new-idea.md) | — |
| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |
```

`tests/fixtures/state-home/records/1234.HK/2026-07-02-research.md`:

```markdown
---
schema: decision-record/v1
symbol: 1234.HK
market: HK
date: 2026-07-02
mode: research
price_at_decision: 25.0
currency: HKD
stance: Hold
position_size: Watch-Avoid
confidence: Low
weighted_fair_value: 32
scenarios: {bear: 18, base: 30, bull: 45}
next_earnings: null
review_by: 2026-09-30
related_symbols: [ACME]
source_report: equity_research_2026-05-01/1234-hk-note.md
action_taken: null
---

# 1234.HK — research (fixture)

Fictional standalone research record.
```

`tests/fixtures/state-home/records/1234.HK/INDEX.md`:

```markdown
# 1234.HK — Decision Timeline

See also: [ACME](../ACME/INDEX.md)

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-01 | historical | — | — | — | — | — | [report](../../equity_research_2026-05-01/1234-hk-note.md) |
| 2026-07-02 | research | 25.0 HKD | Hold | 32 | — | [record](2026-07-02-research.md) | [report](../../equity_research_2026-05-01/1234-hk-note.md) |
```

`tests/fixtures/state-home/equity_research_2026-05-01/1234-hk-note.md`:

```markdown
# 1234.HK old research note (fixture)

Fictional legacy report referenced by a historical INDEX row.
```

- [ ] **Step 2: Append the failing validator tests**

Append to `tests/test_decision_records.py` (add `import shutil`, `import subprocess`, `import sys`, `import tempfile` at the top, keeping `pathlib` and `unittest`):

```python
FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "state-home"
VALIDATOR = REPO_ROOT / "scripts" / "validate_records.py"


def run_validator(home: pathlib.Path, *extra: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--home", str(home), *extra],
        capture_output=True,
        text=True,
    )


class StateHomeTestCase(unittest.TestCase):
    """Copies the fixture home to a temp dir so mutations are isolated."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self._tmp.name) / "home"
        shutil.copytree(FIXTURE_HOME, self.home)
        self.addCleanup(self._tmp.cleanup)

    def mutate(self, relative_path: str, old: str, new: str) -> None:
        path = self.home / relative_path
        text = path.read_text(encoding="utf-8")
        assert old in text, f"mutation target not found in {relative_path}: {old!r}"
        path.write_text(text.replace(old, new), encoding="utf-8")


class RecordValidationTests(StateHomeTestCase):
    def test_good_fixture_home_passes(self) -> None:
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_bad_stance_fails(self) -> None:
        self.mutate("records/ACME/2026-06-01-new-idea.md", "stance: Buy", "stance: StrongBuy")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stance", result.stdout)

    def test_missing_review_by_fails(self) -> None:
        self.mutate("records/ACME/2026-06-01-new-idea.md", "review_by: 2026-09-01", "reviewed: 2026-09-01")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("review_by", result.stdout)

    def test_non_canonical_symbol_dir_fails(self) -> None:
        (self.home / "records" / "1234.HK").rename(self.home / "records" / "01234-HK")
        self.mutate("records/01234-HK/2026-07-02-research.md", "symbol: 1234.HK", "symbol: 01234-HK")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_filename_identity_mismatch_fails(self) -> None:
        (self.home / "records" / "ACME" / "2026-06-01-new-idea.md").rename(
            self.home / "records" / "ACME" / "2026-06-02-new-idea.md"
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("identity", result.stdout)

    def test_incomplete_workflow_group_fails(self) -> None:
        self.mutate(
            "records/ACME/2026-07-01-position-review.md",
            "candidate_tier: Core Candidate\n",
            "",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("candidate_tier", result.stdout)

    def test_dangling_source_report_fails(self) -> None:
        self.mutate(
            "records/1234.HK/2026-07-02-research.md",
            "source_report: equity_research_2026-05-01/1234-hk-note.md",
            "source_report: equity_research_2026-05-01/missing.md",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("source_report", result.stdout)
```

- [ ] **Step 3: Run to verify the new tests fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
```

Expected: `RecordValidationTests` all FAIL/ERROR (`validate_records.py` does not exist); earlier contract tests still pass.

- [ ] **Step 4: Implement record-level validation**

Create `scripts/validate_records.py`:

```python
#!/usr/bin/env python3
"""Validate a private investing state home against the decision-records contract.

Contract: skills/analyzing-stocks/references/decision-records.md
Spec:     docs/plans/2026-07-03-decision-records-design.md

Exit codes: 0 clean, 1 violations, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("validate_records.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

POINTER_FILE = Path.home() / ".investing-home"

STANCES = ("Buy", "Add", "Hold", "Reduce", "Avoid")
POSITION_SIZES = ("Core", "Starter", "Speculative", "Watch-Avoid")
CONFIDENCE_LEVELS = ("High", "Medium", "Low")
CANDIDATE_TIERS = ("Core Candidate", "Tactical Candidate", "Reject")
VALUATION_ZONES = ("Accumulation", "Hold", "Exhaustion", "Invalidation")
EXECUTION_METHODS = (
    "Buy now", "Stage buy", "Sell cash-secured put", "Wait",
    "Reduce", "Exit", "No Action",
)
MODES = ("new-idea", "existing-report", "position-review", "event-review", "research")
MODE_PRIORITY = {
    "position-review": 0, "event-review": 1, "existing-report": 2,
    "new-idea": 3, "research": 4,
}
ACTIONS = ("bought", "added", "reduced", "exited", "sold-put", "put-assigned", "put-closed")
TRIGGER_TYPES = ("price", "kpi", "event")
DIRECTIONS = ("above", "below")

SYMBOL_PATTERNS = {
    "US": re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,2})?$"),
    "HK": re.compile(r"^\d{4,5}\.HK$"),
    "CN": re.compile(r"^\d{6}\.(SH|SZ|BJ)$"),
}

REQUIRED_ALWAYS = (
    "schema", "symbol", "market", "date", "mode",
    "price_at_decision", "currency", "stance", "review_by",
)
VALUATION_GROUP = ("weighted_fair_value", "scenarios", "position_size", "confidence")
WORKFLOW_GROUP = ("candidate_tier", "valuation_zone", "execution_method", "triggers")

RECORD_FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z-]+)\.md$")
CURRENCY = re.compile(r"^[A-Z]{3}$")


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_date(value: object) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        return datetime.date.fromisoformat(value)
    raise ValueError(f"not a date: {value!r}")


def is_canonical(symbol: object) -> bool:
    return isinstance(symbol, str) and any(p.match(symbol) for p in SYMBOL_PATTERNS.values())


class Checker:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.errors: list[str] = []

    def err(self, path: Path, message: str) -> None:
        try:
            rel = path.relative_to(self.home)
        except ValueError:
            rel = path
        self.errors.append(f"{rel}: {message}")

    # ---------------- records ----------------

    def load_frontmatter(self, path: Path) -> "dict | None":
        parts = path.read_text(encoding="utf-8").split("---", 2)
        if len(parts) < 3 or parts[0].strip():
            self.err(path, "missing YAML frontmatter fences")
            return None
        try:
            meta = yaml.safe_load(parts[1])
        except yaml.YAMLError as exc:
            self.err(path, f"frontmatter is not valid YAML: {exc}")
            return None
        if not isinstance(meta, dict):
            self.err(path, "frontmatter is not a mapping")
            return None
        return meta

    def check_record(self, path: Path, symbol_dir: str) -> "dict | None":
        meta = self.load_frontmatter(path)
        if meta is None:
            return None

        missing = [key for key in REQUIRED_ALWAYS if key not in meta]
        if missing:
            self.err(path, f"missing required fields: {', '.join(missing)} (e.g. review_by)")
        if meta.get("schema") != "decision-record/v1":
            self.err(path, f"schema must be decision-record/v1, got {meta.get('schema')!r}")

        symbol = meta.get("symbol")
        if symbol != symbol_dir:
            self.err(path, f"symbol {symbol!r} does not match directory {symbol_dir!r}")
        market = meta.get("market")
        if market not in SYMBOL_PATTERNS:
            self.err(path, f"market must be one of US/CN/HK, got {market!r}")
        elif not (isinstance(symbol, str) and SYMBOL_PATTERNS[market].match(symbol)):
            self.err(path, f"symbol {symbol!r} is not canonical for market {market}")

        mode = meta.get("mode")
        if mode not in MODES:
            self.err(path, f"mode must be one of {MODES}, got {mode!r}")

        match = RECORD_FILENAME.match(path.name)
        if not match:
            self.err(path, "filename must be YYYY-MM-DD-<mode>.md")
        else:
            try:
                meta_date = as_date(meta.get("date"))
                if (match.group(1), match.group(2)) != (meta_date.isoformat(), mode):
                    self.err(path, "filename does not match record identity (date, mode)")
            except (ValueError, TypeError):
                self.err(path, f"date is not ISO: {meta.get('date')!r}")

        for field, vocab in (
            ("stance", STANCES),
            ("position_size", POSITION_SIZES),
            ("confidence", CONFIDENCE_LEVELS),
            ("candidate_tier", CANDIDATE_TIERS),
            ("valuation_zone", VALUATION_ZONES),
            ("execution_method", EXECUTION_METHODS),
        ):
            value = meta.get(field)
            if value is not None and value not in vocab:
                self.err(path, f"{field} {value!r} not in vocabulary {vocab}")

        if not is_number(meta.get("price_at_decision")) or meta.get("price_at_decision", 0) <= 0:
            self.err(path, f"price_at_decision must be a positive number, got {meta.get('price_at_decision')!r}")
        if not (isinstance(meta.get("currency"), str) and CURRENCY.match(meta["currency"])):
            self.err(path, f"currency must be a 3-letter code, got {meta.get('currency')!r}")
        for field in ("review_by", "next_earnings"):
            value = meta.get(field)
            if value is not None:
                try:
                    as_date(value)
                except (ValueError, TypeError):
                    self.err(path, f"{field} is not ISO: {value!r}")

        self._check_group(path, meta, VALUATION_GROUP)
        self._check_group(path, meta, WORKFLOW_GROUP)
        self._check_scenarios(path, meta)
        self._check_triggers(path, meta)
        self._check_action_taken(path, meta)

        related = meta.get("related_symbols") or []
        if not isinstance(related, list) or any(not is_canonical(s) for s in related):
            self.err(path, f"related_symbols must be a list of canonical symbols, got {related!r}")

        source = meta.get("source_report")
        if source is not None and not (self.home / source).exists():
            self.err(path, f"source_report does not resolve: {source!r}")

        return meta

    def _check_group(self, path: Path, meta: dict, group: "tuple[str, ...]") -> None:
        present = [key for key in group if meta.get(key) is not None]
        if present and len(present) != len(group):
            absent = [key for key in group if meta.get(key) is None]
            self.err(path, f"group incomplete: has {', '.join(present)} but missing {', '.join(absent)}")

    def _check_scenarios(self, path: Path, meta: dict) -> None:
        scenarios = meta.get("scenarios")
        if scenarios is None:
            return
        if not isinstance(scenarios, dict) or set(scenarios) != {"bear", "base", "bull"}:
            self.err(path, f"scenarios must have exactly bear/base/bull, got {scenarios!r}")
            return
        if any(not is_number(v) for v in scenarios.values()):
            self.err(path, f"scenarios values must be numbers, got {scenarios!r}")

    def _check_triggers(self, path: Path, meta: dict) -> None:
        triggers = meta.get("triggers")
        if triggers is None:
            return
        if not isinstance(triggers, dict) or not set(triggers) <= {"add_on", "trim_exit"}:
            self.err(path, "triggers must be a mapping with add_on/trim_exit lists")
            return
        for side, items in triggers.items():
            if not isinstance(items, list):
                self.err(path, f"triggers.{side} must be a list")
                continue
            for item in items:
                if not isinstance(item, dict) or item.get("type") not in TRIGGER_TYPES:
                    self.err(path, f"triggers.{side} item needs type in {TRIGGER_TYPES}: {item!r}")
                    continue
                if item["type"] == "price":
                    if not is_number(item.get("level")) or item.get("direction") not in DIRECTIONS:
                        self.err(path, f"price trigger needs numeric level and direction above/below: {item!r}")
                elif not isinstance(item.get("text"), str):
                    self.err(path, f"{item['type']} trigger needs text: {item!r}")

    def _check_action_taken(self, path: Path, meta: dict) -> None:
        action = meta.get("action_taken")
        if action is None:
            return
        if not isinstance(action, dict) or action.get("action") not in ACTIONS:
            self.err(path, f"action_taken.action must be in {ACTIONS}: {action!r}")
            return
        try:
            as_date(action.get("date"))
        except (ValueError, TypeError):
            self.err(path, f"action_taken.date is not ISO: {action!r}")

    # ---------------- walk ----------------

    def run(self) -> "list[str]":
        records_root = self.home / "records"
        if records_root.exists():
            for symbol_dir in sorted(p for p in records_root.iterdir() if p.is_dir()):
                if not is_canonical(symbol_dir.name):
                    self.err(symbol_dir, f"directory name {symbol_dir.name!r} is not a canonical symbol")
                for record_path in sorted(symbol_dir.glob("*.md")):
                    if record_path.name == "INDEX.md":
                        continue
                    self.check_record(record_path, symbol_dir.name)
        return self.errors


def resolve_home(arg: "str | None") -> Path:
    if arg:
        return Path(arg).expanduser()
    if POINTER_FILE.exists():
        return Path(POINTER_FILE.read_text(encoding="utf-8").strip()).expanduser()
    print(f"no --home given and {POINTER_FILE} does not exist", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an investing state home.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--reindex", action="store_true", help="rebuild INDEX.md files, then validate")
    args = parser.parse_args()

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2

    errors = Checker(home).run()
    if errors:
        print("State-home validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"State-home validation passed: {home}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

(`--reindex` is accepted but does nothing yet — implemented in Task 6.)

- [ ] **Step 5: Run the tests to verify they pass**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
```

Expected: all PASS (including the seven `RecordValidationTests`).

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_records.py tests/fixtures tests/test_decision_records.py
git commit -m "Add state-home validator: record schema checks with fixture home"
```

---

### Task 4: INDEX.md validation — bijection, historical rows, sort order, See-also

**Files:**
- Modify: `scripts/validate_records.py`
- Test: `tests/test_decision_records.py` (append `IndexValidationTests`)

- [ ] **Step 1: Append the failing tests**

```python
class IndexValidationTests(StateHomeTestCase):
    def test_missing_index_row_for_record_fails(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |\n",
            "",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no INDEX row", result.stdout)

    def test_index_row_without_record_fails(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review |",
            "| 2026-07-03 | position-review |",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no record file", result.stdout)

    def test_missing_index_file_fails(self) -> None:
        (self.home / "records" / "ACME" / "INDEX.md").unlink()
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INDEX.md missing", result.stdout)

    def test_dangling_historical_link_fails(self) -> None:
        self.mutate(
            "records/1234.HK/INDEX.md",
            "[report](../../equity_research_2026-05-01/1234-hk-note.md) |\n| 2026-07-02",
            "[report](../../equity_research_2026-05-01/gone.md) |\n| 2026-07-02",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("historical", result.stdout)

    def test_unsorted_rows_fail(self) -> None:
        index = self.home / "records" / "ACME" / "INDEX.md"
        text = index.read_text(encoding="utf-8")
        row1 = "| 2026-06-01 | new-idea | 100.0 USD | Buy | 140 | Stage buy | [record](2026-06-01-new-idea.md) | — |"
        row2 = "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |"
        index.write_text(text.replace(row1 + "\n" + row2, row2 + "\n" + row1), encoding="utf-8")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("sorted", result.stdout)

    def test_missing_see_also_fails(self) -> None:
        self.mutate("records/ACME/INDEX.md", "See also: [1234.HK](../1234.HK/INDEX.md)\n", "")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("See also", result.stdout)
```

- [ ] **Step 2: Run to verify the new tests fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records.IndexValidationTests -v
```

Expected: all six FAIL (index checks not implemented).

- [ ] **Step 3: Implement index validation**

In `scripts/validate_records.py`, add to the `Checker` class (and call from `run()`):

```python
    # ---------------- index ----------------

    @staticmethod
    def parse_index_rows(path: Path) -> "list[list[str]]":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) != 8 or cells[0] == "date" or set(cells[0]) <= {"-", ":", " "}:
                continue
            rows.append(cells)
        return rows

    def check_index(self, symbol_dir: Path, record_metas: "dict[tuple[str, str], dict]") -> None:
        index_path = symbol_dir / "INDEX.md"
        if not index_path.exists():
            if record_metas:
                self.err(symbol_dir, "INDEX.md missing but records exist")
            return
        rows = self.parse_index_rows(index_path)

        row_keys = []
        for cells in rows:
            date_cell, mode_cell = cells[0], cells[1]
            row_keys.append((date_cell, mode_cell))
            if mode_cell == "historical":
                match = re.search(r"\]\(([^)]+)\)", cells[7])
                target = (symbol_dir / match.group(1)).resolve() if match else None
                if target is None or not target.exists():
                    self.err(index_path, f"historical row {date_cell}: report link does not resolve")
            elif (date_cell, mode_cell) not in record_metas:
                self.err(index_path, f"row ({date_cell}, {mode_cell}) has no record file")

        for key in record_metas:
            if key not in row_keys:
                self.err(index_path, f"record {key[0]}-{key[1]}.md has no INDEX row")

        def sort_key(cells: "list[str]"):
            kind = 0 if cells[1] == "historical" else 1
            return (cells[0], kind, MODE_PRIORITY.get(cells[1], 99))

        if [sort_key(c) for c in rows] != sorted(sort_key(c) for c in rows):
            self.err(index_path, "rows are not sorted (date asc, historical first, mode priority)")

        index_text = index_path.read_text(encoding="utf-8")
        related = set()
        for meta in record_metas.values():
            related.update(meta.get("related_symbols") or [])
        for other in sorted(related):
            expected = f"[{other}](../{other}/INDEX.md)"
            if expected not in index_text:
                self.err(index_path, f"missing See also link {expected}")
```

Change `run()` so each symbol dir collects metas keyed by identity, then calls `check_index`:

```python
    def run(self) -> "list[str]":
        records_root = self.home / "records"
        if records_root.exists():
            for symbol_dir in sorted(p for p in records_root.iterdir() if p.is_dir()):
                if not is_canonical(symbol_dir.name):
                    self.err(symbol_dir, f"directory name {symbol_dir.name!r} is not a canonical symbol")
                record_metas: dict[tuple[str, str], dict] = {}
                for record_path in sorted(symbol_dir.glob("*.md")):
                    if record_path.name == "INDEX.md":
                        continue
                    meta = self.check_record(record_path, symbol_dir.name)
                    match = RECORD_FILENAME.match(record_path.name)
                    if meta is not None and match:
                        record_metas[(match.group(1), match.group(2))] = meta
                self.check_index(symbol_dir, record_metas)
        return self.errors
```

- [ ] **Step 4: Run the full test module to verify everything passes**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_records.py tests/test_decision_records.py
git commit -m "Validate INDEX timelines: bijection, historical links, sort, See-also"
```

---

### Task 5: `portfolio.yaml` validation

**Files:**
- Modify: `scripts/validate_records.py`
- Test: `tests/test_decision_records.py` (append `PortfolioValidationTests`)

- [ ] **Step 1: Append the failing tests**

```python
class PortfolioValidationTests(StateHomeTestCase):
    def test_bad_portfolio_schema_fails(self) -> None:
        self.mutate("portfolio.yaml", "schema: portfolio/v1", "schema: portfolio/v9")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("portfolio", result.stdout)

    def test_holding_missing_qty_fails(self) -> None:
        self.mutate("portfolio.yaml", "qty: 10, ", "")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("qty", result.stdout)

    def test_dangling_thesis_record_fails(self) -> None:
        self.mutate(
            "portfolio.yaml",
            "thesis_record: records/ACME/2026-06-01-new-idea.md",
            "thesis_record: records/ACME/2020-01-01-new-idea.md",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("thesis_record", result.stdout)

    def test_non_canonical_holding_symbol_fails(self) -> None:
        self.mutate("portfolio.yaml", "symbol: ACME", "symbol: acme")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records.PortfolioValidationTests -v
```

Expected: all four FAIL.

- [ ] **Step 3: Implement portfolio validation**

Add to `Checker` (and call `self.check_portfolio()` at the start of `run()`):

```python
    # ---------------- portfolio ----------------

    def check_portfolio(self) -> None:
        path = self.home / "portfolio.yaml"
        if not path.exists():
            return
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            self.err(path, f"portfolio is not valid YAML: {exc}")
            return
        if not isinstance(data, dict) or data.get("schema") != "portfolio/v1":
            self.err(path, "portfolio schema must be portfolio/v1")
            return
        try:
            as_date(data.get("as_of"))
        except (ValueError, TypeError):
            self.err(path, f"as_of is not ISO: {data.get('as_of')!r}")

        for holding in data.get("holdings") or []:
            if not isinstance(holding, dict):
                self.err(path, f"holding must be a mapping: {holding!r}")
                continue
            missing = [k for k in ("symbol", "qty", "avg_cost", "currency") if holding.get(k) is None]
            if missing:
                self.err(path, f"holding {holding.get('symbol')!r} missing: {', '.join(missing)} (e.g. qty)")
            if holding.get("symbol") is not None and not is_canonical(holding["symbol"]):
                self.err(path, f"holding symbol {holding['symbol']!r} is not canonical")
            thesis = holding.get("thesis_record")
            if thesis is not None and not (self.home / thesis).exists():
                self.err(path, f"thesis_record does not resolve: {thesis!r}")

        for leg in data.get("option_legs") or []:
            if not isinstance(leg, dict):
                self.err(path, f"option leg must be a mapping: {leg!r}")
                continue
            missing = [k for k in ("kind", "underlying", "strike", "expiry", "qty") if leg.get(k) is None]
            if missing:
                self.err(path, f"option leg missing: {', '.join(missing)}")
            if leg.get("underlying") is not None and not is_canonical(leg["underlying"]):
                self.err(path, f"option underlying {leg['underlying']!r} is not canonical")
```

- [ ] **Step 4: Run the full module**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_records.py tests/test_decision_records.py
git commit -m "Validate portfolio.yaml: schema, holdings, option legs, thesis links"
```

---

### Task 6: `--reindex` — rebuild INDEX files from frontmatter

**Files:**
- Modify: `scripts/validate_records.py`
- Test: `tests/test_decision_records.py` (append `ReindexTests`)

- [ ] **Step 1: Append the failing tests**

```python
class ReindexTests(StateHomeTestCase):
    def test_reindex_restores_deleted_record_row(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |\n",
            "",
        )
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        index = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("[record](2026-07-01-position-review.md)", index)

    def test_reindex_preserves_historical_rows(self) -> None:
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        index = (self.home / "records" / "1234.HK" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("| 2026-05-01 | historical |", index)
        self.assertIn("[report](../../equity_research_2026-05-01/1234-hk-note.md)", index)

    def test_reindex_writes_see_also_in_both_directions(self) -> None:
        self.mutate("records/ACME/INDEX.md", "See also: [1234.HK](../1234.HK/INDEX.md)\n", "")
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        acme = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("See also: [1234.HK](../1234.HK/INDEX.md)", acme)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records.ReindexTests -v
```

Expected: FAIL (`--reindex` currently a no-op, so the deleted-row test fails validation with exit 1).

- [ ] **Step 3: Implement reindex**

Add a module-level function and wire it into `main()` before validation:

```python
def record_row(meta: dict) -> str:
    date = as_date(meta["date"]).isoformat()
    mode = meta["mode"]
    price = f"{meta['price_at_decision']} {meta['currency']}"
    wfv = meta.get("weighted_fair_value")
    execution = meta.get("execution_method")
    source = meta.get("source_report")
    report_cell = f"[report](../../{source})" if source else "—"
    return (
        f"| {date} | {mode} | {price} | {meta['stance']} | "
        f"{wfv if wfv is not None else '—'} | {execution or '—'} | "
        f"[record]({date}-{mode}.md) | {report_cell} |"
    )


def reindex(home: Path) -> None:
    records_root = home / "records"
    if not records_root.exists():
        return
    symbol_dirs = sorted(p for p in records_root.iterdir() if p.is_dir())

    metas_by_symbol: "dict[str, list[dict]]" = {}
    checker = Checker(home)  # reuse frontmatter loader; its errors are ignored here
    for symbol_dir in symbol_dirs:
        metas = []
        for record_path in sorted(symbol_dir.glob("*.md")):
            if record_path.name == "INDEX.md":
                continue
            meta = checker.load_frontmatter(record_path)
            if meta is not None:
                metas.append(meta)
        metas_by_symbol[symbol_dir.name] = metas

    # Two-pass related_symbols so See-also lands on both sides.
    related_by_symbol: "dict[str, set[str]]" = {name: set() for name in metas_by_symbol}
    for name, metas in metas_by_symbol.items():
        for meta in metas:
            for other in meta.get("related_symbols") or []:
                related_by_symbol.setdefault(name, set()).add(other)
                related_by_symbol.setdefault(other, set()).add(name)

    for symbol_dir in symbol_dirs:
        name = symbol_dir.name
        index_path = symbol_dir / "INDEX.md"
        historical = []
        if index_path.exists():
            historical = [
                cells for cells in Checker.parse_index_rows(index_path) if cells[1] == "historical"
            ]

        rows = [("| " + " | ".join(cells) + " |") for cells in historical]
        rows += [record_row(meta) for meta in metas_by_symbol[name]]

        def sort_key(row: str):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            kind = 0 if cells[1] == "historical" else 1
            return (cells[0], kind, MODE_PRIORITY.get(cells[1], 99))

        rows.sort(key=sort_key)

        lines = [f"# {name} — Decision Timeline", ""]
        for other in sorted(related_by_symbol.get(name, set())):
            if other in metas_by_symbol:
                lines.append(f"See also: [{other}](../{other}/INDEX.md)")
        if related_by_symbol.get(name) and any(o in metas_by_symbol for o in related_by_symbol[name]):
            lines.append("")
        lines.append("| date | mode | price | stance | WFV | execution | record | report |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        lines.extend(rows)
        index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

In `main()`, after resolving `home` and before validation:

```python
    if args.reindex:
        reindex(home)
```

- [ ] **Step 4: Run the full module and the repo suite**

```bash
.venv/bin/python -m unittest tests.test_decision_records -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_records.py tests/test_decision_records.py
git commit -m "Add --reindex: rebuild INDEX rows from frontmatter, preserve historical"
```

---

### Task 7: Workflow skill edits — state home, stale-check anchor, Output Contract §6

**Files:**
- Modify: `skills/investment-decision-workflow/SKILL.md`
- Test: `tests/test_decision_records.py` (append `WorkflowContractTests`)

- [ ] **Step 1: Append the failing tests**

```python
class WorkflowContractTests(unittest.TestCase):
    def test_workflow_resolves_state_home(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("### State Home", workflow)
        self.assertIn(".investing-home", workflow)
        self.assertIn("Never invent state", workflow)

    def test_stale_check_auto_anchors_from_records(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("latest decision record", workflow)

    def test_output_contract_has_decision_record_section(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("### 6. Decision Record", workflow)
        self.assertIn("action_taken", workflow)
        self.assertIn("INDEX.md", workflow)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records.WorkflowContractTests -v
```

Expected: all three FAIL.

- [ ] **Step 3: Edit the workflow skill**

In `skills/investment-decision-workflow/SKILL.md`, make three insertions:

(a) At the end of the `## Required Data Discipline` section (after the paragraph ending "Do not invent holdings or assume no existing exposure."), append:

```markdown
### State Home

Before asking the user for position or prior-report inputs, resolve the private
state home defined in
[decision-records](../analyzing-stocks/references/decision-records.md):

1. Read `~/.investing-home`; the trimmed content is the state-home path.
2. If the pointer file is missing, offer once per session to create it and the
   state-home skeleton; if declined, continue stateless.
3. If the pointer exists but the directory is unreadable, say so and continue
   stateless. Never invent state.

When the state home resolves, read `portfolio.yaml` and each target symbol's
latest decision record (identity and tie-break rules per decision-records)
before declaring `Missing Inputs`. An explicit in-session user statement
overrides file state; write the correction back at session end after user
confirmation.
```

(b) In `### Stale Check`, after the line "Decide whether the old report/thesis/action sheet can be used as the starting point.", insert:

```markdown
When a state home is configured, resolve `Prior report / thesis anchor` from
the symbol's latest decision record automatically (latest by `date`, same-date
ties by the mode priority in decision-records). A user-pasted report still
takes precedence when newer.
```

(c) At the end of `## Output Contract` (after the `### 5. Execution Sheet` block and the closing paragraph "Keep execution language concrete. ..."), append:

```markdown
### 6. Decision Record

When a state home is configured, persist the outcome per
[decision-records](../analyzing-stocks/references/decision-records.md):

- For every symbol that received at least a `Stance` or an `Execution Method`,
  write or update `records/<SYMBOL>/YYYY-MM-DD-<mode>.md` (record identity
  `(symbol, date, mode)`; same identity updates in place) and append or update
  the symbol's `INDEX.md` row.
- After the user confirms an execution, backfill `action_taken` and update
  `portfolio.yaml`.
- A pure `Missing Inputs` / conditional-only outcome creates no record.
- Without a state home, skip this section (stateless behavior).
```

- [ ] **Step 4: Run the full suite**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all PASS (including the pre-existing workflow wiring tests).

- [ ] **Step 5: Commit**

```bash
git add skills/investment-decision-workflow/SKILL.md tests/test_decision_records.py
git commit -m "Wire decision workflow to the state home: read state, write records"
```

---

### Task 8: Controller skill edits — load reference, emit archive-ready frontmatter

**Files:**
- Modify: `skills/analyzing-stocks/SKILL.md`
- Test: `tests/test_decision_records.py` (append `ControllerContractTests`)

- [ ] **Step 1: Append the failing tests**

```python
class ControllerContractTests(unittest.TestCase):
    def test_controller_loads_decision_records_reference(self) -> None:
        self.assertIn("decision-records", read(CONTROLLER))

    def test_controller_step7_emits_archive_ready_record(self) -> None:
        controller = read(CONTROLLER)
        self.assertIn("mode: research", controller)
        self.assertIn("archive-ready", controller)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_decision_records.ControllerContractTests -v
```

Expected: both FAIL.

- [ ] **Step 3: Edit the controller skill**

In `skills/analyzing-stocks/SKILL.md`:

(a) In `## Step 4: Load Shared References (Mandatory)`, append to the reference list (after the `[report-template](references/report-template.md)` line):

```markdown
- [decision-records](references/decision-records.md) — required only when a
  private state home is configured (see that file's resolution rules)
```

(b) In `## Step 7: Produce the Unified Report`, append a bullet to the existing list:

```markdown
- When a private state home is configured (see
  [decision-records](references/decision-records.md)), emit the decision-record
  frontmatter block at the end of the report and offer to save it as a
  `mode: research` record plus its `INDEX.md` row, so standalone research runs
  are archive-ready without the decision workflow.
```

- [ ] **Step 4: Run the full suite and repo validator**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: all PASS; validator passes.

- [ ] **Step 5: Commit**

```bash
git add skills/analyzing-stocks/SKILL.md tests/test_decision_records.py
git commit -m "Controller emits archive-ready research records for state-home sessions"
```

---

### Task 9 (inline, with user): Private state-home setup

**No repo files change.** Operational — run in this session, not a subagent. The private path below is written only into the pointer file, never into any repo file.

- [ ] **Step 1: Create the pointer file** — confirm the exact private research directory with the user (the one containing their `equity_research_YYYY-MM-DD/` folders), then:

```bash
printf '%s\n' "<absolute-private-path>" > ~/.investing-home
```

- [ ] **Step 2: Create the skeleton**

```bash
mkdir -p "$(cat ~/.investing-home)/records"
```

- [ ] **Step 3: Draft `portfolio.yaml` with the user** — ask for current cash, holdings (symbol/qty/avg cost/currency), open option legs, and constraints; write `<state-home>/portfolio.yaml` per the schema in `decision-records.md`, normalizing symbols to canonical form.

- [ ] **Step 4: Validate**

```bash
.venv/bin/python scripts/validate_records.py
```

Expected: `State-home validation passed` (pointer-file resolution path exercised).

- [ ] **Step 5: Recommend (optional, user's call)** — `git init` the state home as a private repo with its own `.gitignore` (`.omx/`, `.skill-staging/`, `.obsidian/workspace*`).

---

### Task 10 (inline, with user): Historical light-index backfill (one-off)

**No repo files change.** Per spec §3b: index rows only, no schema conversion, `historical` rows excluded from future scoring.

- [ ] **Step 1: Inventory** — list `<state-home>/equity_research_*/` contents; for each report file, identify covered symbols from the filename (patterns like `00883-HK-...`, `multi-name-...-<code>-<code>`) plus a quick skim of the file's header when the filename is ambiguous. Normalize to canonical symbols. Reports with no single-symbol focus (sector notes, screens) are exempt.

- [ ] **Step 2: Append historical rows** — for each (symbol, report): ensure `records/<SYMBOL>/INDEX.md` exists (create with the standard header + table if not); append `| <folder-date> | historical | <price or —> | <stance or —> | — | — | — | [report](../../<relative-path>) |`. Extract price/stance only when trivially visible in the report header; otherwise `—`.

- [ ] **Step 3: Sort and validate**

```bash
.venv/bin/python scripts/validate_records.py --reindex
```

Expected: exit 0; historical rows preserved and sorted.

- [ ] **Step 4: Acceptance check (manual)** — every stock-specific old report is linked from at least one symbol's INDEX; spot-open two INDEX files in Obsidian and confirm links resolve.

---

### Task 11 (inline, with user): End-to-end verification

Spec Verification #4 — proves the skills actually read/write state in a real session.

- [ ] **Step 1:** In a fresh session, run `investment-decision-workflow` on one real name the user picks. Confirm: it resolves the state home, reads `portfolio.yaml` without asking for holdings, and at the end writes `records/<SYMBOL>/<date>-<mode>.md` plus the INDEX row.

- [ ] **Step 2:** Run `.venv/bin/python scripts/validate_records.py` — exit 0.

- [ ] **Step 3:** In a second session on the same name, confirm the stale check anchors on the new record (`review_by` / `next_earnings` referenced) with no re-dictation.

- [ ] **Step 4:** Close out: mark the P0 tasks done in this plan file; report results (including any contract wording that confused the model in practice — feed that back as follow-up edits).

---

## Final Verification (after Task 8, before Task 9)

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/validate_repo.py --profile full
.venv/bin/python scripts/validate_records.py --home tests/fixtures/state-home
bash tests/test_install.sh
```

Expected: everything passes. This mirrors CI (which additionally runs on 3.9/3.11/3.12 with `pip install pyyaml`).

## Spec Coverage Map

| Spec section | Task |
| --- | --- |
| §1 state home + pointer resolution | 2 (doc), 7 (workflow), 9 (setup) |
| §2 layout + canonical symbols + dual listings | 2 (doc), 3 (validator), 6 (See-also) |
| §3 record schema + identity + field rules | 2 (doc), 3 (validator) |
| §3a INDEX timeline + maintenance | 2 (doc), 4 (checks), 6 (reindex), 7 (workflow row upkeep) |
| §3b historical backfill | 2 (doc), 10 (execution) |
| §4 portfolio schema | 2 (doc), 5 (validator), 9 (real file) |
| §5.1 reference doc | 2 |
| §5.2 workflow edits | 7 |
| §5.3 controller edits | 8 |
| §5.4 validator + tests + repo wiring + CI/PyYAML | 1, 2, 3–6 |
| §6 privacy | Execution rule + Tasks 9–10 inline-only |
| Verification 1–3 | Final Verification block |
| Verification 4 | Task 11 |
| Verification 5 | Task 10 Step 4 |
```
