---
name: analyzing-consumer-retail
description: Use when `analyzing-stocks` has already routed a company into consumer, retail, restaurant, e-commerce, or marketplace-retail analysis and sector-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Consumer Retail

## Overview

Provide consumer and retail-specific operating, accounting, and valuation logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only industry-specific subtype, KPI tree, traps, valuation routing, and monitor list.
- Do not restate generic source policy or report contract.

## 1. Industry Router

Choose one subtype:
- Branded consumer goods
- Store-based retail
- E-commerce or marketplace retail
- Restaurants and foodservice chains

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Demand: traffic, same-store sales, order frequency, market share
- Pricing: average ticket, mix, promo intensity, take rate if marketplace
- Cost structure: gross margin, markdowns, logistics or labor ratio
- Working capital: inventory turns, returns, payable support
- Per-share economics: FCF conversion, lease-adjusted leverage, buyback quality

## 3. Accounting Traps and Normalizations

- Inventory build can precede markdown pressure; compare stock growth to sales growth.
- Lease accounting can hide true leverage; use lease-adjusted view where relevant.
- GMV or order growth can obscure weak take-rate or margin quality.
- Promo-driven revenue can overstate underlying demand.
- Franchise or marketplace revenue recognition may need gross-to-net normalization.

## 4. Valuation Routing

- Primary: DCF or FCFE
- Secondary: EV/EBIT or P/E
- Critical assumptions: same-store sales durability, gross margin recovery, inventory normalization, lease burden
- Avoid: sales multiples without a clear path to normalized margin and cash conversion

## 5. Risk Checklist

- Weak brand resilience or customer switching
- Margin pressure from discounting, freight, or labor
- Inventory write-downs or returns spike
- Marketplace subsidy or fulfillment-cost escalation
- Balance-sheet strain from leases or weak cash conversion

## 6. Deliverables Back to Controller

- Subtype and operating model
- KPI tree with demand, margin, and working-capital metrics
- Key normalizations and accounting risks
- Valuation method choice
- Main risks and monitor thresholds
