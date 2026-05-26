---
name: analyzing-banks
description: Use when `analyzing-stocks` has already routed a company into commercial-bank, regional-bank, consumer-lender, or other bank-like balance-sheet analysis and bank-specific KPI, credit, and valuation logic is needed.
---

# Analyzing Banks

## Overview

Provide bank-specific KPI, balance-sheet, and valuation logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, accounting traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic report structure or value-investing theory.

## 1. Industry Router

Choose one subtype:
- Large diversified bank
- Regional or community bank
- Consumer or specialty lender
- Digital or niche bank with unstable funding mix

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Earnings power: NIM, loan growth, fee mix, efficiency ratio
- Credit quality: charge-offs, delinquencies, reserve coverage, criticized assets
- Capital and liquidity: CET1, deposit mix, liquidity coverage, AOCI sensitivity
- Profitability: ROTCE, ROA, pre-provision earnings
- Franchise durability: deposit franchise re-rating, funding beta, noninterest fee mix,
  duration of ROTCE, digital engagement, and operating leverage from scale
- Per-share economics: tangible book value growth, buyback discipline, dilution

## 3. Accounting Traps and Normalizations

- Reserve releases can flatter earnings late in the cycle.
- AOCI and securities marks can change capital strength materially.
- CECL or provisioning noise must be separated from true credit trend.
- Fast asset growth with weak deposit quality can hide funding risk.
- Tangible book and ROTCE matter more than generic EBITDA-style metrics.
- Low reported deposit cost is not durable unless funding beta, customer stickiness,
  uninsured-deposit mix, and fee mix support a real franchise re-rating.

## 4. Valuation Routing

- Primary: P/TBV with ROTE or Gordon-style framework
- Secondary: P/E if earnings quality is stable
- Critical assumptions: normalized credit cost, deposit beta, capital generation, ROTCE path,
  fee mix durability, and whether ROTCE volatility deserves a different P/TBV
- Avoid: enterprise-value DCF as the main valuation anchor
- If deposit stickiness or fee income changes structurally, run old rate-cycle bank vs
  durable-franchise re-rating sensitivity before changing target P/TBV.

## 5. Risk Checklist

- Deposit flight or funding-cost shock
- Credit deterioration and reserve inadequacy
- Capital ratio compression
- Regulatory or liquidity-event risk
- Unrealized-loss exposure and securities-duration mismatch
- Deposit franchise deterioration or fee-income mix reversal that lowers justified P/TBV

## 6. Deliverables Back to Controller

- Subtype and funding model
- KPI tree with earnings, credit, capital, and liquidity metrics
- Key accounting normalizations
- Valuation route using book-value logic
- Risk checklist and monitor thresholds
