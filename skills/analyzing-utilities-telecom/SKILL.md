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
- Tower or fiber infrastructure operator

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

Boundary rule:
- Tower or fiber names may lean on infrastructure-style DCF, AFFO, or EV/EBITDA rather than utility rate-base logic or subscriber-telecom logic.

## 2. KPI Tree

- Revenue base: subscriber adds, churn, ARPU, allowed-rate-base growth
- Cost structure: network opex, maintenance, customer-acquisition cost
- Capital intensity: capex, spectrum or grid investment, asset-base growth
- Balance sheet: leverage, dividend coverage, refinancing need
- Contracted or regulated visibility: PPA terms, capacity contract duration,
  interconnection queue position, rate-case lag, allowed ROE lag, tenancy contracts,
  and contracted cash flow coverage
- Per-share economics: regulated return, free cash after dividends, buyback restraint

## 3. Accounting Traps and Normalizations

- Capitalized costs can flatter near-term margins.
- Dividend optics can hide weak post-capex cash flow.
- Spectrum or network rights require long-horizon capital-return analysis.
- For utilities, rate-case timing can distort yearly earnings.
- For telecom, promo-led net adds can weaken long-term value if ARPU and churn deteriorate.
- PPA, capacity contract, tenancy, or regulated asset visibility can reduce cash-flow risk,
  but only if counterparty credit, escalation terms, and capex obligations preserve returns.

## 4. Valuation Routing

- Regulated utility:
  - Primary: DCF or DDM
  - Secondary: rate-base or allowed-return cross-check
- Telecom:
  - Primary: DCF or EV/EBITDA
  - Secondary: subscriber or ARPU-based multiple context
- Tower or fiber names may lean on infrastructure-style DCF, AFFO, or EV/EBITDA with tenancy and churn assumptions.
- Critical assumptions: allowed return, rate-base growth, PPA or capacity contract coverage,
  interconnection execution, churn, ARPU, tenancy, dividend coverage, capex
- Avoid: treating yield alone as value without capex and leverage context
- If contracted cash flow or regulatory visibility changes materially, run old yield
  multiple vs lower-risk infrastructure/regulated re-rating sensitivity.

## 5. Risk Checklist

- Adverse regulatory reset or weaker allowed return
- Churn increase or ARPU decline
- Capex burden that weakens dividend sustainability
- Balance-sheet stress from rates or spectrum spending
- Competitive pricing pressure or technological substitution
- PPA, capacity contract, or interconnection failure that removes expected visibility

## 6. Deliverables Back to Controller

- Subtype and regulatory or network model
- KPI tree with subscriber or rate-base metrics
- Key accounting normalizations
- Valuation route using DCF/DDM or EV/EBITDA
- Risk checklist and monitor thresholds
