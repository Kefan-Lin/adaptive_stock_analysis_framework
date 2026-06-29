# Inflection Discovery — Backtest & A-vs-B Comparison Report (v3)

**Date:** 2026-06-29 (v3: full Implementation-A backtest) · 2026-06-28 (v2: engine B)
**Run:** engines A (LLM judgment) and B (code), point-in-time, free data only.
**v3 change — the headline:** Implementation A (LLM) is now run through a **full
comparison-mode backtest** on the same harness as B (previously only a one-name
spot-check). A is scored from the same frozen ≤T EDGAR corpus B reads; results in
the new *A-vs-B full backtest* section below. **v2 changes** (B): enlarged control
universe, C keyword precision, IFRS/20-F foreign path, attempted+reverted ¬trap
strengthening.

> **What these numbers are.** A discrimination smoke-test, **not** generalizable
> accuracy. n = 14 positive events / 9 trap tickers; every rate has a wide Wilson
> CI; treat as directional. Point-in-time integrity is verified at runtime (the
> 4-canary leak battery passes against live yfinance/EDGAR; 135 tests pass).
> **A's rates are additionally a memorization-contaminated UPPER BOUND** — the
> model already knows these outcomes (see the A-vs-B section for why that is still
> a fair *engine* comparison).

## A-vs-B full backtest (v3) — LLM judgment vs code features

**The experiment.** Hold *everything* shared with engine B fixed — the depressed-base
A gate, price momentum, the identical 65-name control arm, the `score_D`
aggregation, and every metric definition in `summarize` — and swap **only** the
B / C / trap judgment of the benchmark candidate. B reads those from numeric
features + keyword counting (and in the v2 backtest ran **text-free**, so its
narrative C was null); A (the LLM) reads them from the same ≤T EDGAR filings +
PIT fundamentals (`reports/llm_scores.json`, one audit note per name). Each name
is ranked against the **same** depressed-peer backdrop B faces. So the A−B delta
is a clean ablation of *engine*, with byte-identical metric math.

**Validation that it's apples-to-apples:** B, recomputed inside the A harness,
**reproduces the stored v2 numbers exactly** (top-10 3/14 hit, 4/9 trap; top-20
6/14, 5/9). The only moving part is the engine.

| Metric (control=65, median elig ≈ 28-30) | **A (LLM)** | **B (code)** |
|---|---|---|
| Hit rate · top-10 | **5/14 = 36%** (CI 16–61%) | 3/14 = 21% (CI 8–48%) |
| Hit rate · top-20 | **10/14 = 71%** (CI 45–88%) | 6/14 = 43% (CI 21–67%) |
| Trap rate · top-10 *(lower=better)* | **0/9 = 0%** (CI 0–30%) | 4/9 = 44% (CI 19–73%) |
| Trap rate · top-20 *(lower=better)* | **2/9 = 22%** (CI 6–55%) | 5/9 = 56% (CI 27–81%) |
| Fwd return 12m, top-10 picks vs control | **+78%** vs +14% (5 picks) | +78% vs +18% (3 picks) |

**A beats B on both axes** — higher recall *and* fewer traps — and the wider
recall did **not** dilute pick quality (top-10 picks still +78% at 12m).

**Where A's recall edge comes from (top-20 adds vs B):** BB, NOK, COHR, INTC-2025
— exactly the **narrative / earnings-judgment** names a text-free keyword counter
can't see. (LITE and NFLX come in already at top-10.)

**Where A's trap edge comes from:** A's *structural-decline* judgment avoids
**LUMN, PTON, FOSL** — the traps B's mechanical filter surfaced. PTON is the
clearest win: B rewarded its gross-margin bounce off a negative trough; A reads
"margin up **but revenue still −22% YoY and still burning cash → not a real
turn**."

**A's two residual misses are the intrinsically-hard cases the design predicted**,
not tuning failures:
- **ZM (dead money):** growth stalled at ~+3% with a **pristine** balance sheet, so
  there is *no* trap signal — only "no turn." Its deep depressedness (A≈0.99)
  pulls D into the top-20 despite a low turn. This is the limit of the 40%
  cheapness weight, not a judgment error.
- **INTC-2023 fake-start:** on the as-of numbers (revenue decline decelerating, GM
  recovered to 42%, EPS back positive) it is **indistinguishable from a real
  cyclical trough**. A is honestly fooled here too — this is the irreducible floor
  of free-data separability (encoded as the one allow-listed case in
  `tests/test_llm_backtest.py`).

**Honest caveats (unchanged and load-bearing):**
1. **Memorization upper bound.** The LLM knows these outcomes, so A's *absolute*
   rates overstate live performance. The comparison is still fair as an **engine**
   ablation (A vs B on the identical information set and harness), and the *pattern*
   — A wins precisely on narrative recall and structural-trap judgment, the two
   things B is built to miss — is the mechanism-level result, not the level.
2. **Control arm stays B-scored** by design: LLM-scoring 65 random tickers would be
   *more* biased (asymmetric memorization — known benchmark names vs unknown
   controls) and intractable. So A's hit/trap measure "does LLM judgment of the
   *named candidate* out-rank / clear the depressed-peer backdrop B faces."
3. **Positives scored at the single fixed hit-date** (t*−3mo); per-A lead-time is
   not measured in this pass.
4. The true next step for a *generalizable* read is a **post-training-cutoff
   holdout** (SNDK-2025, INTC-2025, NBIS-2025) scored live — that removes the
   memorization confound. Left as the honest open item.

*(The one-name spot-validation below is now subsumed by this full backtest; it is
kept as a worked example of the C-judgment mechanism.)*

## Post-cutoff holdout (v3) — the memorization confound, removed

The single honest gap in the section above is that the LLM **already knows** the
benchmark outcomes. So I ran a genuine holdout where the outcome is blind: **T =
2026-01-31** (after the model's Jan-2026 knowledge cutoff), a **fresh** universe of
16 depressed names sampled at random with **zero overlap** with the benchmark or
control arm, scored A (LLM) and B from ≤T evidence **before any forward return was
computed** (`reports/llm_holdout_scores.json`), then measured the realized **~5-month
forward return** (T → today). Most names are obscure micro-caps I have near-zero
priors on, so this is about as blind as a free-data test gets.

| ~5-month forward return (T=2026-01-31) | result |
|---|---|
| **A top-5 by D** (CNS, TRIP, FIP, LEAT, FLUT) | **+2%** |
| **B top-5 by D** (TRIP, FLUT, JBGS, SYRA, LEAT) | **+113%** |
| Depressed-pool base rate (all 16) | **+72%** |
| **A trap-CLEARED** (10 eligible names) | **+125%** |
| **A trap-FLAGGED** (6 names, trap>ceiling) | **−17%** |

**This is a deliberately unflattering, honest result, and it splits cleanly:**

- **What generalized — the binary trap / quality screen.** A's *cleared* names
  returned **+125%** vs *flagged* **−17%** — a real out-of-sample spread. Of the 6
  A flagged as un-investable (shells / SPAC-collapses / serial diluters), 5 were
  flat-to-disastrous (JTAI −75%, SGLY −45%, AMST −40%, ALDA/ANKM ~0%); the one miss
  was GUTS (+62%, a flagged shell that popped anyway). So "don't step on the dead
  shells" — the core ¬trap judgment — **held up blind**.
- **What did NOT generalize — the fine-grained D ranking.** A's top-5 (+2%)
  **underperformed both B's top-5 (+113%) and the pool (+72%)**. The biggest winners
  (LESL +600%, SYRA +575%, PVLA +93%) were ranked **low** by A (ranks 6, 7, 10):
  its quality/safety tilt pushed the volatile small-caps down, and two of its actual
  picks fell (FLUT −37%, FIP −15%). The benchmark's headline "A out-ranks B" did
  **not** reproduce here.
- **Regime + n caveat (load-bearing).** A +72% pool base rate over 5 months is a
  **violent small-cap/junk rally** — exactly the regime where the junkiest survivors
  rip and quality lags. With **n = 5 picks over one 5-month regime**, neither
  engine's *ranking* result is statistically meaningful. B's win is essentially one
  name (SYRA, +575%, in B's top-5 but not A's).

**Honest bottom line.** The memorization-free holdout confirms A's **trap/quality
discrimination** carries real out-of-sample signal, but provides **no evidence** that
A's *ranking* adds forward alpha over B or the depressed universe — and one (noisy,
regime-specific) data point where it underperformed by tilting too defensive. So the
benchmark's A-beats-B *ranking* margin should be read as **memorization-flavored, not
confirmed**; the durable, generalizing win is the qualitative **"is this a real
business or a trap"** call. A larger, multi-regime holdout is the real way to settle
the ranking question. *(Reproduce: `reports/run_holdout.py`.)*

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
   overfit this tiny benchmark). **→ v3 update: now tested.** A's full backtest
   drops the trap rate to 0% (top-10) / 22% (top-20) vs B's 44% / 56% — A's
   structural-decline judgment flags LUMN/PTON/FOSL that B missed. See the A-vs-B
   section at the top.
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

The mechanism's **point-in-time machinery is sound** (leak battery green) and the
**top-ranked picks outperform the depressed universe at 12 months**. Engine B
alone, on a realistic universe, has **modest top-10 recall (21%)** and **cannot
solve the value-trap problem with free numeric signals**.

**v3 closes the loop the v2 report opened:** Implementation A (LLM) was run in full
comparison mode and **delivered exactly the discrimination B structurally cannot** —
top-10 recall 36% vs 21% and trap rate 0% vs 44% (top-20: 71% vs 43%, 22% vs 56%),
on the identical harness and control arm. A's gains are concentrated precisely
where the design predicted (narrative recall: BB/NOK/COHR/INTC-2025; structural
traps: LUMN/PTON/FOSL), and A's only residual failures are the two intrinsically
ambiguous cases (ZM dead-money, INTC fake-start). So the architecture's core
thesis — **a code engine for cheap, leak-free breadth; an LLM engine for the
qualitative judgment that the numbers can't encode** — is now empirically
supported, not just argued.

**The memorization confound was then tested directly** (post-cutoff holdout,
above), and it matters: blind, A's **trap/quality screen survived** (+125% cleared
vs −17% flagged) but its **ranking edge did not** (top-5 +2% vs B +113% vs pool
+72%, in a junk-rally regime, n tiny). So the durable, generalizing claim is the
qualitative *"real business vs trap"* judgment — **not** that A out-ranks B. The
benchmark ranking margin is memorization-flavored.

**What remains:** a **larger, multi-regime holdout** (more names, more T-dates,
not one risk-on window) is the only way to settle whether A's ranking adds forward
alpha; a one-time paid point-in-time dataset (user decision) would let the labeled
hit/trap backtest itself be run on post-cutoff data rather than a probe.
