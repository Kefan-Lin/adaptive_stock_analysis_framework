---
name: analyzing-real-estate
description: Use when `analyzing-stocks` has already routed a company into REIT, landlord, developer, or other real-estate-heavy analysis and property-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Real Estate

## Overview

Provide real-estate-specific property, balance-sheet, and valuation logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic report structure or source hierarchy.

## 1. Industry Router

Choose one subtype:
- Equity REIT
- Net lease or infrastructure-like REIT
- Developer or merchant builder
- Asset-light property manager, broker, or real-estate services platform

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

Boundary rule:
- Asset-light property service names may stay on this route for sector KPI coverage, but they can still use operating-company valuation family rather than default NAV/FFO logic.

## 2. KPI Tree

- Property economics: occupancy, lease spreads, same-store NOI, rent growth
- Asset value: cap rates, NAV, development yield, asset quality
- Capital structure: debt ladder, LTV, secured vs unsecured debt, liquidity
- Cash flow: FFO, AFFO, maintenance capex, payout coverage
- Lease durability: WALT, CPI escalator terms, tenant credit, lease renewal spreads,
  rent indexation, pre-leasing, and cap-rate re-rating potential
- Per-share economics: equity issuance, buybacks, JV leakage

## 3. Accounting Traps and Normalizations

- Straight-line rent can overstate current cash income.
- AFFO requires maintenance-capex and leasing-cost normalization.
- Development profits can make recurring earnings look stronger than they are.
- Asset marks and cap-rate assumptions need external realism.
- Equity issuance can offset operating progress on a per-share basis.
- Long leases and CPI escalator clauses can lower cash-flow risk, but tenant credit,
  renewal economics, and mark-to-market rent must support any cap-rate re-rating.

## 4. Valuation Routing

- Asset-heavy landlords and developers:
  - Primary: NAV
  - Secondary: FFO/AFFO multiple
- Asset-light property services:
  - Primary: operating-company valuation family, EBIT/FCF multiple, or DCF
  - Secondary: sector-specific transaction or management-fee multiples
- Critical assumptions: cap rates, occupancy durability, WALT, tenant credit, CPI escalator,
  lease rollover, debt refinancing, fee durability
- Avoid: forcing asset-light service businesses into NAV-only logic
- If lease duration, tenant quality, or indexation changes materially, run old cap-rate
  vs lower-risk cap-rate re-rating sensitivity.

## 5. Risk Checklist

- Refinancing wall or rate shock
- Tenant concentration or weak lease rollover
- Cap-rate expansion or asset markdown risk
- Development execution risk
- Per-share dilution from repeated equity issuance
- Tenant credit downgrade, lease rollover cliff, or CPI escalator reset that weakens duration value

## 6. Deliverables Back to Controller

- Subtype and property model
- Whether the name should keep operating-company valuation family
- KPI tree with NOI, NAV, leverage, and payout metrics
- Key accounting normalizations
- Valuation route using NAV or FFO/AFFO logic
- Risk checklist and monitor thresholds
