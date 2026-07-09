# P1 Morning-Check Monitoring — Design

Status: design (approved forks; pending spec review)
Depends on: P0 decision-records layer (state home, `portfolio.yaml`, decision records)
Defers: `/schedule` automation (P1 note in the P0 design), P2 outcome scoring

## Problem

The P0 layer gives the framework memory — decision records with structured
price triggers, free-text KPI/event triggers, `monitor` KPIs, `next_earnings`,
and `review_by` — but nothing *reads* that state on a cadence. Today the owner
must re-open each name to notice a trigger crossing, a stale thesis, or an
approaching earnings date. P1 is the manually-triggered "morning check" that
sweeps the whole state home and emits one action brief.

The P0 design's own P1 note (docs/plans/2026-07-03-decision-records-design.md,
"Future phases"): *reads `portfolio.yaml` + all records; checks price-type
triggers, `next_earnings` proximity, `review_by` expiry, KPI triggers via LLM;
outputs an action brief. Manual trigger first, `/schedule` later.*

## Approved scope decisions

- **Architecture:** hybrid — a deterministic Python script + an LLM skill.
- **Price data:** live fetch (yfinance for US/HK/KR/AU, akshare for CN A-shares)
  with a per-name fallback to asking the owner for a quote.
- **Checks this pass:** price triggers, `review_by` expiry, `next_earnings`
  proximity, KPI/event free-text triggers (LLM) — plus a lightweight
  cash-secured-put assignment-risk check.
- **`next_earnings` source:** the stored record field only; `null` → a
  "verify earnings date" flag. No live earnings-calendar fetch this pass.
- **Output:** print the brief to the session, then offer to persist a dated
  file into the state home (opt-in per run).
- **Proximity windows (defaults, overridable per run):** earnings within
  7 calendar days; `review_by` within 14 days (or already passed).

## Architecture

Two units with a clean seam between deterministic and judgment work.

### 1. `scripts/morning_check.py` — deterministic core

Pure stdlib + PyYAML (no pandas/yfinance/akshare imported at module top), so it
runs in the main pyyaml-only CI job. Responsibilities:

- Resolve the state home (same contract as `validate_records.py`:
  `--home PATH`, default resolves `~/.investing-home`).
- Load `portfolio.yaml` and every symbol's **latest** decision record (P0
  `(date, mode)` tie-break). Reuse the frontmatter/record loading helpers from
  `validate_records.py` rather than re-parsing.
- Build the **monitored universe**: union of portfolio holdings, option
  underlyings, and every symbol that has a current decision record. (Watchlist
  names with records but no position still surface `add_on` dip triggers.)
- Fetch current prices through an injectable `PriceSource` (below).
- Compute all **deterministic findings** and emit them as structured output
  (JSON) plus a rendered markdown block.

Findings are structured so the skill and future P2 can consume them:

```json
{
  "as_of": "2026-07-09",
  "findings": [
    {"symbol": "ACME", "kind": "price_trigger", "urgency": "act",
     "detail": "trim_exit level 185 crossed (spot 189.20 > 185, above)",
     "evidence": {"spot": 189.20, "level": 185, "direction": "above",
                  "trigger_group": "trim_exit"}}
  ],
  "data_gaps": [
    {"symbol": "0700.HK", "reason": "price fetch failed (provider error)"}
  ],
  "llm_todo": [
    {"symbol": "ACME", "type": "kpi", "text": "fictional KPI recovers two quarters",
     "trigger_group": "add_on"},
    {"symbol": "ACME", "type": "monitor", "kpi": "fictional revenue growth",
     "threshold": "< 5%", "action": "revisit Base"}
  ]
}
```

`kind` ∈ `price_trigger | drawdown | review_expiry | earnings_proximity |
options_assignment`. `urgency` ∈ `act | review | watch`. Missing/unknown data
never becomes a finding — it goes in the separate `data_gaps[]` array so a name
is visibly *not-checked* rather than silently absent.

### 2. `skills/morning-check/SKILL.md` — LLM wrapper

Orchestrates a run:

1. Resolve the state home. If unconfigured/empty, say so and stop (there is
   nothing to monitor) — do not invent state.
2. Run `scripts/morning_check.py --format json`; capture `findings`,
   `data_gaps`, `llm_todo`.
3. **Fallback for `data_gaps`:** for each price-fetch failure, ask the owner for
   a current quote; re-run with `--prices <file>` (or patch the finding) so the
   name is checked rather than dropped.
4. **`llm_todo`:** for each free-text KPI/event trigger and `monitor` KPI, do
   live research (news/filings) and judge fired / not-fired / uncertain, with a
   one-line citation.
5. Assemble the **action brief** grouped by urgency.
6. Offer to save the brief as `monitoring/YYYY-MM-DD-morning-check.md` in the
   state home (opt-in).

## Deterministic checks (in the script)

### Price triggers
For each `add_on`/`trim_exit` entry of `type: price`: compare spot to `level`
per `direction` (`above` fires when `spot >= level`; `below` fires when
`spot <= level`), in the instrument's **native currency** — no FX. A fired
`add_on` and a fired `trim_exit` are both `urgency: act`.

### Drawdown vs scenarios
When the latest record carries `weighted_fair_value`/`scenarios` and a spot is
available: report spot's position vs `bear`/`base`/`bull` and vs WFV
(e.g. "spot 82 below bear 80" → `urgency: review`). Informational, not a hard
trigger.

**Implementation scope:** the deterministic script fires this only on the
actionable **bear-scenario breach** (`spot < bear`). Richer base/bull/WFV
positioning is left to the LLM layer, which already reads the full record —
keeping the script's output to the one case that demands attention.

### `review_by` expiry
`review_by < as_of` → `urgency: review` (thesis stale). Within the review
window (default 14d) → `urgency: watch`.

### `next_earnings` proximity
Using the stored `next_earnings` field only. Within the earnings window
(default 7d) → `urgency: watch`. `null` → a `data_gaps[]` entry
("earnings date unknown — verify") rather than a finding. Past dates are ignored
(a stale `next_earnings`
is a `review_by` concern, not an earnings alert).

### Cash-secured-put assignment risk
For each `portfolio.yaml` `option_legs` entry with `kind: cash-secured-put`
(short put, `qty < 0`), fetch the underlying spot and compute:

- **moneyness** = `spot / strike`; flag when `spot <= strike` (ITM/at risk) or
  within `assignment_watch_pct` (default 3%) of the strike.
- **DTE** = `expiry - as_of`; escalate when small (default ≤ 7d).
- **earnings-before-expiry**: if the underlying's latest record has
  `next_earnings` and it falls on/before `expiry` → escalate (gap risk).
- **assignment reserve** = `strike × multiplier × |qty|` (per the P0 contract,
  computed not stored) — shown so the owner sees the cash needed if assigned.

Urgency: `act` when ITM and near expiry; otherwise `watch`.

## Price source & provider mapping

`PriceSource` is a small interface: `spot(canonical_symbol) -> float | None`.

- **`LivePriceSource`** — the default. Maps canonical → provider and fetches the
  latest close/quote, **lazy-importing** yfinance/akshare *inside* the fetch
  methods (never at module top). Any per-name failure returns `None` (→ a
  `data_gap`), never raises out.
- **`FilePriceSource`** — reads a `{canonical_symbol: price}` YAML/JSON (via
  `--prices FILE`); used for the owner-provided-quote fallback and for tests.
  With `--offline`, this is the *only* source (no network).

Canonical → provider mapping (self-contained in the script, **not** imported
from the pandas-heavy `inflection_discovery` package, to keep the main test job
dependency-free):

| canonical | provider | provider symbol |
| --- | --- | --- |
| `NVDA` (US) | yfinance | `NVDA` (passthrough) |
| `0700.HK` (HK) | yfinance | `0700.HK` (passthrough) |
| `000660.KS` / `.KQ` (KR) | yfinance | passthrough |
| `BC8.AX` (AU) | yfinance | passthrough |
| `600519.SH` / `.SZ` / `.BJ` (CN) | akshare | bare `600519` |

A **contract test** asserts this mapping's canonical patterns stay in lockstep
with `SYMBOL_PATTERNS` in `inflection_discovery/symbols.py` /
`scripts/validate_records.py` (the same lockstep discipline `symbols.py` already
documents), so the two symbol vocabularies never drift.

## CLI

```
python scripts/morning_check.py [--home PATH] [--as-of YYYY-MM-DD]
    [--earnings-window N] [--review-window N]
    [--prices FILE] [--offline] [--format json|md]
```

- `--as-of` fixes "today" for deterministic tests (default: system date).
- `--prices` + `--offline` make a fully offline, network-free run (tests, and
  the owner-provided-quote fallback).
- Exit codes mirror `validate_records.py`: `0` clean run (with or without
  findings), `2` environment error (no state home / unreadable). Findings
  themselves do not set a non-zero exit — the brief communicates urgency.

## Output — action brief

Rendered (markdown `--format md`, or by the skill from JSON), grouped by
urgency, most-urgent first:

```markdown
# Morning Check — 2026-07-09

## Act now
- **ACME** — trim_exit 185 crossed (spot 189.20). Latest record: 2026-06-01 new-idea, WFV 140.
- **NVDA put 140 (exp 2026-08-15)** — spot 138.10 ITM, 6 DTE, reserve $14,000.

## Review (thesis stale / at fair value)
- **1234.HK** — review_by 2026-07-02 passed (7d ago).

## Watch
- **ACME** — earnings in 5d (2026-07-14).

## KPI / event checks (LLM)
- **ACME** — add_on KPI "fictional KPI recovers two quarters": not fired (Q2 still -3%, [src]).

## Data gaps
- **0700.HK** — price fetch failed; provide a quote to include it.
```

## Testing & CI

- **`tests/test_morning_check.py`** (main pyyaml-only suite): a fixture state
  home under `tests/fixtures/` + a stub/`FilePriceSource` → assert findings.
  Cases: `above`/`below` price trigger fires and does not fire; `review_by`
  passed vs within-window vs clear; `next_earnings` soon vs `null` vs past;
  cash-secured-put ITM near expiry vs OTM; earnings-before-expiry escalation;
  a `data_gap` when a price is missing; watchlist (record, no position) add_on
  fires; universe is the correct union. All offline (`--offline`).
- **Contract test** (in `tests/test_morning_check.py` or the existing contract
  file): provider-mapping canonical patterns ↔ `symbols.py` /
  `validate_records.py` `SYMBOL_PATTERNS` in sync.
- **Live-source smoke test**: network-gated (skips when offline) or placed in
  the `inflection-tests` CI job, which already installs yfinance/akshare.
- **No new main-job dependency**: yfinance/akshare are already in
  `pyproject.toml`; lazy imports keep the pyyaml-only job green.
- **Skill contract**: wire `skills/morning-check/SKILL.md` into
  `scripts/validate_repo.py`'s expected-skill list and any skill-wiring test
  (`tests/test_suite_wiring.py` / `tests/test_skill_contracts.py`) that
  enumerates skills, mirroring how the other skills are registered.

## Out of scope (this pass)

- `/schedule` automation and any cron/daemon (P1 note: manual first).
- Live earnings-calendar fetching (stored `next_earnings` only).
- Multi-portfolio support (P0 is single `portfolio.yaml`).
- FX conversion (all comparisons are in native currency).
- P2 outcome scoring — but the structured `findings` are shaped to be
  P2-consumable later.

## Verification

1. `python -m unittest discover -s tests -p 'test_*.py' -v` — green, including
   the new tests (run in the repo `.venv` / `uv`).
2. `python scripts/validate_repo.py --profile full` — passes with the new skill
   registered.
3. `python scripts/morning_check.py --home tests/fixtures/<state-home> --offline
   --prices tests/fixtures/<quotes>.yaml` — emits the expected brief.
4. End-to-end (manual, real session): configure `~/.investing-home` with at
   least one held name and one watchlist name → invoke the `morning-check`
   skill → confirm the brief groups findings correctly, the fallback prompts for
   a failed quote, LLM KPI checks cite a source, and the opt-in save writes
   `monitoring/YYYY-MM-DD-morning-check.md`.
