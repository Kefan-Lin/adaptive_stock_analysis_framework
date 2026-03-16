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
4. Load shared references from this skill.
5. Build source map, evidence ledger, and any needed structural overlay.
6. Produce the unified report with stance and position sizing.

Do not skip steps 2, 3, 4. A report without explicit routing is incomplete.

## Step 1: Define Scope

- Pin down ticker, exchange, currency, analysis date.
- State horizon (`1-2y`, `3-5y`, `5y+`) and style (`compounder`, `cyclical`, `turnaround`, `special situation`).
- State decision verb: `initiate / add / trim / hold / avoid`.
- If user gives no constraints, assume a fundamental-investor context and label assumptions.

## Step 2: Route to One Industry Skill (Mandatory)

Choose one primary route and optionally one secondary route:

| Primary business type | Route to skill |
| --- | --- |
| Software, data platform, marketplace software, mission-critical infra | `$analyzing-software-platforms` |
| Consumer brand, retail, marketplace retail, restaurants | `$analyzing-consumer-retail` |
| Industrials, logistics, transport, capital goods, distributors | `$analyzing-industrials-transport` |
| Semiconductors, hardware, foundry, equipment, electronics | `$analyzing-semiconductors-hardware` |
| Mining, energy, materials, upstream/downstream commodity exposure | `$analyzing-resource-energy-materials` |
| Commercial banks, regional banks, digital banks | `$analyzing-banks` |
| P&C insurers, life insurers, reinsurers, brokers with insurance economics | `$analyzing-insurers` |
| REITs, developers, landlords, property platforms with NAV/FFO logic | `$analyzing-real-estate` |
| Pharma, biotech, medtech, healthcare services with pipeline/regulatory risk | `$analyzing-healthcare-biotech` |
| Utilities, telecom, regulated networks, dividend-like infrastructure | `$analyzing-utilities-telecom` |

If the company is mixed:
- Output `primary industry` and `secondary industry`.
- Use the primary industry skill for valuation routing and conclusion logic.
- Use the secondary industry skill only to enrich KPI, risk, and monitor discussion.
- Do not let the secondary industry override primary valuation method unless the business is truly split and you explicitly switch to a sum-of-parts approach.

## Step 3: Load Shared References (Mandatory)

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

## Step 4: Build Source Map and Evidence Ledger

- Follow [source-policy](references/source-policy.md) strictly.
- Tag each critical number with date and source.
- Label each statement as:
  - `Fact`
  - `Inference`
  - `Assumption`
- Keep an assumption ledger with sensitivity priority (`H/M/L`).

## Step 5: Execute Shared Analysis Modules

- Use [industry-structure](references/industry-structure.md) for value chain, cycle, and key variables.
- Use [industry-playbooks](references/industry-playbooks.md) as an optional structural overlay when the industry route is still too broad.
- Use [business-moat](references/business-moat.md) for business model and moat.
- Use [financial-diagnostics](references/financial-diagnostics.md) for three-statement quality.
- Use [capital-allocation](references/capital-allocation.md) for management and deployment of capital.
- Use [valuation-router](references/valuation-router.md) plus the industry skill for valuation methods.
- Use [valuation-scenarios](references/valuation-scenarios.md) for `Bear / Base / Bull` construction and sensitivity.
- Use [value-investing-lens](references/value-investing-lens.md) for margin of safety, reverse DCF, and value-trap checks.
- Use [portfolio-sizing](references/portfolio-sizing.md) for `Core / Starter / Speculative / Watch-Avoid`.

## Step 6: Produce the Unified Report

- Use [report-template](references/report-template.md) as the fixed contract.
- Always output all 10 blocks in the template.
- Always include:
  - `Bear / Base / Bull`
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

## Report Contract

The final report must contain these 10 blocks in order:
1. Executive summary
2. Company and industry classification
3. Industry structure and variable tree
4. Business model and moat
5. Management and capital allocation
6. Financial diagnostics
7. Valuation and bear/base/bull scenarios
8. Margin of safety, reverse DCF, and value-trap judgment
9. Investment conclusion, position size, and trading triggers
10. Risks, catalysts, monitor list, and evidence ledger
