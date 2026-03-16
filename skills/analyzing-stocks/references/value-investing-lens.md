# Value-Investing Lens

## Objective

Add a downside-first value-investing decision layer on top of fundamental analysis.
Focus on intrinsic value, margin of safety, and value-trap avoidance.

## 1) Core Principles

1. Price is what you pay; value is what you get.
2. Downside protection comes first; upside is secondary.
3. Use conservative assumptions, then test sensitivity.
4. Prefer cash-generating businesses over accounting-profit stories.
5. Reject ideas with weak balance sheets even if they look optically cheap.

## 2) Normalized Free Cash Flow Setup

Use normalized cash generation before valuation.

Steps:
1. Start from historical CFO and capex series (at least 5 years if available).
2. Separate maintenance capex from growth capex when possible.
3. Remove major one-off inflows/outflows.
4. Adjust for cycle position (peak vs trough).
5. Evaluate per-share FCF trend after dilution.

Suggested outputs:
- Normalized FCFF
- Normalized FCFE
- FCF margin trend
- FCF conversion (`FCF / Net Income`)

If normalized FCF is unstable or persistently negative, lower conviction materially.

## 3) FCF DCF Workflow (Intrinsic Value)

Choose method:
- FCFF DCF for enterprise-level valuation (then subtract net debt).
- FCFE DCF when equity cash generation is stable and leverage is manageable.

Baseline formula:

`Intrinsic Equity Value = PV(explicit cash flows) + PV(terminal value) - Net Debt +/- Non-operating Adjustments`

`Intrinsic Value Per Share = Intrinsic Equity Value / Diluted Shares`

Modeling rules:
1. Explicit forecast horizon: 5-10 years.
2. Growth and margin path must match moat and industry logic.
3. Discount rate must reflect business risk and leverage.
4. Terminal growth should be conservative and below long-run nominal GDP in mature cases.
5. Avoid terminal value dominating all value without justification.

## 4) Margin of Safety Rules

Compute:

`Margin of Safety = (Intrinsic Value - Current Price) / Intrinsic Value`

Interpretation bands:
- `>= 25%`: High safety buffer; eligible for higher-conviction sizing if quality is strong.
- `10% - 24%`: Medium buffer; usually `Starter` unless other risks are unusually low.
- `< 10%`: Low buffer; not enough for a value-style entry.

Do not use margin of safety in isolation. Combine with quality and balance-sheet checks.

## 5) Value-Trap Diagnostics

A cheap multiple is not enough. Run these checks:

1. Cash quality: Is FCF real and recurring?
2. Leverage risk: Can debt be serviced in a mild/severe downturn?
3. Dilution risk: Are buybacks offset by heavy SBC or issuance?
4. Competitive decay: Is moat weakening faster than market expects?
5. Governance quality: Is capital allocation value-accretive?
6. Structural decline risk: Is end-market shrinking secularly?

Any two severe failures should block a positive value-investing verdict.

## 6) Reverse DCF Sanity Check

Derive implied expectations from market price:

1. Solve for implied long-term growth.
2. Solve for implied normalized margin.
3. Compare implied assumptions with historical and peer reality.

If implied assumptions are already very optimistic, margin of safety is likely overstated.

## 7) Decision Matrix

Combine financial quality and margin of safety:

| Financial quality | Margin of safety | Typical stance |
| --- | --- | --- |
| High | High (`>=25%`) | Buy / add candidate |
| High | Low (`<25%`) | Watchlist, wait for price |
| Medium | High | Selective, demand catalyst + risk controls |
| Medium | Low | Avoid or monitor only |
| Low | Any | Usually avoid (possible value trap) |

## 8) Position Sizing Interaction

Use with `portfolio-sizing.md`:
- `Core` is only possible when financial quality is high, confidence is high, and margin of safety is at least `25%`.
- High-uncertainty industries should be downgraded at least one tier even if upside looks large.
- Any failed value-trap screen blocks aggressive sizing.

## 9) Required Output Block

Always include:

1. Normalized FCF assumptions (FCFF or FCFE)
2. DCF-derived intrinsic value range
3. Margin-of-safety percentage and band
4. Value-trap diagnostic summary
5. Reverse DCF implied expectation check
6. Final value-investing verdict (`Attractive / Neutral / Unattractive`)
