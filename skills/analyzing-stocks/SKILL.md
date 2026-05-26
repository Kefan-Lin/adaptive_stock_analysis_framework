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
   earnings volatility, contract durability, capital intensity, or risk premium.
8. Produce the unified report with stance and position sizing.

Do not skip steps 2, 3, 4, 5. A report without explicit routing and family selection is incomplete.

## Step 1: Define Scope

- Pin down ticker, exchange, currency, analysis date.
- If there are multiple listings, ADRs, or locally listed lines, state the primary listing and the actual tradable line you are evaluating.
- State horizon (`1-2y`, `3-5y`, `5y+`) and style (`compounder`, `cyclical`, `turnaround`, `special situation`).
- State the final user-facing `Stance`: `Buy / Add / Hold / Reduce / Avoid`.
- If working notes use `initiate / trim`, normalize them to `Buy / Reduce` before the final report.
- If user gives no constraints, assume a fundamental-investor context and label assumptions.

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
- [valuation-router](references/valuation-router.md)
- [valuation-scenarios](references/valuation-scenarios.md)
- [value-investing-lens](references/value-investing-lens.md)
- [portfolio-sizing](references/portfolio-sizing.md)
- [report-template](references/report-template.md)

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
- Use [valuation-router](references/valuation-router.md) plus the industry skill to confirm the `valuation family`.
- Use [valuation-scenarios](references/valuation-scenarios.md) for the route-appropriate `Bear / Base / Bull` method set and sensitivity design.
- Use the `Structural Re-rating Gate` in [valuation-scenarios](references/valuation-scenarios.md)
  whenever business-model visibility or earnings volatility changes. Do not leave a
  plausible re-rating thesis only inside vague Bull-case prose.
- Use [value-investing-lens](references/value-investing-lens.md) for downside framing, value-trap checks, and market-implied expectations.
- Reverse DCF is required only for steady-state operating companies. For other families, use the closest market-implied expectation check instead.
- Use [portfolio-sizing](references/portfolio-sizing.md) for `Core / Starter / Speculative / Watch-Avoid`.

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
