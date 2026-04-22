# Financial Statement Diagnostics

## Objective

Assess financial quality with the right diagnostic family for the business.
Do not force an operating-company template onto balance-sheet financials, real-asset property names, or binary pipeline businesses.

## 1) Normalize the Dataset

Before ratio work:

1. Align periods (TTM, fiscal year, quarter) and currency.
2. Separate recurring vs non-recurring items.
3. Note accounting policy changes, restatements, and capital actions.
4. Track share count evolution, book value evolution, and off-balance-sheet obligations where relevant.

If restatements are frequent or key line items are not reconcilable, lower confidence.

## 2) Choose the Diagnostic Family First

### Operating companies

Use for software, consumer, industrials, semis, many healthcare operators, and utilities/telecom names with stable operating models.

Key checks:
- Revenue bridge: volume, price, mix, FX, M&A
- Margin quality: gross margin, operating leverage, adjusted-vs-GAAP gaps
- Balance sheet resilience: leverage, liquidity, maturity wall, contingent liabilities
- Cash conversion: CFO vs net income, FCF stability, maintenance vs growth capex
- Capital efficiency: ROIC vs WACC only when invested-capital math is meaningful

Stress design:
- `Mild`: revenue down 10%
- `Severe`: revenue down 20%

### Banks and insurers

Use for deposit-funded lenders, consumer lenders, P&C insurers, reinsurers, and life insurers.

Key checks:
- Asset quality: delinquencies, charge-offs, reserve adequacy, criticized assets
- Funding or float quality: deposit mix, surrender behavior, duration mismatch, liquidity buffer
- Capital strength: CET1, tangible equity, solvency ratio, statutory capital headroom
- Earnings quality: reserve releases, realized gains, catastrophe normalization, spread income quality
- Per-share protection: tangible book or book value per share growth after dilution and buybacks

Stress design:
- Banks: funding-cost shock, higher charge-offs, securities-mark pressure
- Insurers: reserve deterioration, catastrophe load, spread compression, asset-liability mismatch

Avoid:
- Net debt / EBITDA
- Interest-coverage heuristics designed for non-financial corporates

### Real estate and asset-backed property businesses

Use for REITs, landlords, developers, and asset-heavy property operators.

Key checks:
- Property cash flow: occupancy, same-store NOI, leasing spreads, cash rent vs straight-line rent
- Balance sheet: debt ladder, LTV, secured vs unsecured debt, covenant headroom
- Asset quality: cap-rate realism, tenant concentration, geographic exposure, development pipeline quality
- Cash distribution quality: FFO, AFFO, maintenance capex, payout coverage
- Per-share economics: repeated equity issuance, JV leakage, asset sales at discounts

Stress design:
- occupancy or rent decline
- cap-rate expansion
- refinancing shock

Avoid:
- treating developer or REIT EBITDA as a sufficient stand-in for asset value

### Pre-commercial biotech and binary healthcare

Use for pipeline-driven biotech, binary medtech, and healthcare names where cash runway and probability of success matter more than current margins.

Key checks:
- Liquidity and runway: quarterly burn, cash runway, debt covenants, milestone timing
- Program concentration: one-asset dependency, readout calendar, regulatory gating
- Accounting normalizations: milestone revenue, collaboration revenue, licensing and IPR&D distortion
- Financing risk: expected dilution, partnership dependence, warrant or convert overhang
- Downside containment: cash floor, salvage value, optionality outside the lead asset

Stress design:
- delayed readout or regulatory setback
- financing on worse terms
- lower probability of success or smaller addressable market

Avoid:
- revenue-down stress tests when the value driver is clinical probability and cash runway
- ROIC / WACC framing when invested-capital returns are not decision-useful

## 3) Accounting and Governance Red Flags

Flag and explain impact if any are present:

- Revenue recognition or reserve policy changes that flatter current earnings
- Large recurring "one-time" adjustments
- Receivables, inventory, reserve releases, or DAC movements that outrun underlying business quality
- Aggressive capitalization that suppresses expenses
- Dilution inconsistent with per-share value creation
- Environmental, legal, pension, or statutory obligations with weak disclosure

## 4) Financial Quality Scoring

Keep the five-category scorecard, but change the metric inside each bucket to match the diagnostic family.

Suggested buckets:
- earnings or earning-power quality
- balance-sheet or capital strength
- cash-flow or funding quality
- accounting/governance quality
- per-share economics

Weighted score bands:
- `>=4.0`: high quality
- `3.0-3.9`: acceptable with watch items
- `<3.0`: fragile quality

## 5) Required Output Block

Include:

1. Chosen diagnostic family and why it fits
2. Route-specific financial quality scorecard
3. Top 5 confirmed strengths and weaknesses
4. Stress result using the correct downside design for that family
5. Items that can invalidate forecasts or value anchors
