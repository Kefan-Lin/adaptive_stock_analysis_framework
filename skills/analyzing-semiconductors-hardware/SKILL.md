---
name: analyzing-semiconductors-hardware
description: Use when `analyzing-stocks` has already routed a company into semiconductor, foundry, equipment, hardware, or electronics analysis and industry-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Semiconductors Hardware

## Overview

Provide semi and hardware-specific route logic for KPI, accounting, and valuation.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not own generic moat or portfolio-sizing logic.

## 1. Industry Router

Choose one subtype:
- Fabless design
- Foundry or memory
- Equipment and tools
- Commodity or branded hardware

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Demand: unit shipments, order intake, design wins, wafer starts
- Pricing: ASP, mix, node mix, memory cycle or end-market mix
- Cost structure: utilization, gross margin, yield, depreciation burden
- Working capital and cash: inventory days, capex intensity, prepayments
- Per-share economics: buyback quality, dilution, cycle-adjusted FCF

## 3. Accounting Traps and Normalizations

- Inventory build can hide demand weakness; compare channel and company inventory.
- Depreciation drag can distort near-term earnings after heavy capex.
- Prepayments, customer financing, or capacity reservations can blur true demand.
- One-cycle peak margins must be normalized.
- For hardware, separate product gross margin from services or software mix where relevant.

## 4. Valuation Routing

- Primary: through-cycle DCF
- Secondary: EV/Sales or EV/EBITDA depending on maturity
- Critical assumptions: cycle position, normalized gross margin, utilization, capex reset path
- Avoid: peak-demand annualization or trough-margin extrapolation without cycle context

## 5. Risk Checklist

- Cycle reversal or inventory correction
- Product-transition or node-execution miss
- Overcapacity or under-absorbed fixed costs
- Geopolitical or customer concentration risk
- Capex misallocation reducing through-cycle returns

## 6. Deliverables Back to Controller

- Subtype and cycle classification
- KPI tree with demand, pricing, and utilization metrics
- Key accounting normalizations
- Valuation route and cycle-adjustment logic
- Risk checklist and monitor thresholds
