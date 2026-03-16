---
name: analyzing-utilities-telecom
description: Use when `analyzing-stocks` has already routed a company into utilities, telecom, broadband, or regulated-network analysis and industry-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Utilities Telecom

## Overview

Provide utility and telecom-specific regulated-return, network, and yield analysis logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic source policy or unified report contract.

## 1. Industry Router

Choose one subtype:
- Regulated utility
- Wireless telecom
- Wireline or broadband operator
- Fiber, tower, or network infrastructure operator

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Revenue base: subscriber adds, churn, ARPU, allowed-rate-base growth
- Cost structure: network opex, maintenance, customer-acquisition cost
- Capital intensity: capex, spectrum or grid investment, asset-base growth
- Balance sheet: leverage, dividend coverage, refinancing need
- Per-share economics: regulated return, free cash after dividends, buyback restraint

## 3. Accounting Traps and Normalizations

- Capitalized costs can flatter near-term margins.
- Dividend optics can hide weak post-capex cash flow.
- Spectrum or network rights require long-horizon capital-return analysis.
- For utilities, rate-case timing can distort yearly earnings.
- For telecom, promo-led net adds can weaken long-term value if ARPU and churn deteriorate.

## 4. Valuation Routing

- Primary: DCF or DDM
- Secondary: EV/EBITDA
- Critical assumptions: allowed return, rate-base growth, churn, ARPU, dividend coverage, capex
- Avoid: treating yield alone as value without capex and leverage context

## 5. Risk Checklist

- Adverse regulatory reset or weaker allowed return
- Churn increase or ARPU decline
- Capex burden that weakens dividend sustainability
- Balance-sheet stress from rates or spectrum spending
- Competitive pricing pressure or technological substitution

## 6. Deliverables Back to Controller

- Subtype and regulatory or network model
- KPI tree with subscriber or rate-base metrics
- Key accounting normalizations
- Valuation route using DCF/DDM or EV/EBITDA
- Risk checklist and monitor thresholds
