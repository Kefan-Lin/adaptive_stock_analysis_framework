# P2 Outcome-Scoring — Design

Status: design (approved decisions; pending spec review)
Depends on: P0 decision-records layer (state home, decision records) and P1
morning-check infrastructure (`scripts/morning_check.py` price-source classes,
`scripts/validate_records.py` loaders and symbol vocabulary).
Defers: benchmark-relative returns, FX, sector / valuation-family grouping,
position-size / P&L weighting, `/schedule` automation.

## Problem

The framework now has memory (P0) and a monitoring sweep (P1), but no way to
ask *were the decisions any good?* Every decision record carries the machine
fields needed to answer that — `date`, `price_at_decision`, `stance`,
`weighted_fair_value`, `scenarios`, price `triggers` — yet nothing reads a
record months later and measures the realized outcome.

P2 is that measurement harness. Per the P0 design's own P2 note
(`docs/plans/2026-07-03-decision-records-design.md`, "Future phases"): *parses
records; computes 90/180/365-day outcomes vs `stance` / `weighted_fair_value` /
trigger hits; calibration report by sector & valuation family. Forward-only.*

The record schema was deliberately shaped so P2 is a **pure consumer** — it adds
no fields and changes no other skill. It reads records, fetches historical
prices, and reports.

### Forward-only, and honestly empty at first

P0 records only began accumulating in early July 2026, so on any near-term run
*no record is 90 days old yet* — every real record scores as **pending**. This
is expected and correct: P2 is the harness that accrues signal as records
mature. The deterministic tests exercise the matured path with dated fixtures so
the machinery is proven before real outcomes exist.

## Approved scope decisions

- **Architecture:** hybrid — a deterministic Python script + an LLM skill,
  mirroring P1.
- **Return basis:** **absolute native-currency return** over each window, no FX
  and no benchmark, judged against the stance's implied direction and against
  `weighted_fair_value` / scenario convergence. (Benchmark-relative is a later
  pass.)
- **Calibration grouping:** by fields the records **already carry** — `stance`,
  `confidence`, `valuation_zone`, `market`. No schema change. (The P0 spec's
  "sector & valuation family" is deferred until those fields exist in the
  record.)
- **`Hold` scoring:** a `Hold` is a directional *hit* when the exit price stays
  inside the record's `[bear, bull]` scenario band (the thesis envelope held);
  when the record carries no scenarios, fall back to a `±10%` return band.
- **v1 extras included:** scenario-landing (which band the exit lands in) and
  price-trigger-touch (did `add_on` / `trim_exit` levels get hit within the
  window). Both are cheap given the history fetch already made.
- **Price data:** live historical closes (yfinance for US/HK/KR/AU, akshare for
  CN A-shares), lazily imported, with an owner-provided / file fallback for
  offline runs and tests.

## Architecture

Two units with a clean seam between deterministic scoring and LLM narration.

### 1. `scripts/outcome_score.py` — deterministic core

Pure stdlib + PyYAML (no pandas/yfinance/akshare imported at module top), so it
runs in the main pyyaml-only CI job. Reuses P0/P1 helpers rather than
re-implementing them:

- from `validate_records.py`: `FRONTMATTER`, `as_date`, `is_number`,
  `resolve_home`, `SYMBOL_PATTERNS`, `MODE_PRIORITY`.
- from `morning_check.py`: `provider_for` (canonical → provider mapping) and the
  lazy-import pattern for the live provider.

Responsibilities:

- Resolve the state home (same contract as `validate_records.py` /
  `morning_check.py`: `--home PATH`, default resolves `~/.investing-home`).
- Load **every** real decision record (not just the latest per symbol — every
  record is a datapoint). Skip `INDEX.md`, unparseable files, and records
  lacking `price_at_decision` + `date`. `historical` rows live only in
  `INDEX.md`, never as record files, so forward-only falls out for free.
  `mode: research` records are scored when they carry a stance and/or a WFV.
- Fetch historical closes through an injectable `PriceHistory` (below).
- Compute per-record outcomes for each matured window, aggregate into a
  calibration report, and emit structured JSON plus rendered markdown.

### 2. `skills/outcome-scoring/SKILL.md` — LLM wrapper

Orchestrates a run:

1. Resolve the state home. If unconfigured/empty, say so and stop — nothing to
   score; do not invent state.
2. Run `scripts/outcome_score.py --format json`; capture `scored`, `pending`,
   `data_gaps`, `calibration`.
3. **Fallback for `data_gaps`:** for each missing historical close, ask the
   owner for the price on that date (or a quotes file) and re-run with
   `--prices <file>` so the record is scored rather than dropped.
4. **Narrate the calibration:** summarize what the buckets say (e.g. whether
   High-confidence or Accumulation-zone calls actually realized better), call out
   the strongest and weakest cohorts, and note where N is too small to trust.
5. Offer to save the report as `scoring/YYYY-MM-DD-outcome-scoring.md` in the
   state home (opt-in per run, mirroring P1's `monitoring/`).

## Price source & provider mapping

P1 needed only a spot quote; P2 needs **historical** closes. New seam:

`PriceHistory.close_on(symbol, date) -> float | None` — the close on `date`, or
the nearest **prior** trading day within a short look-back window (default 7
calendar days) to absorb weekends/holidays. Returns `None` when no close is
found (→ a `data_gap`); never raises out.

- **`LiveHistory`** — the default. Maps canonical → provider via P1's
  `provider_for`, then lazy-imports yfinance / akshare *inside* the fetch and
  pulls a date-ranged history (`yfinance` `history(start,end)`; `akshare`
  `stock_zh_a_hist(..., start_date, end_date)`). One fetch spanning
  `[date_of_decision, date_of_decision + max_window]` per record serves every
  window's `close_on` **and** the window low/high used by trigger-touch, so each
  record hits the network at most once. Any per-name failure → `None`.
- **`FileHistory`** — reads a `{symbol: {YYYY-MM-DD: close}}` YAML/JSON (via
  `--prices FILE`); the same nearest-prior-trading-day rule applies over the
  provided dates. Used for the owner-provided fallback and for tests. With
  `--offline`, this is the only source (no network).

The canonical → provider mapping stays in lockstep with `SYMBOL_PATTERNS` via
the existing contract test discipline (P1 already asserts this); P2 reuses
`provider_for`, so no new mapping is introduced.

## Per-record scoring

For a record with decision date `D`, entry price `P0 = price_at_decision`, and
each window `w ∈ {90, 180, 365}` calendar days:

- **Maturity:** if `as_of < D + w`, the window is **pending** (recorded, not
  scored). Otherwise fetch `Pw = close_on(symbol, D + w)`; if unavailable, record
  a **data gap** for `(symbol, D, w)`.
- **Return:** `return_w = (Pw − P0) / P0`, in the instrument's native currency.
- **Direction hit vs `stance`:**
  - `Buy` / `Add` → hit when `return_w > 0`.
  - `Reduce` / `Avoid` → hit when `return_w < 0` (lightening / avoiding was
    vindicated by a decline).
  - `Hold` → hit when `Pw` is inside `[bear, bull]` from `scenarios`; when the
    record has no `scenarios`, hit when `|return_w| ≤ 0.10`.
  - Records with no `stance` (rare `research` runs) get no direction hit; their
    return and WFV convergence are still reported.
- **WFV convergence** (when `weighted_fair_value` present): the price moved the
  right way and got closer to fair value.
  `gap_closed_w = (|P0 − WFV| − |Pw − WFV|) / |P0 − WFV|` (a signed ratio: `1.0`
  = reached WFV exactly, `0` = no closer, negative = moved away). A boolean
  `converged_w` is true when `gap_closed_w > 0` **and** `sign(return_w) ==
  sign(WFV − P0)` (moved toward WFV, not merely past it in the wrong direction).
  When `P0 == WFV` the ratio is undefined (already at fair value); convergence is
  omitted for that record/window rather than reported.
- **Scenario landing** (when `scenarios` present): which band `Pw` falls in —
  `below_bear | bear_base | base_bull | above_bull` — feeding future
  scenario-range calibration.
- **Price-trigger touch** (when price `triggers` present): using the window's
  low/high from the same history fetch, whether each `add_on {type: price,
  direction: below}` level was touched (`window_low ≤ level`) and each
  `trim_exit {direction: above}` level was touched (`window_high ≥ level`) within
  `[D, D + w]`. `window_low` / `window_high` come from the true daily range under
  `LiveHistory`; under `FileHistory` they are the min / max of the closes the file
  supplies within `[D, D + w]` (lower-fidelity but sufficient for offline tests).
  Reported per trigger as touched / not; judging whether *acting* on a touch would
  have helped is left to the LLM narrative.

Every per-record outcome carries its grouping keys (`stance`, `confidence`,
`valuation_zone`, `market`, `mode`, `symbol`, `date`) so aggregation is a pure
group-by.

## Calibration (aggregation)

Deterministic group-by over the scored outcomes. For each grouping dimension
`stance | confidence | valuation_zone | market`, and for each window, one table:

| bucket | N | direction hit-rate | mean return | median return | WFV-convergence rate |

Plus an overall summary row per window (all scored records). Buckets with `N`
below a small floor (default 3) are shown but flagged `low-N` so the narrative
does not over-read them. The payoff: whether the framework's own confidence and
valuation-zone labels are predictive of realized outcomes.

## CLI

```
python scripts/outcome_score.py [--home PATH] [--as-of YYYY-MM-DD]
    [--windows 90,180,365] [--prices FILE] [--offline] [--format json|md]
```

- `--as-of` fixes "today" for deterministic tests (default: system date).
- `--windows` overrides the default horizon set (comma-separated days).
- `--prices` + `--offline` make a fully offline, network-free run.
- Exit codes mirror P1: `0` clean run (with or without scored records), `2`
  environment error (no state home / unreadable). Having only pending records is
  a clean `0`.

## Output

`--format json`:

```json
{
  "as_of": "2026-10-15",
  "windows": [90, 180, 365],
  "scored": [
    {"symbol": "ACME", "date": "2026-06-01", "mode": "new-idea",
     "stance": "Buy", "confidence": "Medium", "valuation_zone": "Accumulation",
     "market": "US", "price_at_decision": 100.0,
     "windows": {
       "90": {"exit_price": 118.0, "return": 0.18, "direction_hit": true,
              "gap_closed": 0.45, "converged": true,
              "scenario_landing": "base_bull",
              "trigger_touches": [{"group": "trim_exit", "level": 130,
                                   "touched": false}]}
     }}
  ],
  "pending": [{"symbol": "NVDA", "date": "2026-08-01", "window": 90,
               "matures_on": "2026-10-30"}],
  "data_gaps": [{"symbol": "0700.HK", "date": "2026-05-01", "window": 180,
                 "reason": "no close near 2026-10-28"}],
  "calibration": {
    "by_stance": {"90": {"Buy": {"n": 4, "hit_rate": 0.75, "mean_return": 0.09,
                                 "median_return": 0.11, "wfv_convergence": 0.5}}},
    "by_confidence": {"...": {}},
    "by_valuation_zone": {"...": {}},
    "by_market": {"...": {}},
    "overall": {"90": {"n": 7, "hit_rate": 0.71, "mean_return": 0.06,
                       "median_return": 0.08, "wfv_convergence": 0.43}}
  }
}
```

`--format md`: a calibration report — a summary line per window, the by-dimension
tables above, then a "Pending" and "Data gaps" appendix so untested and
un-fetchable records are visible rather than silently absent.

## Testing & CI

- **`tests/test_outcome_score.py`** (main pyyaml-only suite): a fixture state
  home under `tests/fixtures/` plus a `FileHistory` of dated closes. Cases:
  matured vs pending (as-of before/after `D + w`); each direction rule
  (Buy up/down, Reduce down/up, Hold in-band vs out-of-band, Hold no-scenarios
  ±10%); WFV convergence sign and `gap_closed` arithmetic; scenario-landing band
  boundaries; trigger-touch fired vs not via window low/high; a `data_gap` when a
  close is missing; forward-only (a `historical` INDEX row and a record lacking
  `price_at_decision` are ignored); calibration bucketing and `low-N` flagging;
  `close_on` nearest-prior-trading-day fallback.
- **Live-history smoke test:** network-gated (skips offline) or placed in the
  `inflection-tests` CI job, which already installs yfinance/akshare.
- **No new main-job dependency:** yfinance/akshare are already in
  `pyproject.toml`; lazy imports keep the pyyaml-only job green.
- **Skill contract:** register `skills/outcome-scoring/SKILL.md` in
  `scripts/validate_repo.py`'s expected-skill list and any skill-wiring test
  (`tests/test_suite_wiring.py` / `tests/test_skill_contracts.py`) that
  enumerates skills, mirroring how `morning-check` is registered.

## Out of scope (this pass)

- Benchmark-relative / excess returns (needs per-market index series).
- FX conversion (all returns are native-currency).
- Sector / valuation-family grouping (deferred until the record schema carries
  those fields).
- Position-size or P&L weighting (v1 scores the *judgment*, equal-weight per
  record, not the book).
- `/schedule` automation (manual trigger first, like P1).
- Scoring `historical` backfill rows (index-only, no frontmatter).

## Verification

1. `python -m unittest discover -s tests -p 'test_*.py' -v` — green, including
   the new tests (run in the repo `.venv` / `uv`).
2. `python scripts/validate_repo.py --profile full` — passes with the new skill
   registered.
3. `python scripts/outcome_score.py --home tests/fixtures/<state-home> --offline
   --prices tests/fixtures/<closes>.yaml --as-of <matured-date>` — emits the
   expected calibration report.
4. End-to-end (manual, real session, once records mature): configure
   `~/.investing-home`, invoke the `outcome-scoring` skill → confirm the report
   groups scored records correctly, pending/data-gap appendices list the rest,
   the missing-close fallback prompts for a quote, and the opt-in save writes
   `scoring/YYYY-MM-DD-outcome-scoring.md`.
