# Bear/Base/Bull Valuation Guide

## Objective

Translate business and financial analysis into a decision-ready valuation range with explicit probabilities, sensitivity, and value-investing checks.
Use the valuation family that matches the business. Do not force every route into a DCF-first operating template.

## 1) Scenario Construction Rules

Build three internally consistent scenarios:

1. Bear: downside path that is economically plausible for the route.
2. Base: normalized operating trajectory or normalized asset/credit outcome.
3. Bull: favorable but still coherent execution or cycle outcome.

Hard rules:
- Do not vary only one variable; change assumptions coherently.
- Ensure scenario assumptions align with moat durability assessment and the sector skill's KPI tree.
- Keep probability sum at 100%.
- Keep downside scenario economically plausible, not mechanically pessimistic.
- Do not change Bear/Base/Bull fair values solely because the current share price changed.

### Scenario Change Control

When reassessing a company with a prior local report, treat the prior Bear/Base/Bull
fair values as the starting baseline. The current market price updates expected
return, margin of safety, stance discipline, and market-implied expectations; it
does not by itself update intrinsic value.

Any change to Bear/Base/Bull fair values must be attributed to at least one explicit
driver:
- new filing, results, guidance, or management commentary
- normalized revenue, margin, FCF, book value, NAV, or per-share earnings estimate
- discount rate, required return, terminal multiple, or valuation multiple
- net debt, cash, share count, dilution, FX, or capital return
- material M&A, regulation, litigation, refinancing, or other capital action

If price changed but the valuation drivers did not, keep Bear/Base/Bull fair values
unchanged and update only the margin-of-safety, expected-return, market-implied
expectations, and position-sizing discussion. If a scenario value changes, include
a bridge explaining the prior value, current value, change, and reason.

## 2) Valuation Families

### Cash-flow-and-multiples

Use for steady-state operating companies.

Typical assumption rows:
- revenue CAGR or volume/price bridge
- operating or net margin path
- reinvestment intensity
- discount rate or required return
- terminal growth or exit multiple
- net debt or net cash
- diluted shares
- scenario probability

Typical methods:
1. DCF (FCFF or FCFE)
2. justified multiple cross-check

### Book-value-and-earnings / Book-value-and-float

Use for banks and insurers.

Typical assumption rows:
- ROTCE or ROE path
- normalized credit cost, combined ratio, or float yield
- capital generation and payout
- tangible book value or book value per share growth
- required return
- target P/TBV, P/B, or earnings multiple
- scenario probability

Typical methods:
1. P/TBV with ROTE or Gordon-style framework
2. P/B with ROE or excess-capital framework
3. earnings power cross-check when appropriate

### NAV-FFO-AFFO

Use for REITs, developers, and real-asset property names.

Typical assumption rows:
- occupancy, lease spreads, or sales velocity
- same-store NOI or gross margin path
- cap rate or NAV discount/premium
- FFO or AFFO path
- refinancing cost and debt ladder assumptions
- equity issuance or buyback assumptions
- scenario probability

Typical methods:
1. NAV
2. FFO / AFFO multiple

### Mid-cycle-DCF-NAV-multiples

Use for cyclical resource, energy, and asset-heavy materials names.

Typical assumption rows:
- long-run price deck
- volume, reserve life, or utilization
- cost curve position
- sustaining vs growth capex
- discount rate or exit multiple
- net debt, asset-sale optionality, or closure liabilities
- scenario probability

Typical methods:
1. mid-cycle DCF
2. NAV or EV / EBITDA or EV / resource cross-check

### rNPV-SOTP-cash-floor

Use for pre-commercial biotech and binary healthcare.

Typical assumption rows:
- probability of success
- peak sales or market penetration
- launch timing or readout timing
- exclusivity duration
- burn rate, runway, and financing dilution
- cash floor or residual value
- scenario probability

Typical methods:
1. rNPV or SOTP
2. peer multiple or cash-floor triangulation

## 3) Scenario Table Design

Use a route-appropriate assumption table rather than hard-coding revenue plus margin rows for every sector.

Minimum table columns:

| Assumption | Bear | Base | Bull |
| --- | --- | --- | --- |
| Route-specific key driver 1 |  |  |  |
| Route-specific key driver 2 |  |  |  |
| Valuation anchor or method input |  |  |  |
| Capital, leverage, dilution, or runway assumption |  |  |  |
| Scenario probability |  |  |  |

Add one-line rationale per row if the spread is wide.

## 4) Weighted Fair Value

Compute:

`Weighted Fair Value = sum(Scenario Fair Value * Scenario Probability)`

Then report:

1. Bear/Base/Bull fair values
2. Weighted fair value
3. Upside/downside vs current price
4. Implied expected value and asymmetry

## 5) Margin of Safety Integration

Compute intrinsic-value-based margin of safety:

`Margin of Safety = (Intrinsic Value - Current Price) / Intrinsic Value`

Use weighted intrinsic value or scenario-specific intrinsic values with explicit rationale.

Minimum output:
1. Bear/Base/Bull margin of safety
2. Weighted margin of safety
3. Safety band classification (`High / Medium / Low`)

Recommended thresholds (adjust if market regime requires):
- High: `>= 25%`
- Medium: `10% - 24%`
- Low: `< 10%`

## 6) Sensitivity Design

Test at least two key drivers plus one valuation parameter from the chosen family:

1. Operating names: growth, margin, discount rate or exit multiple
2. Financials: ROTCE/ROE, credit cost or combined ratio, target P/TBV or P/B
3. Real estate: NOI, cap rate, refinancing rate
4. Biotech: probability of success, peak sales, dilution or runway
5. Cyclicals: price deck, cost curve, sustaining capex, multiple or discount rate

Show how fair value shifts under combinations; avoid single-point confidence.

## 7) Market-Implied Expectations Check

Back out the expectation embedded in the current price using the chosen framework.
This is a price-explanation tool, not a license to rewrite Bear/Base/Bull intrinsic
values. Keep market-implied assumptions separate from analyst intrinsic-value
assumptions unless new evidence justifies changing the latter.

Examples:
- operating companies: Reverse DCF on growth and margin
- banks and insurers: implied ROTCE / ROE or implied P/TBV / P/B justification
- real estate: implied cap rate, NAV discount, or payout durability
- biotech: implied probability of success or value assigned to the lead asset

Reverse DCF is required only for steady-state operating companies.
For the other families, use the closest market-implied expectations check instead.

## 8) Sanity Checks

Before finalizing:

- Compare the embedded assumptions with historical and peer reality.
- Check that the chosen valuation method matches the economic driver of the business.
- Reconcile valuation conclusion with identified risks and the diagnostic-family stress test.
- Confirm valuation does not ignore balance-sheet, dilution, or refinancing downside.

If sanity checks fail, revise assumptions before publishing.

## 9) Required Output Block

Produce:

1. Scenario assumption table
2. Scenario valuation table
3. Weighted fair value and return profile
4. Margin-of-safety table
5. Sensitivity summary
6. Market-implied expectations takeaway
7. Key assumptions that most affect conclusion
