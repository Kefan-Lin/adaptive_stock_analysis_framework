---
name: analyzing-healthcare-biotech
description: Use when `analyzing-stocks` has already routed a company into biotech, biopharma, medtech, or healthcare-service analysis and sector-specific KPI, runway, dilution, and valuation logic is needed.
---

# Analyzing Healthcare Biotech

## Overview

Provide healthcare and biotech-specific pipeline, reimbursement, and runway analysis logic.
Use as a companion to `$analyzing-stocks`, not as a standalone replacement for the controller.

## Controller Contract

- Return only subtype, KPI tree, traps, valuation route, risk checklist, and monitor triggers.
- Do not restate generic report structure or portfolio-sizing theory.

## 1. Industry Router

Choose one subtype:
- Commercial biopharma
- Pre-commercial biotech
- Medtech and devices
- Healthcare services or tools with reimbursement sensitivity

State:
- why this subtype fits
- 3 key value drivers
- 3 failure triggers

## 2. KPI Tree

- Asset or product value: peak sales, penetration, pricing, reimbursement access
- Pipeline quality: probability of success, catalyst path, patent duration
- Commercial execution: launch ramp, gross-to-net, field-force productivity
- Cash profile: burn rate, runway, milestone timing, financing terms
- Per-share economics: dilution path, partnership economics, royalty leakage

## 3. Accounting Traps and Normalizations

- Collaboration revenue can overstate recurring economics.
- Milestones and upfront payments are often non-recurring.
- Cash runway matters more than current accounting profit for early-stage names.
- IPR&D, licensing, and acquired pipeline accounting need normalization.
- Probability-adjust value; do not treat unproven assets as certain.

## 4. Valuation Routing

- Primary: SOTP or rNPV
- Secondary: peer multiple or cash-floor triangulation
- Critical assumptions: probability of success, peak sales, exclusivity duration, runway, dilution
- Avoid: standard steady-state DCF for early-stage or binary pipeline names

## 5. Risk Checklist

- Trial failure or regulatory rejection
- Reimbursement pressure or label limitation
- Patent cliff or competitive entry
- Financing or dilution shock
- Over-reliance on one asset or one catalyst

## 6. Deliverables Back to Controller

- Subtype and asset model
- KPI tree with pipeline, launch, runway, and dilution metrics
- Key normalizations for collaboration and milestone accounting
- Valuation route with probability adjustment
- Risk checklist and catalyst-driven monitor triggers
