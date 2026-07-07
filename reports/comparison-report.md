# Inflection Discovery — Backtest & A-vs-B Comparison Report (v4)

**Date:** 2026-07-07 (v4.1: dead-name mechanism fix — curated registry +
identity-break truncation) · 2026-07-06 (v4: ADV + dead-name metric rerun;
holdout downgrade) · 2026-06-29 (v3: full Implementation-A backtest) ·
2026-06-28 (v2: engine B)
**Run:** engines A (LLM judgment) and B (code), point-in-time, free data only.

> **v4 (2026-07-06):** metrics rerun with the **ADV liquidity haircut**
> (`MIN_ADV_USD`, per-scan-date illiquid exclusion) and **dead-name handling**,
> and **holdout claims downgraded per an independent methodology audit**. The
> A-vs-B tables below are regenerated from the fresh
> `reports/backtest_results_v4_top{10,20}.json`; the holdout section is
> regenerated from `reports/holdout_results.json` (now carrying median,
> leave-N-out, and ceiling-boundary fields). Numbers that moved vs v3 are shown
> `old → new` the first time they appear. v3 mechanism/narrative text is kept
> where still true.
>
> **v4.1 (2026-07-07) — dead-name mechanism corrected.** The v4 draft claimed
> dead names were realized via *trading-gap truncation* and that the
> recycled-ticker canary was green. Both were wrong as stated: yfinance
> **re-anchors recycled tickers to the current live entity and drops the dead
> leg entirely** (verified 2026-07-07 on BBBY/HTZ/SPCE/SHLD — BBBY's served
> 24-year history bottoms at $2.65; the 2023 collapse to pennies is simply
> absent from the feed), so no series-shape rule can realize such a loss, and
> the canary was in fact **failing live** (BBBY 12m fwd read +0.30). The fix:
> dead benchmark names are floored via a **curated dead-ticker registry**
> (`inflection_discovery/pit/dead_tickers.py` — death date + terminal value,
> same curated-fact class as the benchmark labels), with **identity-break
> truncation** (>30-day trading gap, or a sub-$1 close jumping >8× in one
> session) retained as defense-in-depth for feeds that do keep both legs. The
> `recycled_ticker` canary now **passes live** (2026-07-07 data: BBBY 12m fwd
> = **−1.0**). The registry itself moved no number (BBBY/FFAI sit outside the
> pick baskets and the benchmark-excluded control arm). The **forward-return
> summaries and the holdout were regenerated same-day under this metric
> layer**, with truncation scoped to the **identity segment containing T**: a
> break after T bounds the window (successor prices can't mask a collapse); a
> break at/before T only trims the left (a transient two-session 2012 bad tick
> in LEAT's feed must not zero a 2026 window — segment scoping also makes the
> value invariant to whether the feed serves such glitch rows at all, which it
> does nondeterministically). The regeneration **purged 25 stitched-artifact
> control values** across the four summaries: 5 of 65 control names
> (BESS/CRDV/ELVG/IVDN/MYCB) carry recycled-shell stitch artifacts — flat
> penny closes jumping 19–130× overnight — that the prior v4 control means had
> ingested as real returns; worst cases were a spurious **+14,900%** (IVDN)
> and **+11,800%** (CRDV) inside the 2024-08-30 / 2024-09-30 pick-date control
> means. Effect: 12m control means fell from +28%/+38% (A cuts) and +13%/+42%
> (B cuts) to a clean **+9–11%**; **hit/trap rates, ranks, eligibility,
> exclusions, and pick means are unaffected** (rank data byte-identical), and
> the holdout regenerated **byte-identical** to its previously committed
> numbers.
>
> **Two things the rerun changed, stated plainly.** (1) The A-vs-B hit/trap
> **levels rose vs the v3 table** because v4 runs on the current harness (median
> eligible ≈ 14/date, vs the ~28 the v3 table quoted) — and that halving of the
> eligible field is **caused by the ADV haircut itself**: the $1M-ADV gate
> removes roughly half of the 65-name control arm as verified-illiquid
> micro-caps/preferreds (the audit measured ~32 of 65 sub-$1M; at 2024-06-30
> the eligible field goes **27 pre-ADV → 13 post-ADV**, with **0 None-drops** —
> every exclusion a verified sub-$1M name, none unverifiable). The **thinner
> control denominator — not engine improvement — is what mechanically lifted
> the absolute hit levels ~30pp vs v3**; the *engine ordering* (A ≥ B on both
> recall and trap-avoidance) is unchanged. (2) The **ADV haircut excluded 0
> labeled evaluation rows** (`excluded_illiquid: []` at every hit-date, both
> engines, both cuts; its only firings on labeled names are AXTI's two
> *intermediate B-scan* dates). So the haircut **is load-bearing — on the
> levels, via the control denominator** — just not via labeled-row exclusions,
> which were zero. Which is exactly why the **A−B gap, not the levels**, is
> the read.

**v3 change — the headline:** Implementation A (LLM) is now run through a **full
comparison-mode backtest** on the same harness as B (previously only a one-name
spot-check). A is scored from the same frozen ≤T EDGAR corpus B reads; results in
the new *A-vs-B full backtest* section below. **v2 changes** (B): enlarged control
universe, C keyword precision, IFRS/20-F foreign path, attempted+reverted ¬trap
strengthening.

> **What these numbers are.** A discrimination smoke-test, **not** generalizable
> accuracy. n = 14 positive events / 9 trap tickers; every rate has a wide Wilson
> CI; treat as directional. Point-in-time integrity is verified at runtime (the
> 5-canary leak battery passes against live yfinance/EDGAR as of 2026-07-07 —
> including the recycled-ticker canary, which passes because dead names are
> realized via the curated dead-ticker registry, BBBY 12m fwd = −1.0; the
> `inflection_discovery` + contract suites pass). **A's rates are additionally a
> memorization-contaminated UPPER BOUND** — the model already knows these outcomes
> (see the A-vs-B section for why that is still a fair *engine* comparison).
> **v4/v4.1:** prices now pass through the ADV liquidity haircut and dead-name
> handling (curated registry floor + identity-break truncation) before any
> metric is computed (see the v4/v4.1 notes above for their effect on this run).

## A-vs-B full backtest (v4) — LLM judgment vs code features

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
reproduces its own stored numbers, and both engines share a byte-identical control
arm (**control = 65**, median eligible = 14/date) and metric layer. The only moving
part is the engine.

**A-vs-B, v4 rerun** (`backtest_results_v4_top{10,20}.json`; post-ADV, post-dead-name).
`old → new` = v3 table → v4:

| Metric (control=65, median elig = 14) | **A (LLM)** | **B (code)** |
|---|---|---|
| Hit rate · top-10 | **10/14 = 71%** (36% → 71%) | 7/14 = 50% (21% → 50%) |
| Hit rate · top-20 | **12/14 = 86%** (71% → 86%) | 11/14 = 79% (43% → 79%) |
| Trap rate · top-10 *(lower=better)* | **2/9 = 22%** (0% → 22%) | 5/9 = 56% (44% → 56%) |
| Trap rate · top-20 *(lower=better)* | **2/9 = 22%** (unch.) | 6/9 = 67% (56% → 67%) |
| Fwd 12m, top-10 picks vs control | **+69%** vs +10% (n=10) | +69% vs +11% (n=7) |
| Fwd 12m, top-20 picks vs control | **+82%** vs +9% (n=12) | +82% vs +10% (n=11) |
| `excluded_no_data` / `excluded_illiquid` | 2 (WBA×2) / **0** | 2 (WBA×2) / **0** |

**A beats B on both axes** — higher recall *and* fewer traps, unchanged as an
*ordering* from v3 even though the v4 harness lifts both engines' absolute levels.
Two honest reads of the v4 numbers:

- **The levels rose because the cut got easier, not because the engines improved.**
  With median eligible = 14, "top-10" is ~top-70% and "top-20" is essentially the
  whole eligible field — so top-20 hit rates near 80–86% are *weakly selective by
  construction*, and top-20 trap rates (A 22%, B 67%) are the more informative half
  of the table. The **A−B gap** (recall +21pp top-10; trap −34pp top-10, −44pp
  top-20) is the load-bearing result, not the levels.
- **Forward-return convergence.** At v4 the two engines' *pick* baskets return
  almost identically (top-10 +69% both; top-20 +82% both), and after the v4.1
  artifact purge the **control baskets do too** (12m control ≈ +9–11% for both
  engines at both cuts) — so the pick-vs-control spread (~+58pp top-10, ~+72pp
  top-20) is engine-independent, and the A edge lives in **trap-avoidance and
  recall**, not in forward-return spreads. (The pre-purge read that A "beat
  different controls" — A +28%/+38% vs B +13%/+42% — was an artifact of
  stitched control values, not a real engine difference.) The v3 "+78%" pick
  figure is superseded by these n-labelled basket means.
- **`excluded_illiquid` = 0 at every hit-date** (shown beside `excluded_no_data` =
  2, the two WBA dates with no reconstructable XBRL). The ADV haircut *did* fire —
  AXTI is flagged illiquid on its 2024-03-30 and 2024-08-30 B-scan dates — but
  those are non-hit intermediate scans, so no labeled row was dropped. The
  haircut's load-bearing effect is on the **denominator** instead: it is what
  thins the eligible control field to ~14/date (v4 note), which sets the
  inflated absolute levels.

**Where A's recall edge comes from (v4):** BB, NOK, COHR, INTC-2025 — exactly the
**narrative / earnings-judgment** names a text-free keyword counter can't see —
now clear **at top-10** on the v4 harness (they were v3's top-20 adds). A's only
top-10 shortfalls are META and BILI, which arrive by top-20; A's *sole* structural
misses are **SNDK** and **AMD-2016**, both A-gate failures (post-spin <3y history;
already-rallied by the as-of date), not judgment errors.

**Where A's trap edge comes from:** A's *structural-decline* judgment avoids
**LUMN, PTON, FOSL** — the traps B's mechanical filter surfaced (B flags all three
in v4; A flags none). PTON is the clearest win: B rewarded its gross-margin bounce
off a negative trough; A reads "margin up **but revenue still −22% YoY and still
burning cash → not a real turn**." The A−B trap gap widens at top-20 (A 2/9 vs B
6/9): B additionally surfaces BBBY there, A does not.

**A's two residual flags are the intrinsically-hard cases the design predicted**
(ZM dead-money, INTC-fakestart — 2/9 at both cuts), not tuning failures:
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

## Post-cutoff holdout — the memorization confound, tested (v4: downgraded)

The single honest gap in the A-vs-B section is that the LLM **already knows** the
benchmark outcomes. So a holdout was run where the outcome is blind: **T =
2026-01-31** (after the model's Jan-2026 knowledge cutoff), a **fresh** universe of
16 depressed names with **zero overlap** with the benchmark or control arm, scored A
(LLM) and B from ≤T evidence, then measured the realized **T+5mo forward return**
(pinned at 2026-06-30: `FWD_MONTHS = 5` in `reports/run_holdout.py`, fully
deterministic — not "T → today"). Most names are obscure micro-caps with
near-zero priors, so this is about as blind as a free-data test gets.

> **v4 downgrade (read this first).** An independent methodology audit found the v3
> holdout claims **overstated**. The "cleared arm +125%" spread is carried by two
> names and evaporates under leave-two-out; one of the two "cleared" winners (LESL)
> sits **exactly on the trap ceiling** and only clears via an inclusive `≤`; and the
> run itself is **not reproducible** (no committed seed/script/≤T evidence) and
> **survivorship-filtered**. The corrected C1/C2 blocks below restate the result as
> **suggestive, not validated**. The regenerated `holdout_results.json` (median /
> leave-N-out / ceiling-boundary) is the source of truth for every number here.

| T+5mo forward return (T=2026-01-31, pinned end 2026-06-30) | result |
|---|---|
| **A top-5 by D** (CNS, TRIP, FIP, LEAT, FLUT) | mean **−0.6%** · median **+3.2%** |
| **B top-5 by D** (TRIP, FLUT, JBGS, SYRA, LEAT) | mean **+137%** · median **+3.2%** |
| Depressed-pool base rate (all 16) | mean **+83%** · median **0.0%** |
| **A trap-CLEARED** (10 names, trap ≤ 0.70) | mean **+141%** · **median +10.8%** |
| **A trap-FLAGGED** (6 names, trap > 0.70) | mean **−12.1%** · median −13.7% |

**v4 correction (C1) — the "cleared +141%" number does not survive contact with the
data.** These figures are recomputed from the regenerated `holdout_results.json`,
which now carries median / leave-N-out / ceiling-boundary fields; the v3 draft's
`+125% / −17% / +113% / +72%` were the earlier point estimates and are superseded
by the numbers above (the metric-layer rerun shifted them). Stated verbatim from
the JSON:

- **The cleared arm's mean is +141% but its median is +10.8%.** The mean is an
  artifact of two names: **SYRA (+697.5%)** and **LESL (+640.9%)**. Drop those two
  (`leave_two_out_mean`) and the cleared arm collapses to **+8.7%**; drop only the
  top one (`leave_one_out_mean`, SYRA) and it is **+78.9%**. A ten-name arm whose
  mean falls from +141% to +8.7% on removing two names is **carried entirely by two
  observations**.
- **LESL is a threshold-boundary artifact.** Its trap score is **0.70 = TRAP_CEILING
  exactly**, so it is "cleared" only because the gate is inclusive (`trap ≤ ceiling`).
  It is one of exactly two names sitting *on* the boundary — `ceiling_boundary =
  [LESL, WVVIP]`. Flip the gate to strict (`trap < ceiling`) and both move to
  flagged: the split goes to **cleared +97.6% vs flagged +69.3%** (median +10.8% vs
  −7.0%) — i.e. the mean spread nearly closes and rests on which side of 0.70 two
  names land. And had **LESL + SYRA** landed flagged, the split **inverts** to
  **cleared +8.7% vs flagged +158%** — the screen would look actively harmful.
- **Conclusion.** The blind trap-screen result is **two-name-fragile and
  threshold-boundary-dependent — suggestive, not validated.** The *median* cleared
  (+10.8%) vs flagged (−13.7%) spread is the more honest read of the signal, and
  even that rides on a 16-name, single-regime sample. (The flagged arm itself is
  the steadier half: 5 of 6 were flat-to-disastrous — JTAI −72.5%, SGLY −45.5%,
  AMST −27.3%, ALDA/ANKM ~0% — the lone exception GUTS +72.6%; "don't step on the
  dead shells" is where the residual out-of-sample signal actually lives.)
- **The fine-grained D *ranking* did not generalize either.** A's top-5 (mean
  −0.6%, median +3.2%) trailed both B's top-5 (mean +137%) and the pool (mean +83%);
  the biggest winners (SYRA, LESL, PVLA +99%) were ranked **low** by A (ranks 7, 6,
  10). But both engines' medians are ~+3%, and B's mean "win" is essentially the
  single SYRA +697.5% name — so neither *ranking* result is statistically meaningful
  at n = 5 over one 5-month **junk-rally** regime.

**C2 — reproducibility disclaimer (this holdout cannot be reproduced as run).**
The original 2026-01-31 holdout was **not** committed reproducibly:

- **No sampling script, seed, or source list was committed** for the 16-name draw,
  and the ≤T evidence file the scores were read from **is not in the repo** — so the
  as-of inputs cannot be regenerated.
- **Scores and results landed in the same commit**, so the claim that scoring
  preceded outcome measurement rests on **author attestation**, not on a
  commit-ordering artifact.
- **The pool is survivorship-filtered**: only names still resolving today could be
  drawn, which mechanically **inflates the +83% pool base rate** (the failures that
  delisted between T and today are invisible). The "cleared beats flagged" and "pool
  ripped" numbers all inherit this bias.
- **Requirement going forward:** future holdouts **must** use
  `reports/sample_holdout.py` — now committed, **seeded**, and **sha256-attested**
  over the drawn universe — so the sample, its provenance, and the ≤T cutoff are
  independently checkable. This run predates that tool and should be read as an
  **illustrative single-shot probe, not a validated holdout.**

## Measurement notes (disclosures)

Short list of measurement choices that bound how the numbers above should be read:

- **Price-only returns.** Forward returns are price-only; the control arm holds
  dividend-heavy names, so the control is **understated by ~1.6pp** vs a
  total-return basis. This makes the pick-vs-control spread **conservative** (the
  gap would narrow slightly, not widen, on total return).
- **"top-10 picks +78%" (v3) was a 5-name mean, not a basket.** The v3 headline was
  the mean of the **5 labeled positives that surfaced**, not a tradeable 10-name
  basket; **ex-NVDA the other 4 average +59.6%**. v4 reports n-labelled basket means
  (top-10 +69%, top-20 +82%) instead.
- **Control arm built once, at ref-date 2023-06-30.** The 65-name control is scored
  at a single reference date, so its **effective n is 53–65 by pick date** (names
  without reconstructable data at earlier as-of dates drop out). Using one late
  ref-date makes the control **conservative** (survivors, later window).
- **Engine-A scores are hand-authored frozen files.** A's comparison-mode scores are
  read from committed JSON (`reports/llm_scores.json`, `llm_holdout_scores.json`) —
  there is **no runtime LLM loop**; the harness ranks fixed author-attested scores
  against the live control arm. This is what makes A's rates a memorization upper
  bound, and why a live seeded holdout (C2) is the open item.

## The selectivity correction (v2 → v4)

The single most important v2 finding, updated for the v4 harness. v1 used a 30-name
control arm (median ~13 eligible/date), so "top-10" was barely selective and the
57% hit rate was **inflated**. The 65-name control arm fixed that; on the **v4
harness the median eligible field is 14/date** (the ADV haircut is what thins
the 65-name arm back down to ~14 eligible — see the v4 note), so "top-10" ≈
top-70% and "top-20" is essentially the whole field — read the **trap** row and
the **A−B gap**, not the hit-rate levels.

**Engine B alone, v4** (`backtest_results_v4_top{10,20}.json`; `old → new` =
v3 table → v4):

| Metric — engine B (control=65, median elig = 14) | top-10 | top-20 |
|---|---|---|
| **Hit rate** | **7/14 = 50%** (21% → 50%) | 11/14 = 79% (43% → 79%) |
| **Trap rate** *(lower=better)* | **5/9 = 56%** (44% → 56%) | 6/9 = 67% (56% → 67%) |
| Mean lead (hits) | ~4.9 months | ~5.1 months |
| **Fwd 12m, picks vs control** | **+69% vs +11%** (n=7) | +82% vs +10% (n=11) |
| Fwd 6m, picks vs control | +40% vs +13% | +51% vs +7% |
| `excluded_no_data` / `excluded_illiquid` | 2 (WBA×2) / **0** | 2 (WBA×2) / **0** |

**The honest read:** the D ranker does **not** reliably push the specific labeled
inflections into the absolute top-10 against the other depressed names — B captures
the strongest-signal ones (AXTI, BB, LITE, MU×2, NVDA, NFLX at top-10) and adds the
narrative/foreign names (NOK, META, COHR, BILI) only at top-20. BUT the names it
ranks at the top went on to **beat the depressed universe by ~58pp at 12 months**
(+69% vs +11% top-10). So D carries real economic signal at the top even though the
levels are inflated by the shallow cut. As a "the top of the ranking outperforms"
tool it works; the trap row (B 5/9 top-10, 6/9 top-20) is where it structurally
struggles — which is the whole reason engine A exists.

### Per-name (engine B, control=65, v4)

- **B top-10 hits:** AXTI, BB, LITE, MU (2023), MU (2016), NVDA, NFLX.
  **B top-20 adds:** NOK, META, COHR, BILI (narrative / foreign-filer names that
  need a lower selectivity bar to surface under code features).
- **Persistent misses:** SNDK (post-spin, A gate can't assess <3y history),
  AMD-2016 (already rallied → gate discipline), INTC-2025 (B ranks it below the
  cut).
- **Traps correctly avoided:** BBBY (top-10; enters B's top-20), LCID, FFAI, BLNK
  (cash-burn → caught by the runway filter).
- **Traps B still flags as turns:** LUMN, PTON (margin bounce off a COVID-writedown
  trough), FOSL, ZM (dead-money, flat+profitable), INTC-fakestart — the mechanical
  filter's structural blind spot, and exactly the set A clears (it flags only ZM +
  INTC). These are the genuinely hard cases (below).

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

1. **Control universe enlarged** (30→65) → the selectivity correction above.
   *Done.* (Median eligible/date is 14 on the v4 harness; sampling free tickers
   caps the count; 200+ needs a much larger random draw, noted.)
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
   overfit this tiny benchmark). **→ tested (v4 numbers).** A's full backtest holds
   the trap rate at **2/9 = 22%** at both cuts vs B's **56% / 67%** — A's
   structural-decline judgment clears LUMN/PTON/FOSL that B flags. See the A-vs-B
   section at the top.
5. **Paid point-in-time dataset — not done (blocked by the free-data decision).**
   This would lift the probe to a generalizable accuracy estimate and revive the
   estimate-revision signal, but it costs money and needs a data subscription /
   credentials. Left for the user to decide.

## Remaining honest limitations

- **Shallow cut on a small field.** With median eligible = 14/date the hit-rate
  levels are weakly selective; the informative signals are the **trap row** and the
  **A−B gap**, not the top-10/20 hit levels. B's top-10 recall (50%) and A's (71%)
  both benefit from the easy cut.
- **Hard traps persist:** PTON (margin bounce off a catastrophic trough reads as a
  turn), ZM (cheap+profitable+flat = "dead money"), INTC-fakestart (depressed +
  rich AI/foundry narrative — indistinguishable from a real turn in 2022–24
  except in hindsight). These are intrinsic, not tuning failures — and are the two
  A itself still flags.
- **Holdout is a single-shot probe, not a validated result** (C1/C2): two-name-
  fragile spread, ceiling-boundary dependence, non-reproducible + survivorship-
  filtered. A larger seeded multi-regime holdout is the open item.
- **ADV haircut: load-bearing on the levels via the control denominator, not
  via exclusions.** It excluded 0 labeled rows (its only labeled-name firings
  are AXTI's intermediate scans), but it halves the eligible control field
  (median ~28 → 14; 2024-06-30: 27 → 13, 0 None-drops) and thereby produces
  the ~30pp-inflated absolute hit levels — read the A−B gap, not the levels.
- **Foreign-filer quarterly gap** (NOK/BILI), **post-spin gating** (SNDK),
  **small-n / regime-noisy forward return** — unchanged from v1.

## Verdict & next steps

The mechanism's **point-in-time machinery is sound** — the 5-canary battery is
green against live yfinance/EDGAR as of 2026-07-07, with `recycled_ticker`
passing at BBBY 12m fwd = **−1.0**. Dead names are realized via the **curated
dead-ticker registry** (`pit/dead_tickers.py`): yfinance re-anchors recycled
tickers to the live successor and drops the dead leg entirely (verified on
BBBY/HTZ/SPCE/SHLD), so series-shape detection alone cannot realize those
losses; **identity-break truncation** (>30-day gap, or a sub-$1 close jumping
>8× in one session), scoped to the identity segment containing T, is retained
as defense-in-depth — and already earned its keep: the v4.1 regeneration
purged 25 stitched-artifact control values from 5 of 65 control names, worst
case +14,900% inside a pick-date control mean (see the v4.1 note). And the
**top-ranked picks outperform the depressed universe at 12 months** (+69% vs
+10% control at top-10). Engine B alone **cannot solve the value-trap
problem with free numeric signals** (trap rate 5/9 top-10, 6/9 top-20).

**The A-vs-B loop (v4):** Implementation A (LLM), on the identical harness and
control arm, **delivers exactly the discrimination B structurally cannot** — the
A−B **trap gap** is −34pp at top-10 (22% vs 56%) and −44pp at top-20 (22% vs 67%),
with a matching recall edge (top-10 71% vs 50%). A's gains are concentrated where
the design predicted (narrative recall: BB/NOK/COHR/INTC-2025; structural traps:
LUMN/PTON/FOSL cleared), and A's only residual flags are the two intrinsically
ambiguous cases (ZM dead-money, INTC fake-start). So the architecture's core thesis
— **a code engine for cheap, leak-free breadth; an LLM engine for the qualitative
judgment the numbers can't encode** — is empirically supported as an *engine
ordering*. (The v4 harness lifts both engines' absolute levels vs the v3 table; the
ordering, not the level, is the result. A's rates remain a memorization upper
bound.)

**The memorization confound was tested (holdout) — and the v4 audit downgrades it.**
Blind, the trap-screen *looks* like it separates (+141% cleared vs −12% flagged),
but that mean is **two-name-fragile** (leave-two-out → +8.7%) and
**threshold-boundary-dependent** (LESL sits on the 0.70 ceiling; strict `<` nearly
closes the spread), and the run is **non-reproducible + survivorship-filtered**. The
honest read is the **median** cleared +10.8% vs flagged −13.7% — **suggestive, not
validated** — and the *ranking* edge did not reproduce at all (A top-5 mean −0.6% vs
B +137% vs pool +83%, junk-rally, n = 5). The durable, generalizing claim is the
qualitative *"real business vs trap"* screen; even that needs a bigger sample.

**What remains:** a **larger, seeded, multi-regime holdout** — via the now-committed
`reports/sample_holdout.py` (seeded, sha256-attested) — is the only way to settle
both whether A's ranking adds alpha and whether the trap screen survives outside one
risk-on window; a one-time paid point-in-time dataset (user decision) would let the
labeled hit/trap backtest itself run on post-cutoff data rather than a probe.
