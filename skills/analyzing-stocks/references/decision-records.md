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
- Korea: 6-digit KRX code + `.KS` (KOSPI) / `.KQ` (KOSDAQ) — `000660.KS`
- Australia: ASX code (letters/digits) + `.AX` — `BC8.AX`

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
market: US                    # US | CN | HK | KR | AU
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
- Write cells as the canonical render, not a prettified display: the price cell
  is `<price_at_decision> <currency>` (e.g. `390.49 USD`) and WFV is the bare
  number — no currency symbols, no thousands separators (`2425000 KRW`, not
  `KRW 2,425,000`). `--reindex` canonicalizes rows to exactly this render, so
  writing them this way keeps diffs quiet.
- Record rows are derived data: `scripts/validate_records.py` checks the
  record ↔ row bijection and `--reindex` rebuilds them from frontmatter.
- Sort key: `date` ascending; same-date ties order `historical` rows first,
  then record rows by mode priority. `--reindex` applies the same key.
- `historical` rows are index-only backfill entries for old reports: cell
  contents preserved by `--reindex` (spacing normalized); their only integrity
  check is that the report link resolves. If an old report is later
  hand-converted into a real record, the conversion replaces its `historical`
  row.
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
