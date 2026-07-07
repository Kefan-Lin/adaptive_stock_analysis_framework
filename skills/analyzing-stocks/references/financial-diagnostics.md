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

### Earnings base representativeness (do this before anchoring any multiple)

Trailing earnings can **understate** forward earnings power just as often as they
overstate it. Before using any fiscal-year or TTM figure as a valuation base:

1. Compute the latest-quarter (or latest-half) **annualized run-rate** and the most
   recent TTM, and compare both to the **trailing full-year or TTM** base.
2. If the latest run-rate diverges materially from the trailing base in either
   direction, the trailing base may be unrepresentative — do not anchor a multiple
   on it without classifying the cause.
3. Classify the divergence as either:
   - **structural step-change**: new capacity online, a new product or business line
     ramping, post-turnaround operating leverage, or a durable mix shift — the profit
     center has genuinely re-based; or
   - **one-off / peak / pulled-forward**: lumpy project recognition, a one-time gain,
     a cyclical peak, channel stuffing, or order pull-forward — trailing-style
     normalization still applies.
4. Note **seasonality** direction explicitly (e.g. is the strong quarter normally a
   seasonally weak one?), so a seasonal artifact is not mistaken for an inflection and
   a genuine inflection in a seasonally weak quarter is not dismissed.

A structural step-change routes into the `Earnings Base Re-basing Gate` in
[valuation-scenarios](valuation-scenarios.md); a one-off does not. Do not default to
skepticism: a strong quarter is neither automatically noise nor automatically signal.

When the divergence is classified as a **cyclical peak**, or the name is
cyclical/commodity-classified in [industry-structure](industry-structure.md), also
compute the **historical amplitude table** — peak-to-trough % change of revenue, gross
margin, and EPS (use FCF or book value per share where EPS goes negative) over at least
the last two completed cycles, or the closest industry proxy if the company is too young —
and route it into the `Cycle-Trough Cross-Check Gate` in
[valuation-scenarios](valuation-scenarios.md), the same way a step-change routes into the
re-basing gate. This keeps a peak-quarter base from being anchored as steady-state.

## 2) Choose the Diagnostic Family First

### Operating companies

Use for software, consumer, industrials, semis, many healthcare operators, and utilities/telecom names with stable operating models.

Key checks:
- Revenue bridge: volume, price, mix, FX, M&A
- Margin quality: gross margin, operating leverage, adjusted-vs-GAAP gaps
- Balance sheet resilience: leverage, liquidity, maturity wall, contingent liabilities
- Cash conversion: CFO vs net income, FCF stability, maintenance vs growth capex
- Capital efficiency: ROIC vs WACC is **required** for operating-company family.
  If invested-capital math cannot be derived from available disclosures, state
  "insufficient disclosure" explicitly and lower the confidence level by one band.
  Do not omit or substitute a qualitative comment for the quantitative check.

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

### Understatement and hidden-value flags

Earnings quality runs both ways. Symmetrically check whether reported earnings or book
value **understate** economic reality, so a genuinely cheap or inflecting business is not
dismissed on optically high trailing multiples:

- conservative accounting that depresses current earnings: growth investment fully
  expensed rather than capitalized, accelerated depreciation, or front-loaded provisioning
- hidden or under-marked assets: land or property at historical cost, equity stakes or
  investment securities carried below fair value, an overfunded pension, or net cash masked
  by gross presentation
- trough or one-off costs in the base period (start-up losses for a ramping segment,
  restructuring, integration) that understate normalized earning power
- loss-making or pre-profit segments dragging blended margins while a profitable core
  compounds underneath

When understatement is material, normalize upward with the same evidentiary discipline used
for downward normalization, and route a genuine step-up through the
`Earnings Base Re-basing Gate`.

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
