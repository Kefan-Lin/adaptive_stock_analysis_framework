# Inflection Discovery — Backtest & A-vs-B Comparison Report (v2)

**Date:** 2026-06-28 · **Code:** commit `d7c0163`
**Run:** engine B, point-in-time, free data only.
**v2 changes** (the report's own "next steps", now done): enlarged the control
universe so top-N is genuinely selective; improved C keyword precision; added an
IFRS/20-F path for foreign filers; attempted (and reverted) a ¬trap strengthening.
Results below **supersede the v1 thin-universe numbers**.

> **What these numbers are.** A discrimination smoke-test, **not** generalizable
> accuracy. n = 14 positive events / 9 trap tickers; every rate has a wide Wilson
> CI; treat as directional. Point-in-time integrity is verified at runtime (the
> 4-canary leak battery passes against live yfinance/EDGAR; 125 tests pass).

## Headline: the selectivity correction

The single most important v2 finding. v1 used a 30-name control arm (median ~13
eligible/date), so "top-10" was barely selective (~top 77%) and the 57% hit rate
was **inflated**. With a realistic universe (65-name control arm, **median ~28
eligible/date**), top-10 is a real cut (~top 36%):

| Metric (control=65, median eligible≈28) | top-10 | top-20 |
|---|---|---|
| **Hit rate** | **3/14 = 21%** (CI 8–48%) | 6/14 = 43% (CI 21–67%) |
| **Trap rate** | 4/9 = 44% (CI 19–73%) | 5/9 = 56% (CI 27–81%) |
| Mean lead (hits) | ~5 months | ~5 months |
| **Forward return 12m, picks vs control** | **+78% vs +18%** | +74% vs +12% |
| Forward return 6m, picks vs control | +23% vs +18% | +33% vs +10% |

**The honest read:** the D ranker does **not** reliably push the specific labeled
inflections into the absolute top-10 against ~28 other depressed names — it only
captures the strongest-signal ones (AXTI, MU-2023, NVDA at top-10; +LITE, MU-2016,
NFLX at top-20). BUT the names it **does** rank at the top went on to **beat the
depressed universe by ~60pp at 12 months** (+78% vs +18%). So D carries real
economic signal at the top even though binary top-10 recall is modest. As a
"the top of the ranking outperforms" tool it works; as a "catches exactly these 14
names in top-10" tool it is weak — and only the realistic universe reveals that.

### Per-name (control=65)

- **top-10 hits:** AXTI, MU (2023), NVDA. **top-20 adds:** LITE, MU (2016), NFLX.
- **Persistent misses:** BB/NOK/BILI (narrative or foreign-filer — see below),
  SNDK (post-spin, A gate can't assess <3y history), AMD-2016/INTC-2025 (already
  rallied by the test date — A gate discipline), META/COHR (depressed + real but
  out-ranked by peers on D).
- **Traps correctly avoided (top-10):** BBBY, LUMN (weak turn → rank too low to
  surface), LCID, FFAI, BLNK (cash-burn → caught by the runway filter).
- **Traps still flagged (top-10):** PTON (margin bounce off a COVID-writedown
  trough), ZM (dead-money, flat+profitable), INTC-fakestart, FOSL. These are the
  genuinely hard cases (below).

## A vs B on the narrative (C) dimension

**v2 improved B's lightweight C** (review finding): keyword matching is now
word-boundary + cover-page/glossary boilerplate is stripped. The v1 false
positives are gone — `FedRAMP` no longer matches "ramp", and "large accelerated
filer" no longer matches "accelerating". Effect on scores (cleaner, less
inflated): BB C 0.67→0.44, MU C 0.80→0.65.

Even so, A (LLM) retains an edge on the same EDGAR text — demonstrated on the
names numeric-B misses:

- **BB @2020-12** — B(numeric)=0.01 (no earnings turn, correct), C(keyword)=0.44.
  The 2020 10-Q literally says *"achieving design wins with automotive OEMs"*,
  *"leverages artificial intelligence and machine learning"*, *"cost reduction
  measures to preserve financial flexibility"*. A reading this affirms a genuine
  QNX-automotive + cybersecurity + AI pivot **and reasons about whether the design
  wins are material** — judgment the keyword counter cannot make (it only knows
  the words are present). This is the A-vs-B edge the design predicted: same
  information set, the LLM's C judgment is higher-precision than code features.

**Method/caveats (honest):** A's comparison-mode (same frozen EDGAR-only corpus,
same harness) is the only mode comparable to B; A's benchmark hit-rate would be a
**memorization-contaminated upper bound** (the model has seen these outcomes), so
a full automated A backtest needs an LLM-API scoring loop (out of v1/v2 scope) and
a post-training-cutoff holdout (SNDK-2025, INTC-2025, NBIS-2025 are the natural
holdout names). v2 delivers the A-vs-B *spot validation*, not a full A backtest.

## Improvements delivered (the v1 "next steps")

1. **Control universe enlarged** (30→65; median eligible 13→28) → the selectivity
   correction above. *Done.* (Sampling free tickers caps the count; 200+ needs a
   much larger random draw, noted.)
2. **C precision** — boilerplate-stripped, word-boundary keywords. *Done.*
3. **Foreign-filer path** — added IFRS (`ifrs-full`) fundamentals + 20-F/6-K text.
   *Partial by reality:* NOK files IFRS but **no quarterly XBRL** (annual/semi
   only), and BILI files **annual** us-gaap — so a *quarterly* B signal remains
   unavailable for foreign private issuers regardless of taxonomy. They score on
   price (A) only. This is a structural free-data gap, now documented, not a bug.
4. **¬trap strengthening — attempted and REVERTED (the honest result).** A
   gap-tolerant secular-decline detector + a turn-strength eligibility gate were
   built and tested. Both were reverted because, on free data:
   - a multi-year revenue decline does **not** separate a structural decliner from
     a cyclical trough, so the secular detector false-flagged real turnarounds
     (LITE, INTC-2025) whose revenue was still down at the test date; and
   - deeply-depressed **real** turnarounds (META 0.24, NVDA 0.45, NFLX 0.29) have
     turn scores that **overlap the value traps** (BBBY 0.25, BLNK 0.28), so no
     turn threshold excludes traps without also killing positives.
   **Conclusion:** separating depressed value traps from depressed real
   turnarounds is not reliably possible with free *numeric* signals. It needs
   richer judgment — management quality, end-market structural analysis,
   capital-allocation history — which is exactly **Implementation A's (LLM)
   domain**. The real next step is to test whether A's qualitative ¬trap judgment
   beats B's mechanical filter, not to hand-tune more thresholds (which would
   overfit this tiny benchmark).
5. **Paid point-in-time dataset — not done (blocked by the free-data decision).**
   This would lift the probe to a generalizable accuracy estimate and revive the
   estimate-revision signal, but it costs money and needs a data subscription /
   credentials. Left for the user to decide.

## Remaining honest limitations

- **Weak top-10 discrimination among depressed peers** (hit 21%): D surfaces the
  strongest inflections but doesn't out-rank all depressed peers; forward-return
  suggests the top of the ranking still outperforms.
- **Hard traps persist:** PTON (margin bounce off a catastrophic trough reads as a
  turn), ZM (cheap+profitable+flat = "dead money"), INTC-fakestart (depressed +
  rich AI/foundry narrative — indistinguishable from a real turn in 2022–24
  except in hindsight). These are intrinsic, not tuning failures.
- **Foreign-filer quarterly gap** (NOK/BILI), **post-spin gating** (SNDK),
  **small-n / regime-noisy forward return** — unchanged from v1.

## Verdict & next steps

The mechanism’s **point-in-time machinery is sound** (leak battery green) and its
**top-ranked picks outperform the depressed universe at 12 months**, but a
realistic universe shows its top-10 **recall of specific inflections is modest
(21%)** and the value-trap problem is **not solvable with free numeric signals**.
The highest-value next step is no longer more numeric tuning — it is to run
**Implementation A (LLM) in full comparison mode** (and a post-cutoff holdout) to
test whether qualitative judgment delivers the ¬trap discrimination and narrative
recall that engine B structurally cannot. A one-time paid point-in-time dataset
(user decision) would make any of these numbers generalizable rather than a probe.
