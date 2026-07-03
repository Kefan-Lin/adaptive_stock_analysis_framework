# Decision Records & Portfolio State — Design (P0)

Date: 2026-07-03
Status: Approved design, pending implementation plan

## Context

The framework is a strong single-session analysis discipline machine, but it has no
memory. Reports are generated in-session and vanish; the stale check requires the
user to paste prior reports back in; holdings, cost basis, and option legs are
re-dictated every session; add-on / trim-exit triggers and monitor lists are emitted
and never checked again; and there is no way to score past judgments.

This design adds the missing foundation: a **private state home** holding
machine-readable **decision records** and a **portfolio state file**, plus the
framework-side contract for reading and writing them. Monitoring (P1), outcome
scoring (P2), and the inflection-discovery pipeline (P3) all build on this layer.

Owner usage facts that shaped the design (from the owner's real research archive):

- Research sessions already accumulate in the owner's private research directory
  (`equity_research_YYYY-MM-DD/` folders) — that directory becomes the state home;
  no new location is introduced. Its actual path lives only in the private
  pointer file (§1), never in this repo.
- Reports are frequently **multi-name** (one decision-workflow report covering
  several A-share/HK/US names at once), so a record is **per symbol per
  decision**, not per report file.
- Holdings span US, China A-share, and Hong Kong markets.
- The owner explicitly wants a **per-stock chronological view**: today one stock's
  analyses are scattered across date folders, so its thesis evolution cannot be
  read in one place. `records/<SYMBOL>/` plus the timeline index (§3a) is the
  answer; the primary browsing dimension is the stock, not the session date.
- The owner chose: separate private state home (not committed to this public
  repo); records accumulate forward-only, plus a one-off **index-only** backfill
  of old reports (§3b) so historical analyses are also reachable per symbol.

## Goals

1. Every decision produced by `investment-decision-workflow` (and optionally any
   full `analyzing-stocks` report) is persisted as a machine-readable record in the
   state home, automatically.
2. `investment-decision-workflow` reads portfolio state and prior records at session
   start instead of asking the user to re-dictate holdings and paste old reports.
3. The record and portfolio schemas are contract-tested in this repo so vocabulary
   stays in sync with the skills (same style as existing contract tests).
4. No personal data ever lives in this public repository.

## Non-goals (deferred to later phases)

- No automated price/fundamentals fetching, no caching layer (P4 direction).
- No morning-check monitoring skill, no scheduled runs (P1).
- No outcome scoring / calibration reports (P2) — but the record schema must carry
  enough structure (dates, prices, structured price triggers) for P2 to be a pure
  consumer.
- No full record-backfill of the ~30 existing `equity_research_*` folders — they
  get index rows only (§3b). Old reports may still be converted to real records
  opportunistically by hand later; converted records join the system with no
  special handling.

## Design

### 1. State home and discovery

The state home is the owner's existing private research directory — the one
already holding the `equity_research_*` folders. Its path is written only into
the pointer file, not into this repo. Recommended (not enforced) to be a private
git repository for backup/sync.

Skills discover it via a **pointer file** `~/.investing-home` containing a single
line: the absolute path of the state home. Resolution contract (defined in the new
shared reference, used by all skills that touch state):

1. Read `~/.investing-home`; trim whitespace; the result is the state home path.
2. If the pointer file is missing, ask the user once **per session**, offer to
   create both the pointer file and the state-home skeleton, then continue. A
   user who declines runs stateless; there is nowhere to persist the refusal, so
   a later session may ask again — accepted behavior.
3. If the pointer exists but the directory is missing/unreadable, say so and fall
   back to stateless behavior (current behavior: ask for inputs, emit
   `Missing Inputs`). Never invent state.

Rationale: independent of CWD (skills are installed globally and invoked from
anywhere), no env-var dependence, trivially portable.

### 2. State home layout

```
<state-home>/
├── portfolio.yaml              # single portfolio snapshot (see §4)
├── records/
│   └── <SYMBOL>/               # canonical symbol, one dir per name
│       ├── INDEX.md            # per-symbol decision timeline (see §3a)
│       └── YYYY-MM-DD-<mode>.md    # one decision record (see §3)
└── equity_research_*/          # existing report folders, unchanged
```

**Canonical symbol form** (directory names and `symbol:` field):

- US: bare ticker, uppercase — `NVDA`
- Hong Kong: HKEX code zero-padded to 4 digits + `.HK` — `0700.HK` (normalize
  `00700` / `00883-HK` input forms); genuine 5-digit codes (e.g. RMB counters
  like `80700`) stay 5 digits
- China A-share: 6-digit code + `.SH` / `.SZ` / `.BJ` — `600519.SH`, `300750.SZ`

The canonical form is an **internal identity**, deliberately the human-dominant
convention (`.SH` per tushare/Eastmoney usage), not any data provider's format:
yfinance wants `600519.SS` for Shanghai, akshare wants bare `600519`. P1 owns a
canonical→provider mapping (a pure function; US and `.HK` forms pass through to
yfinance unchanged) and must pick an A-share-capable source — akshare is already
integrated on the inflection branch, and yfinance's `.BJ` coverage is unreliable.

**Dual listings / ADRs**: a record anchors to the tradable line actually analyzed
(the controller already requires stating that line), so `9988.HK` and `BABA` get
separate directories. Link them instead of merging: an optional
`related_symbols: [BABA]` frontmatter field, which the validator mirrors as a
`See also: [BABA](../BABA/INDEX.md)` line in both symbols' `INDEX.md` headers.
Different lines can legitimately carry different valuations and stances.

Multiple records for the same symbol accumulate over time; the latest record by
`date` is the "current" one for stale checks.

### 3. Decision record format

One markdown file per **symbol × decision**. YAML frontmatter carries the machine
fields; the body must be **self-contained**: for single-name runs, the full
report; for multi-name runs, that symbol's complete per-name sections. Duplicating
content out of the session report is accepted — the records directory is the
canonical per-stock view, and reading a symbol's directory front-to-back must
reconstruct the thesis evolution without opening other files. `source_report`
still links the full session report for shared context.

All enum values reuse the skills' exact vocabulary (contract-tested, see §6).

```yaml
---
schema: decision-record/v1
symbol: 0700.HK               # canonical form, §2
market: HK                    # US | CN | HK
date: 2026-07-03
mode: position-review         # new-idea | existing-report | position-review | event-review | research
price_at_decision: 512.00
currency: HKD

# Research & valuation (from analyzing-stocks / refreshed upstream report)
stance: Hold                  # Buy | Add | Hold | Reduce | Avoid
position_size: Core           # Core | Starter | Speculative | Watch-Avoid
confidence: Medium            # High | Medium | Low (report-template vocabulary)
weighted_fair_value: 610
scenarios: {bear: 420, base: 600, bull: 760}

# Decision & execution (from investment-decision-workflow, when run)
candidate_tier: Core Candidate    # Core Candidate | Tactical Candidate | Reject
valuation_zone: Hold              # Accumulation | Hold | Exhaustion | Invalidation
execution_method: No Action       # Buy now | Stage buy | Sell cash-secured put | Wait | Reduce | Exit | No Action

# Triggers: price-type triggers are structured (script-checkable, P1/P2);
# KPI/event triggers stay as text (LLM-checkable, P1).
triggers:
  add_on:
    - {type: price, level: 430, direction: below}
    - {type: kpi, text: "游戏流水连续两季重回双位数增长且利润率企稳"}
  trim_exit:
    - {type: price, level: 780, direction: above}
    - {type: event, text: "监管对游戏版号发放再次系统性收紧"}
monitor:
  - {kpi: "广告收入同比增速", threshold: "< 5%", action: "复核 Base 场景收入假设"}

# Dates for staleness & monitoring
next_earnings: 2026-08-12     # null if unknown
review_by: 2026-09-30         # explicit staleness date set by the skill

# Provenance & lifecycle
source_report: equity_research_2026-07-03/0700-HK-decision-workflow.md  # relative to state home; null if body is the full report
action_taken: null            # backfilled after execution, e.g. {action: reduced, qty: 300, price: 515.0, date: 2026-07-04}
---

# (human-readable body: conclusion, downside path, key evidence, or full report)
```

Field rules:

- Required always: `schema, symbol, market, date, mode, price_at_decision,
  currency, stance, review_by`.
- Required when a full valuation backs the decision: `weighted_fair_value,
  scenarios, position_size, confidence`.
- Required when the decision workflow ran: `candidate_tier, valuation_zone,
  execution_method, triggers`.
- `mode: research` marks a standalone `analyzing-stocks` run saved without the
  decision workflow; workflow-only fields stay absent. The writing skill always
  sets `review_by` explicitly; default when the user states none:
  `min(next_earnings, date + 90 days)`.
- **Record identity is `(symbol, date, mode)`** — also the `INDEX.md` row key. A
  rerun with the same identity updates the record and row in place (no same-day
  duplicates). For "latest record" (the stale-check anchor) on a same-date tie,
  use mode priority `position-review > event-review > existing-report >
  new-idea > research` — the workflow's own mode-routing priority.
- A record is written when the session produced at least a `stance` or an
  `execution_method` for that symbol; a pure `Missing Inputs` / conditional-only
  outcome creates no record.
- Enum fields store the skills' **display strings verbatim** (`stance: Hold`,
  `confidence: Medium`, `candidate_tier: Core Candidate`,
  `execution_method: No Action`), so contract tests can assert literal sync.
  The one exception is `mode` (it appears in filenames): filename-safe slugs
  with a normative slug ↔ display table in the §5.1 reference
  (`new-idea` ↔ `New Idea Decision`, `existing-report` ↔
  `Existing Report to Action`, `position-review` ↔ `Position Review`,
  `event-review` ↔ `Event Review`; `research` and index-only `historical` have
  no workflow counterpart). `execution_method` vocabulary is pinned to the
  workflow Output Contract line under `### 5. Execution Sheet`, read as seven
  distinct values with `Reduce` and `Exit` separate (the process-section bullet
  `Reduce / Exit` is a combined outcome label, not the vocabulary source).
- `action_taken` starts `null`; the workflow backfills it (and updates
  `portfolio.yaml`) only after the user confirms an execution happened.
  `action_taken.action` vocabulary (v1): `bought | added | reduced | exited |
  sold-put | put-assigned | put-closed`.
- `source_report` is set only if the linked file already exists in the state
  home; otherwise leave it `null` (the validator hard-fails dangling paths).
- Amounts are in `currency`; no FX conversion inside records.

### 3a. Per-symbol timeline index

Each `records/<SYMBOL>/` directory holds an `INDEX.md`: one table row per
decision, **oldest first**, so the file reads top-to-bottom as the thesis
evolution timeline (and renders as a clickable table in Obsidian):

| date | mode | price | stance | WFV | execution | record | report |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-10 | historical | 480 HKD | Buy | — | — | — | [report](../../equity_research_2026-04-10/0700-hk-....md) |
| 2026-07-03 | position-review | 512 HKD | Hold | 610 | No Action | [record](2026-07-03-position-review.md) | [report](../../equity_research_2026-07-03/....md) |

Maintenance contract:

- The workflow appends/updates the symbol's row whenever it writes a record,
  keyed by the record identity `(symbol, date, mode)`.
- Record rows are **derived data**: `validate_records.py` checks the
  record ↔ row bijection, and `--reindex` rebuilds record rows from frontmatter.
- Sort key: `date` ascending; same-date ties order `historical` rows first, then
  record rows by the §3 mode priority. `--reindex` applies the same key.
- `historical` rows (§3b) are preserved verbatim by `--reindex`; their only
  integrity check is that the report link resolves. `historical` is an
  index-only mode value; the record `mode` enum in §3 is unchanged.
- Obsidian note: nested frontmatter (`scenarios`, `triggers`) renders as
  non-editable "complex" properties in Obsidian's Properties pane — harmless;
  the INDEX tables and links are the intended browsing surface.

### 3b. Historical light-index backfill (one-off)

The ~30 existing `equity_research_*` folders are wired into the per-symbol
timelines **as index rows only**: for each old report, identify the symbols it
covers (filename plus a quick content skim), then append one `historical` row per
symbol — date from the folder name, price/stance where cheaply extractable
(else `—`), and a link to the untouched original report. No schema conversion,
no frontmatter, and P2 scoring never reads `historical` rows. Performed once,
LLM-assisted, during implementation. If an old report is later hand-converted
into a real record, the conversion **replaces** that report's `historical` row —
no duplicate timeline entries.

### 4. Portfolio state format

Single `portfolio.yaml` at the state-home root — the fields the workflow's
`Required Data Discipline`, `Portfolio Risk Budget`, and exposure rules currently
ask the user to dictate:

```yaml
schema: portfolio/v1
as_of: 2026-07-03
base_currency: USD            # reporting currency for caps/floors
cash: {USD: 25000, HKD: 80000, CNY: 50000}
holdings:
  - {symbol: 0700.HK, qty: 500, avg_cost: 480.0, currency: HKD,
     opened: 2026-04-10, thesis_record: records/0700.HK/2026-07-03-position-review.md}
option_legs:
  - {kind: cash-secured-put, underlying: NVDA, strike: 140, expiry: 2026-08-15,
     qty: -1, premium: 4.20, currency: USD, opened: 2026-06-20, multiplier: 100}
constraints:                  # feeds Portfolio Risk Budget verbatim
  single_name_cap_pct: 10
  cash_reserve_floor_pct: 15
  max_drawdown_budget_pct: 25
  sleeves: {core: 60, tactical: 25, speculative: 15}
```

Contract: skills treat `portfolio.yaml` as the source of truth when present, but a
user statement in-session **overrides** it (then the skill updates the file at the
end with the user's confirmation). Assignment reserve for cash-secured puts is
computed from `option_legs` (`strike × multiplier × |qty|`), not stored.
`underlying` uses the §2 canonical form. `multiplier` defaults to 100 (US equity
options) and must be set explicitly for markets with other contract sizes (HKEX
per-underlying sizes; A-share ETF options are 10000).

### 5. Framework-side changes (this repo — no personal data)

1. **New shared reference** `skills/analyzing-stocks/references/decision-records.md`
   — the normative home of §1–§4 above: state-home resolution, layout, both
   schemas, canonical symbol rules, read/write contract. Written with fictional
   example data only.

2. **`skills/investment-decision-workflow/SKILL.md`** — three edits:
   - Under `Required Data Discipline`: add a `State Home` step — resolve the state
     home, read `portfolio.yaml` and the target symbols' latest records **before**
     declaring `Missing Inputs`; explicit user input overrides file state; missing
     state home falls back to current behavior.
   - In the `Stale Check` process section **and** the Output Contract block
     `### 2. Stale Check`: the `Prior report / thesis anchor` field resolves
     automatically from the symbol's latest decision record per the §3 tie-break
     (user-pasted reports still accepted and take precedence when newer).
   - In `Output Contract`: add section `### 6. Decision Record` — for every symbol
     that received a decision, write/update a record per §3 and its `INDEX.md`
     row per §3a; after the user confirms an execution, backfill `action_taken`
     and update `portfolio.yaml`.

3. **`skills/analyzing-stocks/SKILL.md`** — Step 7 (Produce the Unified Report):
   when a state home is configured, also emit the §3 frontmatter block at the end
   of the report and offer to save it as a `mode: research` record **plus its
   `INDEX.md` row (§3a)**, so standalone research runs are archive-ready — and
   index-consistent — without the decision workflow.

4. **Validation & tests**:
   - `scripts/validate_records.py` — validates a state home (`--home PATH`, default
     resolves `~/.investing-home`): YAML parses, required fields present, enums
     within vocabulary, symbols canonical, dates ISO, `thesis_record`/`source_report`
     paths exist, `INDEX.md` rows ↔ record files consistent (`historical` rows
     only need a resolving report link). `--reindex` rebuilds record-derived
     index rows from frontmatter, preserves `historical` rows, and mirrors
     `related_symbols` as `See also` lines in both symbols' INDEX headers (§2).
     Exits non-zero with a readable violation list.
   - `tests/test_decision_records.py` — contract tests in the existing style:
     display-string enums in `decision-records.md` stay literally in sync with
     the vocabulary lines in `analyzing-stocks/SKILL.md`, `report-template.md`,
     and `investment-decision-workflow/SKILL.md` (execution-method pinned to the
     workflow's `### 5. Execution Sheet` line), and the `mode` slug ↔ display
     table maps both directions onto the workflow's mode names; validator passes on a good fixture
     state home and fails on targeted mutations (bad stance, non-canonical symbol,
     missing `review_by`, index row missing for a record). Fixtures use fictional
     data under `tests/fixtures/`.
   - Wire the new reference into `validate_repo.py`'s required-file list (the
     full profile enumerates reference files).
   - **Dependencies & CI**: the repo is currently stdlib-only, but the schemas
     use nested YAML that is not sanely hand-parseable — `validate_records.py`
     and the fixture tests take **PyYAML** as the one new dependency. Add a
     `pip install pyyaml` step to `.github/workflows/ci.yml`; the validator must
     stay compatible with the CI floor (Python 3.9).

### 6. Privacy & data separation

- The public repo gains only: one reference doc, skill-contract edits, validator,
  tests, fixtures — all with fictional data.
- Real records and portfolio live only in the state home. Recommend the state home
  be a **private** git repo; if so, add `.omx/`, `.skill-staging/` etc. to its own
  `.gitignore` (owner's call, outside this repo's scope).

## Verification

1. `python3 -m unittest discover -s tests -p 'test_*.py' -v` — all green,
   including the new contract tests (run in repo `.venv` / `uv`).
2. `python3 scripts/validate_repo.py --profile full` — passes with the new
   reference wired in.
3. `python3 scripts/validate_records.py --home tests/fixtures/state-home` — passes;
   mutated fixtures fail with readable errors.
4. End-to-end (manual, in a real session): create `~/.investing-home` → run
   `investment-decision-workflow` on one real name → confirm the record file and
   its `INDEX.md` row land in the state home with valid schema → run a second
   session on the same name → confirm it auto-reads the record + portfolio without
   re-dictation, and the stale check references the record's
   `review_by`/`next_earnings`.
5. After the one-off backfill (§3b): every **stock-specific** `equity_research_*`
   report file is linked from at least one symbol's `INDEX.md` (sector notes or
   screens with no single symbol are exempt; this is a manual acceptance check),
   and every `historical` row's link resolves (`validate_records.py`).

## Future phases (context, not scope)

- **P1 morning-check**: reads `portfolio.yaml` + all records; checks price-type
  triggers, `next_earnings` proximity (US + CN/HK calendars), `review_by` expiry,
  KPI triggers via LLM; outputs an action brief. Manual trigger first, `/schedule`
  later.
- **P2 scoring**: parses records; computes 90/180/365-day outcomes vs `stance` /
  `weighted_fair_value` / trigger hits; calibration report by sector & valuation
  family. Forward-only.
- **P3 inflection pipeline**: merge branch `claude/compassionate-thompson-93ff22`;
  wire discover → `debating-stocks` trap-judgment → `analyzing-stocks`; candidates
  that survive become records with `mode: new-idea`.
