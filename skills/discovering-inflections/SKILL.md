---
name: discovering-inflections
description: Use when the user wants to DISCOVER candidate stocks at an earnings or narrative inflection (depressed, out-of-favor names whose fundamentals or story have started to turn) rather than analyze a ticker they already named. Produces a ranked candidate list and routes the best names into analyzing-stocks. This is the upstream discovery front-end; analyzing-stocks remains the per-name research engine.
---

# Discovering Inflections

## Overview

Surface companies at an **earnings or narrative inflection** — a depressed base
with a turning second derivative — *before* consensus fully reprices them, then
hand the best candidates to `$analyzing-stocks` for a full work-up.

Core principle: **低预期底 + 二阶导转正,赶在共识完全重定价之前**。This is the
inverse of momentum screening (which buys after strength shows up) and of naive
value screening (which buys cheapness and walks into value traps).

This skill is the **Implementation A** of the design in
`docs/plans/2026-06-28-inflection-discovery-design.md`: an LLM-judgment funnel.
It shares one scorecard taxonomy and one point-in-time backtest with the
code-first **Implementation B** (`inflection_discovery/engine_b/`), so the two
are comparable.

## The Scorecard (shared IP)

Rank by `D` among names where `A ∧ (B ∨ C) ∧ ¬trap` holds. `A` is a **hard gate**.

- **A — Depressed base (hard gate).** ≥30% below the 3-year high, near the 52-week
  low, out of favor. No A ⇒ it's a momentum chase, not a turnaround. Exclude
  loved hypergrowth names (CRDO/NBIS-type) by construction.
- **B — Earnings second derivative turning up.** Sequential revenue/EPS
  acceleration (seasonally adjusted via YoY-of-YoY), gross-margin troughing and
  ticking up, inventory days falling / destocking ending.
- **C — Narrative re-rating.** New TAM/segment, design wins, "AI/datacenter",
  strategic review, new management, spin-off, capital-return start, sell-side
  re-engagement — read from filings, calls, and news.
- **¬trap — not a value trap / head-fake.** Survivable balance sheet (runway,
  dilution), cyclical dip vs secular decline, durable turn vs dead-cat. Reuse the
  value-trap diagnostics in `$analyzing-stocks` `references/value-investing-lens.md`.
- **D — Expectations gap + timing (ranker).** How far price/consensus still lag a
  confirmed turn; market starting to notice without fully repricing.

The numeric thresholds are in `inflection_discovery/scorecard/taxonomy.py` — the
single source of truth both implementations read.

## Two modes (keep them separate)

- **Live mode (production).** Read the open web — news, transcripts, live
  estimate snapshots — for the richest narrative judgment. This is how you
  actually discover names. Its results are reported on their own.
- **Comparison mode (evaluation only).** Score names from the **same frozen,
  as-of-T SEC EDGAR corpus** that Implementation B uses, under the same
  point-in-time backtest harness — no open web, no live estimates. Only this mode
  is compared head-to-head with B, so the experiment varies only the engine
  (LLM judgment vs code text-features), not the information set.

**Memorization caveat:** on the historical benchmark, an LLM already knows which
names turned. Treat A's benchmark hit-rate as a memorization-contaminated *upper
bound*, and prefer the post-training-cutoff holdout for an honest read.

## Workflow

### Stage 1 — Broad pre-screen (cheap, wide)
Filter a universe to the **depressed base** (A gate) before spending judgment.
Run the thin pre-screen:

```
.venv/bin/python skills/discovering-inflections/scripts/prescreen.py --as-of 2024-06-30 --limit 50
```

It uses the shared point-in-time components to return a longlist of names that
pass the A gate (depressed) with reconstructable data. (For live use, seed the
universe from a sector/theme list or a screener export; the script accepts a
`--tickers` file.)

### Stage 2 — Dual-engine scorecard (LLM judgment)
For each longlist name, score the dual engine and fill the candidate contract
(`inflection_discovery/contract.py`):
- **Earnings engine:** read the latest 10-Q/10-K (sequential acceleration,
  margin/inventory inflection). In comparison mode, restrict to EDGAR ≤ T.
- **Narrative engine:** read filings/calls/news for the C signals above (live
  mode) or as-filed EDGAR text only (comparison mode).
- Apply the `¬trap` checks; set `passes_A_gate`, the A/B/C/trap_risk/D scores,
  evidence (cite sources), and a one-paragraph `thesis`.

### Stage 3 — Rank and route
Rank eligible candidates (pass A gate, trap_risk under ceiling) by `D`. For the
top N, hand each to `$analyzing-stocks` using the `routing` block (exchange,
currency, tradable line, `suggested_style = turnaround`) plus the `thesis` as the
scope for a full work-up.

## What this does and does not claim

The backtest that compares A and B on the labeled benchmark is a **discrimination
smoke-test, not a generalizable accuracy number** (small, selection-biased
sample; free data; see the spec). Report metrics with n and confidence intervals,
never a bare "X% accurate."

A full comparison-mode A-vs-B backtest exists: `inflection_discovery/harness/llm_backtest.py`
ranks LLM-scored candidates (`reports/llm_scores.json`) against the identical
control arm and harness B uses, so only the engine varies. On the benchmark A beats
B on both recall and trap-avoidance (top-10 36% vs 21% hit, 0% vs 44% trap; top-20
71% vs 43%, 22% vs 56%) — see `reports/comparison-report.md`. **These A rates are a
memorization-contaminated upper bound** (the model knows the outcomes).

A **post-cutoff holdout** (`reports/run_holdout.py`, T=2026-01-31, fresh blind
universe) tested that confound and split the result: A's **trap/quality screen
generalized** (cleared +125% vs flagged −17% forward) but its **ranking edge did
not** (top-5 +2% vs B +113% vs pool +72%, junk-rally regime, n tiny). So treat the
durable claim as the qualitative *real-business-vs-trap* judgment, **not** that A
out-ranks B; a larger multi-regime holdout is needed to settle the ranking question.
