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
- Contracted cash flow: offtake agreements, tolling arrangements, streaming or royalty
  contracts, floor-price hedge terms, take-or-pay commitments, and counterparty credit

## 3. Accounting Traps and Normalizations

- Normalize for cycle position; peak earnings are not steady-state value.
- Separate sustaining capex from growth capex.
- Reserve write-downs, impairment reversals, stripping, and DD&A can distort economics.
- Hedge gains/losses can obscure true realized economics.
- Offtake, tolling, or floor-price hedge contracts can transform commodity exposure into
  contracted cash flow; verify duration, floors, caps, volumes, and counterparty risk
  before applying a lower discount rate or higher multiple.
- Asset retirement or closure obligations can hide tail liabilities.

## 4. Valuation Routing

- Commodity assets:
  - Primary: mid-cycle DCF or NAV
  - Secondary: EV/resource or EV/EBITDA
- Specialty processors:
  - Primary: mid-cycle operating-company DCF or EV/EBITDA on normalized margins
  - Secondary: replacement-cost or asset-value cross-check only when assets truly anchor the thesis
- Critical assumptions: long-run price deck, reserve life, cost-curve position, sustaining capex, spread durability, contracted volume, and cost-curve reset risk
- Avoid: spot-price extrapolation or single-year earnings multiple at cycle extremes
- If contracts or policy support reduce commodity beta, run old spot-cycle vs contracted
  cash-flow sensitivity and say whether the valuation family shifts toward infrastructure-like DCF.
- Cycle-Trough Cross-Check (resource/energy): set the Bear trough price deck at cost-curve
  support (marginal-cost / AISC floor), and build the historical amplitude table on
  peak-to-trough realized price, margin, and EPS/FCF. Credit only *disclosed* hedge, offtake,
  tolling, streaming, or floor-price coverage in the Bear floor (its share of run-rate volume
  and revenue); stress the uncovered remainder at the trough deck. Anchor the Bear on NAV
  computed at trough prices and show it even when headline Bear is above. Run before finalizing
  Bear/Base/Bull.

## 5. Risk Checklist

- Commodity-price collapse or spread squeeze
- Reserve replacement failure or asset-quality downgrade
- Jurisdiction, permitting, or environmental risk
- Cost inflation and capital blowouts
- Over-levered balance sheet into a down-cycle
- Contract rollover, counterparty failure, or hedge expiry that restores commodity exposure

## 6. Deliverables Back to Controller

- Subtype and cycle position
- KPI tree with price, volume, cost, and reserve metrics
- Key normalizations and asset-liability adjustments
- Valuation route with long-run price assumptions
- Cycle-trough cross-check: trough price deck at cost-curve support, disclosed hedge/offtake coverage arithmetic, and NAV-at-trough-prices Bear floor
- Risk checklist and monitor thresholds
