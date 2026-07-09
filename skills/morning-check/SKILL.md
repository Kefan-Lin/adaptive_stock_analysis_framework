---
name: morning-check
description: Use when the user wants a morning check, a portfolio monitoring sweep, or a 晨检 across their tracked names. Reads the private state home (portfolio.yaml plus decision records), flags crossed price triggers, stale review dates, upcoming earnings, and cash-secured-put assignment risk, judges the free-text KPI and event triggers live, and emits one action brief. Manual trigger only; scheduling is out of scope.
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

   Capture `findings`, `data_gaps`, and `llm_todo` from the JSON. Each finding
   carries a `symbol`, `kind`, `urgency` (`act` / `review` / `watch`), a human
   `detail`, and structured `evidence`.

3. **Fill price gaps (fallback).** For each `data_gaps` entry whose reason is a
   failed or unavailable price, ask the user for a current quote. Write the
   collected quotes to a temporary YAML `{symbol: price}` file and re-run with
   `--prices <file>` so those names are checked rather than dropped. A
   `data_gaps` entry reading "earnings date unknown" is not a price gap — carry
   it into the brief as a "verify earnings date" item instead. A
   "held/underlying but no decision record on file" gap means an owned name has
   no thesis on record — surface it so the user can decide whether to write one.

4. **Judge the free-text triggers.** For each `llm_todo` item (KPI and event
   triggers, and `monitor` KPIs), do live research (recent news and filings) and
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
- Default windows: earnings within 7 days, `review_by` within 14 days. Override
  per run with `--earnings-window` / `--review-window`.
