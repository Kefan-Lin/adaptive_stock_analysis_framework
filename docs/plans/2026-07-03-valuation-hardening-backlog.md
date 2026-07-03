# Valuation Reliability Hardening Backlog

Date: 2026-07-03
Status: Backlog — execute after the decision-records implementation
(`2026-07-03-decision-records-design.md`)

## Context

Produced by a full methodology review of the valuation chain (controller,
decision workflow, valuation-router, valuation-scenarios, value-investing-lens,
financial-diagnostics, source-policy, macro-overlay, report-template,
risk-register).

Review verdict, in one line: **the discipline layer is strong; the
point-estimate layer is structurally unreliable.** What can be trusted: stance
direction, the eight-bucket risk sweep, value-trap screening, valuation-family
routing, market-implied-expectations sanity checks. What cannot: the precision
of `Weighted Fair Value`, margin-of-safety percentages, and scenario
probabilities — these are produced with no calibration mechanism, no input
redundancy, and unmeasured run-to-run variance.

Empirical anchor: the inflection-discovery post-cutoff holdout (branch
`claude/compassionate-thompson-93ff22`, `reports/`) showed LLM **qualitative
business-vs-trap judgment generalized out of sample while precise ranking did
not**. This backlog strengthens exactly the layer where the evidence is
weakest.

Relation to `2026-04-22-skill-hardening-plan.md`: its three tasks (sector-safe
controller contract, routing boundaries, global source policy + executable
sizing) are implemented in the current files and covered by contract tests.
This backlog is the next layer: execution reliability and valuation-input
discipline.

Sequencing: run after P0 (decision records) so that P2 outcome scoring can
later **measure** whether these fixes improve calibration instead of asserting
it.

## Findings Register

Execution-layer findings (dominant reliability risk — the method runs on an
LLM over live-searched data):

| # | Finding | Severity | Where |
| --- | --- | --- | --- |
| E1 | False precision: scenario probabilities and WFV have no calibration mechanism, yet MoS bands (≥25%/10%) consume the point estimate for sizing | High | `valuation-scenarios.md` §4–5, `value-investing-lens.md` §5 |
| E2 | Single-pass data layer: no second-source cross-check for share count / net debt / earnings base; no arithmetic re-check on the ordinary path (only `debating-stocks` has a fact-checker, and it is optional) | High | `source-policy.md`, controller Step 5 |
| E3 | Run-to-run variance unmeasured: same name, same day can produce different WFV/stance; long skills risk perfunctory gate-filling; self-red-teaming is weakly adversarial | High | controller, `report-template.md` §9.0 |
| E4 | No user-view isolation: a directional prompt ("this looks like a golden pit") biases scenario construction; confirmation-bias check is self-policed | Medium | controller Step 1 |

Methodology-layer findings:

| # | Finding | Severity | Where |
| --- | --- | --- | --- |
| M5 | No baseline WACC construction rule (risk-free anchor, ERP source, risk adders); macro regime adjustments are relative to an undefined baseline and can act pro-cyclically with no floor | High | `value-investing-lens.md` §3, `macro-overlay.md` §1 |
| M6 | Terminal-value dominance rule has no numeric guardrail | Medium | `value-investing-lens.md` §3 |
| M7 | Bear scenarios lack a plausibility benchmark (e.g. worst historical KPI drawdown); generic −10%/−20% stress is too mild for cyclicals | Medium | `valuation-scenarios.md` §1, `financial-diagnostics.md` §2 |
| M8 | Probability elicitation has no rules: no default prior, no base rates, no anti-optimism constraint | Medium | `valuation-scenarios.md` §1 |
| M9 | Moat score → valuation assumption linkage is soft: weak moat does not force excess-return fade in terminal assumptions | Medium | `valuation-scenarios.md`, `business-moat.md` |
| M10 | No mandatory cross-sectional reconciliation: a valuation can pass all gates while implying an unexplained premium to the entire live peer set | Medium | `valuation-scenarios.md` §8 |

## Execution Rules

- Execute one task at a time.
- For each task: add or update contract tests first, implement the skill/reference
  edits, run verification, review the diff, then commit.
- Do not batch multiple tasks into one commit. Avoid unrelated cleanup.
- Every rule added must be checkable by the existing string-level contract-test
  style (`tests/test_skill_contracts.py`).

## Task 1: Arithmetic & Input Verification Pass (E2, part of E3)

### Objective

The ordinary path gets a mandatory, cheap audit step — no report finalizes
without it. This is the single highest-leverage fix: wrong share count or net
debt corrupts every downstream number.

### Files

- Modify: `skills/analyzing-stocks/SKILL.md` (new step between Step 6 and 7)
- Modify: `skills/analyzing-stocks/references/source-policy.md`
- Modify: `skills/analyzing-stocks/references/report-template.md` (§10.4)
- Create/extend: contract tests

### Required outcomes

- Diluted share count, net debt/cash, and the valuation earnings/cash-flow base
  must each be confirmed by two independent sources (or one filing-direct
  citation); a discrepancy is stated and lowers confidence one band.
- WFV and margin-of-safety arithmetic is recomputed and shown as an explicit
  math line (`sum(prob × value)`), not asserted.
- Dual-listed / ADR names get a currency-and-line reconciliation assertion
  before the target range is stated.
- §10.4 evidence ledger gains a compact verification block (item / sources /
  pass-fail) so skipping the step is visible.

### Verification gate

- New contract tests pass; full unittest suite and `validate_repo.py --profile
  full` pass.

## Task 2: Valuation Input Discipline (M5, M6, M7, M8)

### Objective

Bound the free parameters that dominate value: discount rate, terminal value,
scenario probabilities, bear depth.

### Files

- Modify: `skills/analyzing-stocks/references/valuation-scenarios.md`
- Modify: `skills/analyzing-stocks/references/value-investing-lens.md`
- Modify: `skills/analyzing-stocks/references/macro-overlay.md`
- Modify: `skills/analyzing-stocks/references/report-template.md` (§7.1)
- Create/extend: contract tests

### Required outcomes

- WACC construction rule: explicit build — current 10Y risk-free of the pricing
  currency + stated ERP source + business/leverage adders — with a hard floor
  (suggested default: risk-free + 300 bps minimum for equities; exact number
  adjustable at implementation). Macro-overlay regime adjustments apply on top
  and may not breach the floor.
- Terminal-value flag: if terminal value exceeds ~75% of total PV, a terminal
  sensitivity is mandatory and confidence caps at `Medium` unless
  contracted-visibility evidence (structural re-rating gate) says otherwise.
- Probability prior: default 25/50/25; deviations beyond ±15 pp require stated
  evidence; the Bull scenario may not silently carry the thesis via a
  probability shift.
- Bear plausibility benchmark: compare the Bear KPI path against the name's (or
  industry's) worst historical drawdown; a milder Bear must be justified in one
  line.
- §7.1 assumption table gains: discount-rate build one-liner, TV share of PV,
  probability rationale line.

### Verification gate

- Contract tests for each rule's presence pass; suite and validator pass.

## Task 3: Cross-Sectional Reconciliation (M10, M9)

### Objective

No valuation finalizes without live peer context and a moat-consistent terminal
assumption.

### Files

- Modify: `skills/analyzing-stocks/references/valuation-scenarios.md` (§8 → required output)
- Modify: `skills/analyzing-stocks/references/report-template.md` (§7.2 or §8)
- Create/extend: contract tests

### Required outcomes

- A compact live comps table (3–5 peers, current multiples appropriate to the
  valuation family) is required output, with a one-line reconciliation of the
  implied premium/discount vs the closest peer and why it is justified.
- Moat linkage rule: moat verdict below 3.0 forces an explicit excess-return
  fade horizon in terminal assumptions; a weak-moat name modeling decade-long
  above-peer growth must say why.

### Verification gate

- Contract tests pass; suite and validator pass.

## Task 4: Run-Stability & Adversarial Guards (E1 consumption, E3, E4)

### Objective

Make estimate noise visible and directional bias resistible, without new
infrastructure.

### Files

- Modify: `skills/investment-decision-workflow/SKILL.md`
- Modify: `skills/analyzing-stocks/SKILL.md` (Step 1)
- Modify: `skills/analyzing-stocks/references/value-investing-lens.md` (§5)
- Create/extend: contract tests

### Required outcomes

- Material-decision second opinion: for decisions at/above the existing
  material-exposure threshold (`>= 2%–3%` of net liquidation value), require
  either a `$debating-stocks` run or an independent second valuation pass
  before execution; record both WFVs in the decision record; divergence > 15%
  caps confidence and defaults the execution to `Wait`.
- User-view isolation: when the user states a directional view at intake, the
  report must construct and document the strongest opposing case before the
  valuation section.
- MoS noise floor: `value-investing-lens.md` states that a margin of safety
  below the process-noise floor (default 25–30% for long-duration/growth names)
  cannot justify `Buy` on valuation grounds alone.

### Verification gate

- Contract tests pass; suite and validator pass.
- After P0+P2 are live: paired-WFV divergence from this task's dual runs is
  logged in decision records, giving the first measured run-variance data.

## Explicitly Deferred

- Automated data fetching, caching, or structured filing extraction (P4
  direction in the roadmap; bigger infrastructure than a skill edit).
- Data-driven probability calibration — requires P2 outcome history first.
- Tooling to automate blind dual runs — manual rule first, automate if used.

## Measurement

P2 outcome scoring (per the decision-records spec) is the test harness for this
backlog: calibration by sector and valuation family, trigger-hit rates, and
paired-run WFV dispersion (Task 4) turn "is the valuation reliable" from a
qualitative argument into a measured number. Success for this backlog is that
those numbers improve after the fixes land — not that the rules exist.
