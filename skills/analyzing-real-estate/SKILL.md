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
- Property manager or services-heavy real-estate operator

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Property economics: occupancy, lease spreads, same-store NOI, rent growth
- Asset value: cap rates, NAV, development yield, asset quality
- Capital structure: debt ladder, LTV, secured vs unsecured debt, liquidity
- Cash flow: FFO, AFFO, maintenance capex, payout coverage
- Per-share economics: equity issuance, buybacks, JV leakage

## 3. Accounting Traps and Normalizations

- Straight-line rent can overstate current cash income.
- AFFO requires maintenance-capex and leasing-cost normalization.
- Development profits can make recurring earnings look stronger than they are.
- Asset marks and cap-rate assumptions need external realism.
- Equity issuance can offset operating progress on a per-share basis.

## 4. Valuation Routing

- Primary: NAV
- Secondary: FFO/AFFO multiple
- Critical assumptions: cap rates, occupancy durability, lease rollover, debt refinancing
- Avoid: EBITDA-only valuation without asset-value context

## 5. Risk Checklist

- Refinancing wall or rate shock
- Tenant concentration or weak lease rollover
- Cap-rate expansion or asset markdown risk
- Development execution risk
- Per-share dilution from repeated equity issuance

## 6. Deliverables Back to Controller

- Subtype and property model
- KPI tree with NOI, NAV, leverage, and payout metrics
- Key accounting normalizations
- Valuation route using NAV or FFO/AFFO logic
- Risk checklist and monitor thresholds
