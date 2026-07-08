---
name: analyzing-stocks
description: Use when users ask for stock/company research reports, industry analysis, earnings interpretation, valuation, margin-of-safety judgment, or portfolio decision support and the work must route to different industry-specific frameworks instead of one generic template.
---

# Analyzing Stocks

## Overview

Act as the controller skill for equity research. Route each company to the right industry skill, enforce source quality, and produce one unified report contract.

Core principle: **先做行业分型，再做估值，再做仓位建议**。不同公司必须使用不同分析路径，避免“同一模板套所有股票”。

## Control Flow

1. Define scope and decision question.
2. Determine primary industry and optional secondary industry.
3. Route to one primary industry skill and optionally one secondary companion skill.
4. Determine the `analysis family` and `valuation family`.
5. Load shared references from this skill.
6. Build source map, evidence ledger, and any needed structural overlay.
7. Run the structural re-rating gate when new evidence changes revenue visibility,
   earnings volatility, contract durability, capital intensity, or risk premium,
   run the `Earnings Base Re-basing Gate` when the latest-quarter annualized run-rate
   diverges materially from the trailing full-year or TTM earnings base, and run the
   `Cycle-Trough Cross-Check Gate` whenever the name is cyclical or commodity-linked and
   Bear/Base/Bull values are being set or changed.
8. Run the input verification pass: confirm the critical valuation inputs and show the weighted-fair-value arithmetic before anything is finalized.
9. Produce the unified report with stance and position sizing.

Do not skip steps 2, 3, 4, 5. A report without explicit routing and family selection is incomplete.

## Step 1: Define Scope

- Pin down ticker, exchange, currency, analysis date.
- If there are multiple listings, ADRs, or locally listed lines, state the primary listing and the actual tradable line you are evaluating.
- State horizon (`1-2y`, `3-5y`, `5y+`) and style (`compounder`, `cyclical`, `turnaround`, `special situation`).
- State the final user-facing `Stance`: `Buy / Add / Hold / Reduce / Avoid`.
- If working notes use `initiate / trim`, normalize them to `Buy / Reduce` before the final report.
- If user gives no constraints, assume a fundamental-investor context and label assumptions.
- **User-View Isolation:** if the user states a directional view at intake (e.g. "this
  looks like a golden pit", "I think this is a short"), construct and document the
  **strongest opposing case** before writing the valuation section, so the scenario
  construction is not anchored to the user's prior. Record it in report Section 9.0.

## Step 2: Route to One Industry Skill (Mandatory)

Choose one primary route and optionally one secondary route:

| Primary business type | Route to skill |
| --- | --- |
| Software, data platform, marketplace software, mission-critical infra | `$analyzing-software-platforms` |
| Consumer brand, retail, marketplace retail, restaurants | `$analyzing-consumer-retail` |
| Industrials, logistics, transport, capital goods, distributors, specialty/process manufacturers without commodity-asset thesis | `$analyzing-industrials-transport` |
| Semiconductors, hardware, foundry, equipment, electronics | `$analyzing-semiconductors-hardware` |
| Mining, energy, bulk materials, commodity chemicals, spread-driven materials, asset-NAV-heavy processors | `$analyzing-resource-energy-materials` |
| Commercial banks, regional banks, digital banks | `$analyzing-banks` |
| P&C insurers, life insurers, reinsurers, brokers with insurance economics | `$analyzing-insurers` |
| REITs, developers, landlords, property-linked operators; asset-light managers may still keep operating-company valuation family | `$analyzing-real-estate` |
| Pharma, biotech, medtech, healthcare services, CRO, and HCIT; subtype decides operating-company vs probabilistic path | `$analyzing-healthcare-biotech` |
| Utilities, telecom, towers, fiber, and regulated or network infrastructure; tower/fiber names may use infrastructure overlay | `$analyzing-utilities-telecom` |

Boundary reminders:
- If a business is processor-heavy, service-led, or distribution-led rather than commodity/NAV-led, processor-heavy businesses may route to industrials instead.
- Healthcare services, CRO, and HCIT names are not automatically pipeline businesses.
- Property services or brokerage businesses can stay on the real-estate route for domain KPI coverage while still using operating-company valuation family.
- Tower/fiber names may use infrastructure overlay rather than pure telecom subscriber or utility rate-base logic.

If the company is mixed:
- Output `primary industry` and `secondary industry`.
- Use the primary industry skill for valuation routing and conclusion logic.
- Use the secondary industry skill only to enrich KPI, risk, and monitor discussion.
- Do not let the secondary industry override primary valuation method unless the business is truly split and you explicitly switch to a sum-of-parts approach.

### Conglomerates and holding companies

When the business is genuinely multi-segment with no single dominant economic engine —
typically when a second segment with different economics holds more than ~1/3 of value, or
for investment/operating holding companies — do not force one route's valuation family onto
the whole. Use a **sum-of-parts (SOTP)**:

- Value each material segment with its own industry route and valuation family.
- Net out holdco-level items: central costs, cross-holdings, parent-level net debt, and minority interests.
- Apply a **holding-company discount** where control, liquidity, or capital-allocation frictions
  warrant it, and state the assumed discount explicitly.
- State which segments drive value and which route governs each, then reconcile to one per-share number.

Use a single primary route only when one segment clearly dominates value; otherwise the SOTP
is the primary method, not an afterthought.

## Step 3: Determine `analysis family` and `valuation family`

Use the industry route plus subtype to choose the family that governs diagnostics and valuation.

| Route | Default analysis family | Default valuation family |
| --- | --- | --- |
| Software / consumer / industrials / semis | `operating-company` | `cash-flow-and-multiples` |
| Resource / energy / materials | `cycle-and-asset` | `mid-cycle-dcf-nav-multiples` |
| Banks | `balance-sheet-financial` | `book-value-and-earnings` |
| Insurers | `balance-sheet-financial` | `book-value-and-float` |
| Real estate | `real-asset-property` | `nav-ffo-affo` |
| Healthcare / biotech | `subtype-driven` | `subtype-driven` |
| Utilities / telecom | `regulated-or-network` | `regulated-dcf-ddm-multiples` |

Healthcare / biotech override:
- Commercial biopharma, devices, and healthcare services with stable recurring operations may use `operating-company`.
- Pre-commercial, binary, or pipeline-driven names must use `probabilistic-healthcare`.

Mixed-company rule:
- Primary skill decides the default `analysis family` and `valuation family`.
- Secondary skill may enrich KPI, risk, and monitor sections.
- Secondary skill cannot silently replace the valuation family; if it changes the valuation family, say so explicitly and justify the switch.

## Step 4: Load Shared References (Mandatory)

Always load these references from this skill:
- [source-policy](references/source-policy.md)
- [industry-structure](references/industry-structure.md)
- [industry-playbooks](references/industry-playbooks.md)
- [business-moat](references/business-moat.md)
- [financial-diagnostics](references/financial-diagnostics.md)
- [capital-allocation](references/capital-allocation.md)
- [macro-overlay](references/macro-overlay.md)
- [valuation-router](references/valuation-router.md)
- [valuation-scenarios](references/valuation-scenarios.md)
- [value-investing-lens](references/value-investing-lens.md)
- [risk-register](references/risk-register.md)
- [portfolio-sizing](references/portfolio-sizing.md)
- [portfolio-construction](references/portfolio-construction.md)
- [report-template](references/report-template.md)
- [decision-records](references/decision-records.md) — required only when a
  private state home is configured (see that file's resolution rules)

## Step 5: Build Source Map and Evidence Ledger

- Follow [source-policy](references/source-policy.md) strictly.
- Match the filing set to the listing jurisdiction and accounting basis (`US GAAP`, `IFRS`, `PRC GAAP`, or local equivalent).
- Tag each critical number with date and source.
- Label each statement as:
  - `Fact`
  - `Inference`
  - `Assumption`
- Keep an assumption ledger with sensitivity priority (`H/M/L`).
- For reassessments, explicitly tag any new contract, backlog, subscription, lease,
  regulated-return, reimbursement, or offtake evidence that may change valuation
  multiple or discount rate, not just near-term earnings.

## Step 6: Execute Shared Analysis Modules

- Use [industry-structure](references/industry-structure.md) for value chain, cycle, and key variables.
- Use [industry-playbooks](references/industry-playbooks.md) as an optional structural overlay when the industry route is still too broad.
- Use [business-moat](references/business-moat.md) for business model and moat.
- Use [financial-diagnostics](references/financial-diagnostics.md) for the route-appropriate diagnostic family rather than one generic three-statement template.
- Use [capital-allocation](references/capital-allocation.md) for management and deployment of capital.
- Use [macro-overlay](references/macro-overlay.md) for the regime-aware adjustment to discount
  rate, growth, FX, and commodity-cycle inputs before finalizing assumptions; record the
  one-line macro regime summary at the top of report Section 7.1.
- Use [valuation-router](references/valuation-router.md) plus the industry skill to confirm the `valuation family`.
- Use [valuation-scenarios](references/valuation-scenarios.md) for the route-appropriate `Bear / Base / Bull` method set and sensitivity design.
- Use the `Structural Re-rating Gate` in [valuation-scenarios](references/valuation-scenarios.md)
  whenever business-model visibility or earnings volatility changes. Do not leave a
  plausible re-rating thesis only inside vague Bull-case prose.
- Use the `Earnings Base Re-basing Gate` in [valuation-scenarios](references/valuation-scenarios.md)
  whenever the latest-quarter annualized run-rate diverges materially from the trailing
  full-year or TTM base, so a genuine profit-center inflection is not valued on
  unrepresentative trailing earnings. Re-rating changes the multiple; re-basing changes
  the earnings base level.
- Use the `Cycle-Trough Cross-Check Gate` in [valuation-scenarios](references/valuation-scenarios.md)
  whenever the name is cyclical or commodity-linked and Bear/Base/Bull values are being set
  or changed, so an earnings base near a cycle peak is not treated as steady-state. It is the
  symmetric downside counterpart to the two upward gates and bounds how much of a re-based or
  re-rated floor is evidence-backed; it does not weaken them.
- Use [value-investing-lens](references/value-investing-lens.md) for downside framing, value-trap checks, and market-implied expectations.
- Reverse DCF is required only for steady-state operating companies. For other families, use the closest market-implied expectation check instead.
- Use [risk-register](references/risk-register.md) to complete the mandatory eight-bucket risk
  sweep that feeds the Red-Team Gate (report Section 9.0) and the risk table (report Section 10.1).
- When the thesis is contested, the value-trap risk is live, or the name is a top portfolio
  driver, run `$debating-stocks` to execute the Red-Team Gate (Section 9.0) as a fact-checked
  adversarial bull/bear debate rather than a single-analyst sweep; carry its cruxes, confidence,
  and flip conditions into the conclusion. It reuses these same references, so its verdict maps
  straight onto Stance, value-trap judgment, and the Bear/Base/Bull scenarios.
- Use [portfolio-sizing](references/portfolio-sizing.md) for `Core / Starter / Speculative / Watch-Avoid`.
- Use [portfolio-construction](references/portfolio-construction.md) to convert the per-name tier
  into a portfolio-adjusted size (sector caps, KPI-driver correlation, factor tilt) for report Section 9.1.

## Step 6.5: Input Verification Pass (Mandatory)

Before producing the report, run a cheap audit of the inputs every downstream
number depends on. A wrong diluted share count or net debt figure silently
corrupts Weighted Fair Value, margin of safety, and sizing.

- Verify the three critical inputs per [source-policy](references/source-policy.md)
  `Critical-Input Verification`: the **diluted share count**, **net debt** (or net
  cash), and the **valuation earnings base** (the earnings/cash-flow numerator the
  valuation actually uses). Each must be confirmed by two independent sources or one
  filing-direct citation; state any discrepancy and lower confidence one band.
- **Earnings-base sanity floor:** reconcile the base-year / normalized EPS (or
  earnings numerator) used in the valuation to the **annualized latest reported
  quarter**. Setting the base **below** that annualized figure requires an explicit
  stated reason (e.g. deliberate cyclical normalization off a peak quarter); an
  **unexplained below-annualized base** is a red flag to re-verify the source before
  finalizing, because it usually signals a data or estimate error rather than a real
  earnings base. This is a justify-or-re-verify check, not an absolute block —
  legitimate peak-normalization is allowed with a stated reason.
- **Post-correction consistency sweep:** if input verification corrects any critical
  input *after* scenarios or multiples are drafted, re-derive every dependent figure
  and confirm no section still uses the superseded value. A corrected input may not
  leave stale figures elsewhere — EPS, multiples, Weighted Fair Value, and margin of
  safety must all reflect the corrected input.
- Recompute Weighted Fair Value as an explicit shown line, `sum(probability ×
  scenario value)`, not an asserted scalar; it must reconcile with the scenario
  table.
- For dual-listed / ADR names, assert the currency-and-tradable-line reconciliation
  before stating the target range.
- Record the pass in report Section 10.4's `输入验证块` so skipping it is visible.

## Step 7: Produce the Unified Report

- Use [report-template](references/report-template.md) as the fixed contract.
- Always output all 10 blocks in the template.
- Always include:
  - `Bear / Base / Bull`
  - `Structural re-rating sensitivity` when applicable
  - `Fact / Inference / Assumption`
  - `Stance`
  - `Weighted Fair Value`
  - `Margin of Safety`
  - `Position Size`
  - `Add-on Trigger`
  - `Trim/Exit Trigger`
  - the fixed closing line from the template
- When a private state home is configured (see
  [decision-records](references/decision-records.md)), emit the decision-record
  frontmatter block at the end of the report and offer to save it as a
  `mode: research` record plus its `INDEX.md` row, so standalone research runs
  are archive-ready without the decision workflow.

## Hard Rules

1. Latest price, latest filings, latest guidance, and latest capital action must be internet-verified before a final conclusion.
2. Every material number must include a date or reporting period.
3. No positive stance without an explicit downside path.
4. No `Core` position without passing value-trap checks and meeting the margin-of-safety threshold.
5. If data gaps materially affect valuation, lower confidence and widen the value range.
6. If the company fits a high-uncertainty bucket, auto-downgrade position sizing by at least one tier.
7. If a secondary industry skill is used, state exactly which sections it influenced.
8. If the route is not `operating-company`, do not force EBITDA, ROIC-WACC, or Reverse DCF terminology where it does not fit the balance-sheet or asset framework.
9. If the tradable line is illiquid, the ADR differs materially from the primary listing, or the bid-ask spread is wide, downgrade position sizing and say which line anchors the conclusion.

## Merge schema

Every primary industry skill must return these controller-ready fields:

- `subtype`
- `analysis family`
- `valuation family`
- `kpi tree`
- `accounting normalizations`
- `valuation anchors`
- `risk checklist`
- `monitor triggers`
- `sections influenced`

Controller merge rules:

- Shared references define the report spine and evidence rules.
- Primary skill output defines the KPI language, diagnostic family, and valuation anchors.
- Secondary skill output may enrich only the sections listed in `sections influenced`.
- If a sector skill does not provide one of the required fields, the controller must say the contract is incomplete and lower confidence.

## Report Contract

The final report must contain these 10 blocks in order:
1. Executive summary
2. Company and industry classification
3. Industry structure and variable tree
4. Business model and moat
5. Management and capital allocation
6. Financial diagnostics
7. Valuation and bear/base/bull scenarios
8. Margin of safety, market-implied expectations, and value-trap judgment
9. Investment conclusion, position size, and trading triggers
10. Risks, catalysts, monitor list, and evidence ledger
