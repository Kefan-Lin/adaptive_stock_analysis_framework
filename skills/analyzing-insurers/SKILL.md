---
name: analyzing-insurers
description: Use when `analyzing-stocks` has already routed a company into P&C, life, reinsurance, or insurance-like underwriting analysis and insurer-specific KPI, reserve, and valuation logic is needed.
---

# Analyzing Insurers

## Overview

Provide insurance-specific underwriting, reserve, and valuation logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic margin-of-safety or report-template sections.

## 1. Industry Router

Choose one subtype:
- P&C insurer
- Reinsurer
- Life and annuity insurer
- Specialty insurer or broker-like platform with float economics

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Underwriting: combined ratio, loss ratio, expense ratio, rate adequacy
- Capital and reserves: reserve adequacy, solvency ratio, catastrophe exposure
- Investment income: float yield, duration, reinvestment rate
- Profitability: BVPS growth, ROE, normalized earnings power
- Per-share economics: buyback discipline, dilution, capital release capacity

## 3. Accounting Traps and Normalizations

- Reserve releases can overstate true underwriting quality.
- Catastrophe or weather periods must be normalized across cycles.
- DAC, reserve assumptions, and investment marks can distort headline earnings.
- Life insurers need asset-liability duration and spread sensitivity review.
- Book value quality matters more than simple EPS growth.

## 4. Valuation Routing

- Primary: P/B with ROE or excess-capital framework
- Secondary: dividend-based valuation or earnings yield
- Critical assumptions: normalized combined ratio, reserve quality, float return, solvency buffer
- Avoid: generic enterprise DCF without insurance-balance-sheet logic

## 5. Risk Checklist

- Reserve deterioration
- Cat or claims volatility
- Asset-liability mismatch
- Regulatory capital strain
- Reinsurance pricing or competitive underpricing cycle

## 6. Deliverables Back to Controller

- Subtype and underwriting model
- KPI tree with underwriting, reserve, capital, and float metrics
- Key accounting normalizations
- Valuation route using book-value logic
- Risk checklist and monitor thresholds
