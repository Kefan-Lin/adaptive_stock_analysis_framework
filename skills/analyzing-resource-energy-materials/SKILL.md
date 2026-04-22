---
name: analyzing-resource-energy-materials
description: Use when `analyzing-stocks` has already routed a company into mining, metals, energy, chemicals, or other resource-heavy analysis and industry-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Resource Energy Materials

## Overview

Provide cycle-aware resource, energy, and materials analysis logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic report-template or evidence-ledger rules.

## 1. Industry Router

Choose one subtype:
- Upstream energy
- Diversified mining or bulk materials
- Commodity chemicals or spread-driven materials
- Specialty chemicals or processors with formulation, distribution, or service economics
- Royalty or streaming-like asset exposure

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

Boundary rule:
- If the thesis is mostly formulation, service, distribution, or customer-embedded economics rather than commodity exposure, reroute to `analyzing-industrials-transport`.

## 2. KPI Tree

- Price: realized commodity price, hedge profile, benchmark spread
- Volume: production, reserve replacement, project timing
- Cost structure: AISC or cash cost, LOE, recovery rate, grade
- Capital intensity: sustaining vs growth capex, F&D or reserve replacement
- Balance sheet: leverage, liquidity, covenant cushion, asset sale optionality

## 3. Accounting Traps and Normalizations

- Normalize for cycle position; peak earnings are not steady-state value.
- Separate sustaining capex from growth capex.
- Reserve write-downs, impairment reversals, stripping, and DD&A can distort economics.
- Hedge gains/losses can obscure true realized economics.
- Asset retirement or closure obligations can hide tail liabilities.

## 4. Valuation Routing

- Commodity assets:
  - Primary: mid-cycle DCF or NAV
  - Secondary: EV/resource or EV/EBITDA
- Specialty processors:
  - Primary: mid-cycle operating-company DCF or EV/EBITDA on normalized margins
  - Secondary: replacement-cost or asset-value cross-check only when assets truly anchor the thesis
- Critical assumptions: long-run price deck, reserve life, cost-curve position, sustaining capex, spread durability
- Avoid: spot-price extrapolation or single-year earnings multiple at cycle extremes

## 5. Risk Checklist

- Commodity-price collapse or spread squeeze
- Reserve replacement failure or asset-quality downgrade
- Jurisdiction, permitting, or environmental risk
- Cost inflation and capital blowouts
- Over-levered balance sheet into a down-cycle

## 6. Deliverables Back to Controller

- Subtype and cycle position
- KPI tree with price, volume, cost, and reserve metrics
- Key normalizations and asset-liability adjustments
- Valuation route with long-run price assumptions
- Risk checklist and monitor thresholds
