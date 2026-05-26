---
name: analyzing-industrials-transport
description: Use when `analyzing-stocks` has already routed a company into industrial, transport, logistics, capital-goods, distributor, or services analysis and industry-specific KPI, accounting, and valuation logic is needed.
---

# Analyzing Industrials Transport

## Overview

Provide industrial and transport-specific KPI, accounting, and valuation logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation routing, risks, and monitor triggers.
- Do not restate generic report structure or margin-of-safety rules.

## 1. Industry Router

Choose one subtype:
- Capital goods and equipment
- Industrial services or distributors
- Transport and logistics
- Project-based or engineered systems

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Demand: orders, backlog, book-to-bill, volume, lane activity
- Pricing: contract repricing, fuel surcharge pass-through, mix
- Cost structure: utilization, labor productivity, maintenance, procurement
- Cash and capital: capex intensity, working capital, service attach rate
- Contract quality: cancellable vs non-cancellable backlog, price escalator clauses,
  advance payment terms, cost pass-through, service attach durability, and aftermarket mix
- Per-share economics: FCF conversion, restructuring drag, acquisition reliance

## 3. Accounting Traps and Normalizations

- Percentage-of-completion accounting can pull revenue forward.
- Restructuring charges may recur and should not be ignored blindly.
- Pension obligations or lease obligations may hide leverage.
- M&A-heavy rollups can inflate growth while depressing organic visibility.
- Backlog quality matters; not all backlog is equally cancel-resistant.
- A large backlog is not automatically high-quality demand; separate cancellable awards,
  fixed-price execution risk, price escalator protection, advance payment support, and
  service attach that can reduce earnings volatility.

## 4. Valuation Routing

- Primary: through-cycle DCF
- Secondary: EV/EBITDA or EV/EBIT
- Critical assumptions: backlog conversion, utilization, service mix, normalized margin, capex needs, backlog protection, and service/aftermarket mix
- Avoid: peak-cycle multiples or one-quarter run-rate valuation
- If backlog or service attach materially improves visibility, run a re-rating sensitivity
  against the old project-cycle multiple before changing the Base valuation.

## 5. Risk Checklist

- Order cancellations and backlog deterioration
- Utilization decline or project execution miss
- End-market cycle reversal
- Cost inflation or labor constraints
- Balance-sheet strain from acquisition or capex programs
- Backlog repricing failure or low-quality backlog that reverses expected visibility

## 6. Deliverables Back to Controller

- Subtype and operating model
- KPI tree with demand, margin, and capital metrics
- Key accounting or contract normalizations
- Valuation method route
- Risk checklist and monitor triggers
