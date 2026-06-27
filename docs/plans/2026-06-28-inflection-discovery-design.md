# Inflection Discovery Mechanism Design

> **Revision v2 (2026-06-28)** — Revised after an independent design review. The conceptual design (the `A ∧ (B ∨ C) ∧ ¬trap` conjunction, dual engine, depressed-base hard gate) survived; the **backtest-validity** sections were reworked because the v1 free-data point-in-time claims would have silently leaked look-ahead and survivorship. Key changes: explicit point-in-time reconstruction components for prices / fundamentals / universe; a leak-specific canary battery; a fundamentals-only `T*` definition; a controlled A-vs-B comparison mode; and an honest reframing of the benchmark as a **discrimination smoke-test, not a generalizable accuracy number**.
>
> **Revision v2.1 (2026-06-28)** — Re-review pass. Corrected the `pit_fundamentals` selector to "latest `filed` ≤ T" (a restatement filed *before* T was the truth at T) and split out `pit_filing_text` because `companyfacts` covers only numeric facts (the dimension-C text engine and backlog/book-to-bill need separate as-filed document parsing). Gave narrative-primary `T*` (BB) an independent, non-price definition; resolved the seasonal-adjustment vs short-history conflict (SNDK); scoped the random control arm to forward-return only (trap rate stays on labeled negatives); fixed the hit-date definition (−3m) and the comparison-mode limitation caveat.

## Goal

Build a discovery mechanism that surfaces companies at an **earnings or narrative inflection** — names with depressed expectations whose fundamentals or story have started to turn — and routes the best candidates into `analyzing-stocks` for a full work-up.

The motivating set of names is AXTI, BB, NOK, LITE, MU, SNDK: beaten-down companies whose earnings cycle bottomed or whose strategic narrative re-rated, caught before consensus fully repriced them.

This is a new **upstream stage** for the framework. Today `analyzing-stocks` only analyzes a *known* ticker (industry routing → valuation → sizing). It has no discovery / idea-generation front-end. This mechanism produces the candidate tickers that feed it.

## Core Thesis

A name is at an inflection when this conjunction holds:

```
A  ∧  (B ∨ C)  ∧  ¬trap        ranked by D
```

- **A — Depressed base / low expectations** (necessary precondition). Without A, surfacing a name is just momentum-chasing (too late).
- **B — Earnings second derivative turning up** (quantitative engine).
- **C — Narrative re-rating** (text engine).
- **¬trap — Not a value trap / head-fake** (survivable balance sheet, real catalyst, cyclical dip rather than secular decline).
- **D — Expectations gap + timing** (the ranker): how far price/consensus still lag the confirmed turn.

The conjunction is the edge. It deliberately rejects the two classic failure modes:

- **A without B/C → value trap** (cheap and hated, but nothing is turning).
- **B/C without A → momentum chase** (already turned and loved; no margin of safety).

**A is a hard gate** (decided). The mechanism targets *depressed → inflection* turnarounds only. Pure earnings-acceleration in names that were never cheap or hated (e.g., CRDO, NBIS) is **out of scope for v1**; it overlaps with generic momentum/growth screeners and dilutes the "catch it while hated" edge. A growth-acceleration sibling can be added later (see Future Work).

## What the Backtest Can and Cannot Prove (read this before trusting any number)

This is decided scope, surfaced by review: on **free data**, a rigorous point-in-time backtest of fundamental signals is achievable for *prices* and *as-filed EDGAR fundamentals*, but the labeled benchmark is small and selection-biased. Therefore:

- The benchmark is a **discrimination smoke-test / probe**, not a source of generalizable accuracy. With ~14 positives, a hit-rate has a ~±25-point 95% confidence interval; it cannot distinguish a 60%-from-80% mechanism, and it cannot definitively rank A vs B.
- Every reported metric is published **with its n and a confidence interval**, and alongside an **unbiased random control arm** (see Metrics).
- We do **not** claim "X% accurate." We claim directional discrimination: does the mechanism separate the curated inflections from the curated traps and from random depressed names, with what lead time, without leaking look-ahead.
- A paid point-in-time dataset (to get generalizable accuracy and the estimate-revision line) is documented as Future Work, explicitly out of v1.

## Scope and Non-Goals

**In scope (v1):** US common stocks; quarterly cadence; free data only (yfinance prices, Finviz screening snapshots, SEC EDGAR filings + `companyfacts`); two implementations (A and B) over one shared core; point-in-time backtest scoped to backtest-active signals.

**Out of scope (v1):** paid data; real-time/intraday alerts; automated trading; non-US listings; historical analyst estimate-revision signals **inside the backtest** (free sources lack point-in-time history — live-only in A, not scored in the backtest); the growth-acceleration sibling.

## Architecture

Three layers. The funnel (Universe → depressed-base filter → dual-engine scorecard → ranked candidates → route) is conceptually identical across both implementations; they differ only in how the funnel's first stages are executed.

### Layer 1 — Shared Core (built once on the base branch, used by both worktrees)

The single source of truth that makes A and B comparable:

1. **Inflection taxonomy** — the scorecard definition (A/B/C/D dimensions, sub-signals, free-data source per signal, point-in-time reconstruction method, **numerically specified** percentile thresholds). Documentation, not code.
2. **Point-in-time reconstruction components** (named functions, shared so A and B reconstruct identically):
   - `pit_prices(ticker, T)` — pull yfinance with `auto_adjust=False` plus the raw splits/dividends action series, then re-derive the as-of-T adjusted series using **only** corporate actions with ex-date ≤ T. Never use today's adjustment factors. This feeds dimension A's hard gate, so it must be exact.
   - `pit_fundamentals(ticker, T)` — numeric financials only, from SEC `companyfacts`. For each `(concept, period)` keep the observation with the **latest `filed` date ≤ T** — an amendment or restatement filed *before* T was the public truth at T, so it is used; discard any observation with `filed` > T. `companyfacts` stores each reported value as a separate observation carrying its own `accn`/`form`/`filed`, which is what makes this point-in-time. yfinance fundamentals (`.financials`, `.quarterly_financials`, `.balance_sheet`) are **forbidden in the backtest** — restated and undated. A concept-mapping layer handles XBRL tag drift across companies/years (e.g., `Revenues` vs `RevenueFromContractWithCustomerExcludingAssessedTax` vs custom extensions) and carries its own tests.
   - `pit_filing_text(ticker, T)` — as-filed **document** text (10-K/10-Q/8-K) for the dimension-C narrative engine and for the text-only B signals (backlog, book-to-bill), which are **not** in `companyfacts`. Use the EDGAR `submissions` API to list filings, fetch each document by accession with `filed` ≤ T, and parse point-in-time. This is a genuinely hard shared-core component: `companyfacts` discharges only the *numeric* half of extraction; this discharges the *text* half. (Early-XBRL coverage is thin pre-~2012, so the minimum-history fallback must also cover tagging gaps, not just short history.)
   - `pit_universe(T)` — the investable universe **as of T**, including names that later delisted. A symbol list compiled today omits exactly the completed value traps the gate must reject. Use historical EDGAR filer lists / archived listing snapshots; where a name's point-in-time series cannot be reconstructed, mark the row `excluded-no-data` and **count it** rather than silently dropping it.
3. **Candidate contract** — the normalized record every candidate emits (see Candidate Contract). JSON schema with a validator.
4. **Benchmark dataset** — labeled `(ticker, as-of-date, label)` rows (see Benchmark).
5. **Backtest harness** — point-in-time evaluation engine + metrics + the **canary battery** + the random control arm.
6. **Routing adapter** — emits a candidate plus its inflection thesis as the scope hand-off to `analyzing-stocks`, pre-filling the controller's required Step-1/Step-2 fields.
7. **¬trap diagnostics** — reuse the value-trap diagnostics already documented in `references/value-investing-lens.md` rather than reinventing them; align filing-lag handling with `references/source-policy.md`.

### Layer 2 — Implementation A: skill + thin scripts (LLM judgment), two modes

A new skill `discovering-inflections`, sibling to `analyzing-stocks`.

- **Stage 1 (broad pre-screen):** a thin script queries Finviz / yfinance for a depressed-base universe (52-week-low proximity, low valuation percentile, high short interest, beaten-down 1–2y) → longlist (~50–150).
- **Stage 2 (dual-engine scorecard, LLM):** the model scores each longlist name. Earnings engine reads the latest 10-Q / financials for sequential acceleration, margin and inventory inflection. Narrative engine reads filings, calls, and news for language shift, pivot, and catalyst. Fills the candidate contract.
- **Stage 3 (route):** rank by D, route top N → `analyzing-stocks`.

Because A is LLM-driven, it runs in **two distinct modes** so its comparison to B is controlled:

- **Comparison mode** — A is fed the **same frozen, EDGAR-only corpus at the same as-of T** that B uses, under the same backtest harness: no open web, no live estimate snapshots. This is the only mode whose numbers are tabled against B, so the C-dimension experiment varies *only* the engine (LLM reading vs code text-features), not the information set.
- **Live mode** — A reads the open web (news, transcripts, live estimates). This is the production discovery mode; its numbers are reported **separately and never tabled against B**.

**Memorization caveat:** an LLM has seen the post-T outcome of every famous benchmark name, so A's benchmark hit-rate is a memorization-contaminated **upper bound**. It is labeled as such, and A is additionally evaluated on a post-training-cutoff out-of-sample holdout (see Benchmark) where memorization cannot help.

### Layer 3 — Implementation B: code-first scoring pipeline (rigor, backtestable)

- A Python package.
- **Universe:** `pit_universe(T)` (not a current static list).
- **Inflection Score:** computed only from backtest-active, point-in-time-safe signals — `pit_prices` (price/volume) and `pit_fundamentals` (sequential revenue/EPS acceleration, gross-margin delta, inventory-days delta). The narrative dimension (C) is a lightweight text-feature pass over as-filed EDGAR text (keyword and tone deltas), point-in-time via filing date. No historical estimate-revision line.
- **Output:** ranked universe, persisted, fully backtestable on the benchmark.

## The Inflection Scorecard (shared IP)

All thresholds are **percentile-based** and specified numerically in the shared taxonomy so A and B compute them identically. Each percentile is point-in-time: it uses only data ≤ T. The taxonomy fixes, per signal: the **history window** (default 5y trailing, ≤ T), the **peer set** (point-in-time industry peers from the controller's routing, with delisted peers retained), and a **minimum-history fallback** (for post-spin/recently-troubled names with < 8 quarters, fall back to peer-relative-only and flag lower confidence).

Each signal row is tagged **backtest-active** or **live-only**. The backtested scorecard is the strict subset of backtest-active signals; "measured discrimination" is scoped to that subset.

### A — Depressed base (hard gate)

| Signal | Source | Point-in-time | Tag |
| --- | --- | --- | --- |
| Price near multi-year low / large drawdown from highs | `pit_prices` | actions ex-date ≤ T only | backtest-active |
| Valuation at trough percentile (EV/S, P/B, EV/EBITDA) vs own history & peers | `pit_fundamentals` + `pit_prices` | filed ≤ T | backtest-active |
| Elevated short interest; low/falling coverage/ratings | Finviz live | no PIT history free | live-only |

Gate rule: a name must clear the minimum depressed-base percentile (set in taxonomy) to proceed. Fail A → excluded regardless of B/C.

### B — Earnings second derivative turning up (quantitative engine)

| Signal | Source | Point-in-time | Tag |
| --- | --- | --- | --- |
| Sequential revenue/EPS acceleration, **seasonally adjusted** (YoY-of-sequential, or seasonal-dummy), even if YoY still negative | `pit_fundamentals` | filed ≤ T (latest) | backtest-active |
| Gross / operating margin troughing and ticking up | `pit_fundamentals` | filed ≤ T | backtest-active |
| Inventory days falling / destocking ending | `pit_fundamentals` | filed ≤ T | backtest-active |
| Backlog / book-to-bill where disclosed | as-filed EDGAR text | filed ≤ T | backtest-active |
| Estimate revisions turning up | Finviz/live | no PIT history free | live-only (not scored) |

Raw QoQ is seasonally dangerous (Q4→Q1 down for many names regardless of any turn); the signal is most valid for the semis/cyclicals in the motivating set and is explicitly seasonally adjusted. For names with too little point-in-time history to seasonally adjust (< ~5 quarters, e.g., post-spin SNDK), the seasonal-sequential B signal is **suppressed** and the name leans on peer-relative valuation + dimension C, flagged lower-confidence — the short-history fallback wins over the seasonal-adjustment mandate.

### C — Narrative re-rating (text engine)

| Signal | Source | Point-in-time | Tag |
| --- | --- | --- | --- |
| Language shift in latest 10-K/10-Q/8-K and earnings call (new TAM, segment, design win, "AI/datacenter", strategic review) | as-filed EDGAR text (+ transcripts/news in A live mode) | filed ≤ T | backtest-active (EDGAR text); live-only (news/transcripts) |
| Management / strategy change (new CEO/CFO, restructuring, spinoff, capital-return start) | EDGAR 8-K | filed ≤ T | backtest-active |
| Catalyst proximity (launch, contract, regulatory, spinoff completion) | filings (+ news in A live) | dated ≤ T | mixed |
| Sell-side re-initiation / 13F additions | EDGAR 13F (+ news in A live) | filed ≤ T | backtest-active (13F); live-only (sell-side) |

In Implementation B, C is approximated by keyword/tone deltas over as-filed EDGAR text. In Implementation A comparison mode, C is LLM reading of the **same** EDGAR corpus. The A-vs-B comparison on C therefore isolates the engine.

### ¬trap — Trap / head-fake filter

Reuse the value-trap diagnostics in `references/value-investing-lens.md`. Core checks: balance-sheet runway and dilution risk (cash, debt maturities, share-count trend); secular decline vs cyclical dip; durability of the sequential turn across ≥ 1 quarter of confirmed follow-through (a fixed rule, not "where data allows").

### D — Expectations gap and timing (ranker)

- Size of the gap between price/consensus and the confirmed turn (bigger gap + confirmed turn = better setup).
- Has the market begun to notice (volume, price reclaiming key moving averages) without fully repricing?

Note: price-reclaim signals live here **only as scoring inputs**; they are deliberately kept out of the `T*` evaluation anchor (see Backtest) to avoid circularity.

## Candidate Contract

```json
{
  "ticker": "AXTI",
  "as_of_date": "2024-06-30",
  "passes_A_gate": true,
  "scores": { "A": 0.0, "B": 0.0, "C": 0.0, "trap_risk": 0.0, "D": 0.0 },
  "composite": 0.0,
  "rank": 0,
  "engine": "A | B",
  "evidence": { "A": ["..."], "B": ["..."], "C": ["..."], "trap_risk": ["..."] },
  "routing": { "exchange": "NASDAQ", "currency": "USD", "tradable_line": "AXTI", "suggested_style": "turnaround" },
  "thesis": "one-paragraph inflection thesis for the analyzing-stocks hand-off"
}
```

- `scores` are 0–1, percentile-derived. Key names are consistent (`trap_risk`) across schema, evidence, and validator.
- **`composite` and ranking:** `composite` is a documented, fixed function of the sub-scores used for transparency; **top-N membership is determined by `rank`, which is ordered by D** (gated by `passes_A_gate` and a `trap_risk` ceiling). The taxonomy states the composite formula and confirms D is the sort key, so "what enters top-N" is unambiguous (it drives every metric).
- `routing` pre-fills the controller's required Step-1/Step-2 fields (exchange, currency, the actual tradable line per the controller's listing-line rule, and `suggested_style` = `turnaround`/`special situation`, which by construction every candidate is) so the hand-off drops no context.
- `evidence` strings cite their source (filing accession, price fact, news item) so a human and the backtest can audit the call.

## Backtest Harness and Metrics

The harness answers one question per labeled name: **"rewind the clock — would the mechanism have surfaced this before it moved?"**

**`T*` is defined from fundamentals only** — the first reported quarter (by filing date) of confirmed sequential acceleration. Price is **removed from the `T*` definition** so the evaluation anchor is independent of dimension D's price-reclaim scoring input (v1 used a 200dma reclaim in `T*`, which was circular and inflated lead time via the trailing average's lag). For narrative-primary names (e.g., BB), which have no clean sequential-acceleration quarter, `T*` is the **filing/announcement date of the catalyst document itself** (the 8-K, or a press release filed as an 8-K exhibit) — never the market's price reaction to it, so the narrative path avoids the same circularity just removed from the earnings path. Lead time may additionally be reported against an independent market anchor (first close above the 200dma) shown separately, never blended.

For each positive, run the mechanism as-of **`T*` − 1, 3, 6 months**, feeding only data knowable at that date via the Layer-1 PIT components.

### Metrics (each reported with n and a 95% confidence interval)

- **Hit rate** — positives surfaced into top-N (default **N = 20**). Counting rule is **symmetric** with trap rate: a positive is a hit if surfaced at the **fixed −3-month as-of date** (the canonical lead requirement); a negative is a trap if surfaced at **any** of the tested as-of dates (conservative pairing). Lead time (below) is still measured as the *earliest* of {−6, −3, −1} at which the name entered top-N.
- **Lead time** — for a hit, `T*` minus the earliest as-of date at which it entered top-N (fundamental-`T*`).
- **Trap rate** — negatives surfaced into top-N ÷ negatives **with reconstructable data** (the `excluded-no-data` count is reported beside it so survivorship can't silently flatter it).
- **Forward return** — 6- and 12-month forward return of the top-N basket at each as-of date vs the universe average. **Dead-name handling:** a name that delists/goes to zero in the window contributes its realized loss (down to −100%), never silently drops. A **liquidity haircut / minimum-ADV filter** is applied so microcap "paper" returns (AXTI, FFAI, BLNK, FOSL) are not counted as costlessly investable.
- **Random control arm** — at each as-of date, also score a random sample of depressed-base names **not** in the curated benchmark. These are **unlabeled**, so they feed **forward-return and base-rate context only** (basket-vs-universe needs no labels); **trap rate stays on the labeled negatives** (a random depressed name that quietly turns must not be mis-counted as a trap).

Hit rate + lead time measure precision and earliness; trap rate measures discipline; forward return is the economic test; the control arm keeps the denominators honest. All read together — high hit rate **with** high trap rate is a "flags every cheap stock" failure.

### Point-in-time discipline — canary battery

A single self-designed injected-value canary only tests the harness tripwire, not the real leaks (which are implicit in the data the sources hand you). The harness ships a **battery**, each targeting a real mechanism:

- **Split/adjustment canary** — assert an as-of-T price series is identical whether built before or after a known post-T split (catches yfinance back-adjustment).
- **Survivorship canary** — assert a known-delisted ticker present in `pit_universe(T)` is not silently absent from the reconstructed universe.
- **Filing-lag canary** — assert a 10-Q with `period_end ≤ T < filed` is excluded, and that a later `/A` amendment is not substituted for the originally-filed values.
- **Injected-value sanity** — the original forward-value injection, kept as a harness self-check.

No accuracy number is trusted until the battery passes.

## Benchmark Dataset

Label unit is **`(ticker, as-of-date, label)`** — the same ticker can carry opposite labels at different dates. INTC is the canonical illustration: cheap-and-hated with repeated fake starts in 2022–2024 (negative), then a real turn in 2025 (positive). It is illustrative of the design, **not** load-bearing — no conclusion rests on a single ticker's path.

The benchmark is a **discrimination probe** (see "What the Backtest Can and Cannot Prove"), not a generalizable accuracy source. It deliberately includes **hard cases**, not only famous winners/failures:

- **Hard negatives** — depressed-base names that *passed the gate and showed an early head-fake uptick* that then rolled over (the genuinely discriminating cases). INTC-2022/2024 is one; at least 3–4 more are sourced during construction.
- **Borderline A-gate cases** — a name sitting near the depressed-base percentile threshold, to test that the gate's cutoff lands it correctly. (This replaces relying on CRDO/NBIS as gate "controls": since they fail the gate by construction, "they never appear" is a tautology that tests plumbing, not judgment. They are kept only as plumbing checks.)
- **Out-of-sample holdout** — a few names whose inflection postdates the LLM training cutoff, to evaluate A free of memorization.

`T*` dates below are **initial anchors**, pinned precisely during construction using the fundamentals-only `T*` rule.

### Positives (depressed → confirmed inflection)

| Ticker | T\* anchor | Inflection type |
| --- | --- | --- |
| AXTI | 2024 | earnings (InP / datacenter pull) |
| BB | ~2021 | narrative-primary (cyber/IoT/QNX pivot) — weak earnings confirmation; tests the C engine |
| NOK | 2024–2025 | narrative + earnings (AI networking, new CEO) |
| LITE | 2024-H1 | earnings (AI datacom recovery) |
| MU | 2016-H2 | earnings (memory cycle bottom) |
| MU | 2023-H2 | earnings (HBM / AI upcycle) |
| SNDK | 2025 | earnings + special situation (NAND spin from WDC) — pre-spin history lives inside WDC filings; PIT series effectively starts at the Feb-2025 spin, so its lead-time test is mechanically capped (special-case reconstruction) |
| AMD | 2016-H2 | earnings turnaround (Zen ramp) |
| NVDA | 2019-H1 | earnings (post-crypto-bust recovery) |
| META | 2022-Q4 | earnings + narrative ("year of efficiency") |
| NFLX | 2022-Q3 | earnings (post subscriber scare) |
| COHR | 2024-H1 | earnings (AI datacom + deleveraging) |
| BILI | 2024-Q3 | earnings + narrative (first non-GAAP profit; gaming) |
| INTC | 2025-H1 | earnings (real turn under new CEO) |

AMAT is excluded by default (cyclical, mild drawdowns, never "left for dead"). Noted tension: excluding ambiguous cases for "purity" is itself a selection bias — the hard-negatives and random control arm exist to offset it.

### Negatives (cheap/hated but no real turn, or trap)

| Ticker | As-of window | Why negative |
| --- | --- | --- |
| BBBY | 2022 | value trap → bankruptcy (delisted — exercises the survivorship canary) |
| LUMN | 2022–2023 | cheap telecom, kept sinking |
| PTON | 2022–2023 | post-COVID collapse, recurring narrative hype |
| FOSL | 2019–2023 | perennially cheap, no turn |
| WBA | 2023–2024 | cheap, kept declining |
| LCID | 2022–2024 | EV cash burn, chronic dilution |
| FFAI | 2022–2024 | story-stock SPAC, serial diluter (ticker/reverse-split history — survivorship canary) |
| BLNK | 2022–2024 | EV-charging cash burn, serial diluter |
| ZM | 2023–2024 | dead-money control: cheap and profitable but second derivative never turned |
| INTC | 2022–2024 (multiple) | cheap and hated, repeated fake starts (a hard negative) |

### Plumbing-only controls (fail the A gate by construction)

CRDO (2024), NBIS (2025) — never depressed; used only to confirm the gate excludes loved growth names. They cannot fail unless the code is broken, so they validate plumbing, not judgment.

## Comparison Protocol (A vs B)

Both implementations emit candidate contracts on the same as-of dates over the same benchmark, scored on the same metrics. **Only A's comparison mode** (frozen EDGAR-only corpus, same harness) is tabled against B, so the headline C-dimension result varies only the engine. A's live mode and A's memorization-caveat upper-bound are reported separately. Outputs:

- Head-to-head table (comparison-mode A vs B): hit rate, mean lead time, trap rate, forward return — each with n and CI, and against the random control arm.
- Per-dimension insight, especially C (LLM reading vs code text-features) on the identical corpus.
- **Stated limitation (symmetric to the memorization caveat):** comparison-mode A is deliberately hobbled (EDGAR-only, no news/transcripts), so the head-to-head **understates live-A's real-world C performance**. The table's conclusion is scoped to "LLM vs code *on identical EDGAR text*," not "LLM vs code." Live mode is never tabled against B.
- Optional ensemble (intersection / union / score blend) and whether it beats either alone.

## Build Sequence and Worktrees

1. Build the **Shared Core** on the base branch first: taxonomy doc, the three PIT reconstruction components (`pit_prices`, `pit_fundamentals`, `pit_universe`) with their canaries, candidate-contract schema + validator, benchmark CSV, harness + metrics + control arm, routing adapter. Commit. The genuinely load-bearing shared artifacts are the **contract schema, the benchmark, and the PIT reconstruction components** — get these frozen before forking.
2. Fork two worktrees from that base: `feat/inflection-A` and `feat/inflection-B`.
3. Implement A and B in parallel, each plugging into the shared harness via the candidate contract.
4. Run both on the benchmark and produce the comparison.

## Testing Strategy

- **Unit:** PIT reconstruction (assert each component uses only inputs ≤ T), scorecard scoring, contract-schema validation.
- **Canary battery:** split/adjustment, survivorship, filing-lag, injected-value — all must pass before any metric is trusted.
- **Integration:** the benchmark backtest itself is the integration test for each implementation.

## Future Work (post-v1)

- A one-time paid point-in-time estimate/valuation history (Sharadar / FMP) to backtest the estimate-revision line and produce **generalizable** accuracy rather than a discrimination probe.
- A growth-acceleration sibling that relaxes the A gate to catch loved hypergrowth earnings inflections (CRDO/NBIS-type), kept separate so the turnaround edge stays clean.
- Real-time / alert cadence; non-US universe.
