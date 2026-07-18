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

- Manual trigger, or the P4 monthly scheduled task (see `skills/morning-check/references/scheduled-prompts.md`).
- Absolute native-currency returns; no FX and no benchmark this pass.
- Grouping uses fields the record already carries (stance, confidence,
  valuation zone, market); sector / valuation-family grouping is deferred.
- Forward-only: `historical` index rows are never scored.
- Default windows 90/180/365 days; override with `--windows`.
