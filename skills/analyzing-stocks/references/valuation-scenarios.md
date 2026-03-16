# Bear/Base/Bull Valuation Guide

## Objective

Translate business and financial analysis into a decision-ready valuation range with explicit probabilities, sensitivity, and value-investing checks.

## 1) Scenario Construction Rules

Build three internally consistent scenarios:

1. Bear: adverse demand, weaker margins, multiple compression.
2. Base: normalized operating trajectory and fair multiple.
3. Bull: superior execution, sustained edge, optionality realization.

Hard rules:
- Do not vary only one variable; change assumptions coherently.
- Ensure scenario assumptions align with moat durability assessment.
- Keep probability sum at 100%.
- Keep downside scenario economically plausible, not mechanically pessimistic.

## 2) Required Assumption Set

Use this table for each scenario:

| Assumption | Bear | Base | Bull |
| --- | --- | --- | --- |
| Revenue CAGR (explicit period) |  |  |  |
| Operating margin / net margin |  |  |  |
| Reinvestment intensity (capex + WC) |  |  |  |
| Normalized FCF basis (FCFF or FCFE) |  |  |  |
| Tax rate |  |  |  |
| Discount rate / required return |  |  |  |
| Terminal growth or exit multiple |  |  |  |
| Net debt (or net cash) |  |  |  |
| Diluted shares outstanding |  |  |  |
| Scenario probability |  |  |  |

Add one-line rationale per row if spread is wide.

## 3) Valuation Methods

Prefer triangulation with at least two methods:

1. Intrinsic method: DCF (FCFF or FCFE).
2. Market method: justified multiple (P/E, EV/EBIT, EV/EBITDA, P/S depending on maturity).

### DCF skeleton

`Enterprise Value = sum(FCFF_t / (1 + r)^t) + Terminal Value / (1 + r)^N`

`Equity Value = Enterprise Value - Net Debt +/- Non-operating Adjustments`

`Per-share Fair Value = Equity Value / Diluted Shares`

### Multiple cross-check

`Per-share Fair Value = Forward Metric * Target Multiple`

Use peer and own-history context to justify target multiple.

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

Test at least two key drivers plus one valuation parameter:

1. Growth sensitivity (`-200 bps / base / +200 bps`)
2. Margin sensitivity (`-150 bps / base / +150 bps`)
3. Discount rate or exit multiple sensitivity

Show how fair value shifts under combinations; avoid single-point confidence.

## 7) Reverse DCF Sanity Check

Back out market-implied growth/margin from current price.

If implied assumptions exceed realistic operating or industry bounds, reduce margin-of-safety confidence.

## 8) Sanity Checks

Before finalizing:

- Compare implied long-term growth with industry reality.
- Compare implied margin with historical and peer range.
- Check if terminal assumptions exceed competitive logic.
- Ensure forecast reinvestment supports forecast growth.
- Reconcile valuation conclusion with identified risks.
- Confirm valuation does not ignore balance-sheet downside.

If sanity checks fail, revise assumptions before publishing.

## 9) Required Output Block

Produce:

1. Scenario assumption table
2. Scenario valuation table
3. Weighted fair value and return profile
4. Margin-of-safety table
5. Sensitivity summary
6. Reverse DCF takeaway
7. Key assumptions that most affect conclusion
