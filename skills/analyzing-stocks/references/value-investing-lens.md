# Value-Investing Lens

## Objective

Add a downside-first value-investing decision layer on top of fundamental analysis.
Focus on intrinsic value, margin of safety, and value-trap avoidance.
When a cash-flow DCF is not the right anchor, translate the same downside discipline into the route-appropriate valuation framework.

## 1) Core Principles

1. Price is what you pay; value is what you get.
2. Downside protection comes first; upside is secondary.
3. Use conservative assumptions, then test sensitivity.
4. Prefer real per-share value creation over flattering accounting optics.
5. Reject ideas with weak balance sheets, fragile funding, or unbounded dilution even if they look optically cheap.

## 2) Pick the Right Downside Anchor

Use the valuation family that matches the route:

- Operating companies: normalized FCFF or FCFE plus Reverse DCF
- Banks and insurers: tangible book or book value growth plus implied ROE / ROTCE sanity check
- Real estate: NAV / AFFO plus implied cap-rate or payout sanity check
- Binary biotech: rNPV / cash-floor plus implied probability or asset-value sanity check

If the business lacks stable normalized cash generation, do not pretend a cash-flow DCF is the main anchor.

## 3) Operating-Company FCF Workflow

Use this only when the company has stable recurring operations and cash conversion.

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

Choose method:
- FCFF DCF for enterprise-level valuation (then subtract net debt).
- FCFE DCF when equity cash generation is stable and leverage is manageable.

Baseline formula:

`Intrinsic Equity Value = PV(explicit cash flows) + PV(terminal value) - Net Debt +/- Non-operating Adjustments`

`Intrinsic Value Per Share = Intrinsic Equity Value / Diluted Shares`

Modeling rules:
1. Explicit forecast horizon: 5-10 years.
2. Growth and margin path must match moat and industry logic.
3. Discount rate must reflect business risk and leverage, built by the rule below.
4. Terminal growth should be conservative and below long-run nominal GDP in mature cases.
5. Avoid terminal value dominating all value without justification, bounded by the guardrail below.

### Discount Rate Construction

Build the discount rate explicitly, do not assert a round number:

- **Base:** current 10Y risk-free of the pricing currency + a stated
  **equity risk premium** (name the source/vintage) + business and leverage adders.
- **Floor:** for equities the discount rate may not fall below **risk-free + 300 bps**
  (adjust the exact adder only with stated justification). Macro-overlay regime
  adjustments apply on top of this build and may not breach the floor.
- State the build as a one-line sum in report Section 7.1 so the number is auditable.

### Terminal Value Guardrail

If **terminal value exceeds 75%** of total present value, a
**terminal sensitivity is mandatory** (vary terminal growth / exit multiple across a
plausible band) and **confidence caps at `Medium`** unless a Structural Re-rating Gate
with contracted-visibility evidence justifies the durability. Report the TV share of PV
in Section 7.1.

## 4) Non-DCF Margin-of-Safety Translation

When DCF is not the main anchor, define margin of safety against the weighted fair value from the chosen family:

- Banks and insurers: book-value-based fair value after reserve / credit / capital normalization
- Real estate: NAV or AFFO-based fair value after cap-rate and refinancing stress
- Binary healthcare: probability-adjusted value or cash-floor-weighted fair value after dilution

Margin of safety still means buying below conservative value. The math changes; the discipline does not.

## 5) Margin of Safety Rules

Compute:

`Margin of Safety = (Intrinsic Value - Current Price) / Intrinsic Value`

Interpretation bands:
- `>= 25%`: High safety buffer; eligible for higher-conviction sizing if quality is strong.
- `10% - 24%`: Medium buffer; usually `Starter` unless other risks are unusually low.
- `< 10%`: Low buffer; not enough for a value-style entry.

Do not use margin of safety in isolation. Combine with quality and balance-sheet checks.

## 6) Value-Trap Diagnostics

A cheap multiple is not enough. Run these checks:

1. Cash quality or earning-power quality: Is the value anchor real and repeatable?
2. Balance-sheet or funding risk: Can the capital structure survive a realistic stress?
3. Dilution risk: Are buybacks offset by SBC, equity issuance, or capital raises?
4. Competitive decay: Is moat weakening faster than market expects?
5. Governance quality: Is capital allocation value-accretive?
6. Structural decline risk: Is end-market shrinking or asset quality deteriorating?

Any two severe failures should block a positive value-investing verdict.

**Inflection caveat (avoid the omission-style trap):** when the
`Earnings Base Re-basing Gate` confirms a structural re-basing, run the value-trap
and market-implied checks on the **forward run-rate** base, not the trailing base.
A high *trailing* multiple is computed on an unrepresentatively low denominator, so
**a high trailing multiple is not by itself a value-trap signal** for a confirmed
inflection — judging it as one is itself a trap of omission. Conversely, if the
re-basing is unconfirmed, hold the trailing base and treat the optical cheapness or
richness accordingly.

## 7) Market-Implied Expectations Check

Derive the expectation embedded in market price with the route-appropriate method:

1. Operating companies: implied long-term growth and normalized margin
2. Banks and insurers: implied ROE / ROTCE or implied justified P/B / P/TBV
3. Real estate: implied cap rate, NAV discount, or payout durability
4. Binary healthcare: implied probability of success or value attributed to the lead asset

If implied assumptions are already very optimistic, margin of safety is likely overstated.
For a confirmed inflection, back out market expectations against the forward run-rate base;
backing them out against trailing earnings will overstate how optimistic the market looks
and can falsely flag a fairly priced re-rating as a bubble.

## 8) Decision Matrix

Combine financial quality and margin of safety:

| Financial quality | Margin of safety | Typical stance |
| --- | --- | --- |
| High | High (`>=25%`) | Buy / add candidate |
| High | Low (`<25%`) | Watchlist, wait for price |
| Medium | High | Selective, demand catalyst + risk controls |
| Medium | Low | Avoid or monitor only |
| Low | Any | Usually avoid (possible value trap) |

## 9) Position Sizing Interaction

Use with `portfolio-sizing.md`:
- `Core` is only possible when financial quality is high, confidence is high, and margin of safety is at least `25%`.
- High-uncertainty industries should be downgraded at least one tier even if upside looks large.
- Any failed value-trap screen blocks aggressive sizing.
- If `risk-register.md` returns 2+ `High` entries, maximum size is `Starter` regardless of margin of safety.

## 9a) Red-Team Interaction

Before writing the Investment Conclusion, complete `risk-register.md` and the Red-Team Gate (Section 9.0 of `report-template.md`).
The value-investing verdict (`Attractive / Neutral / Unattractive`) must be reconciled with the red-team output:
- If the highest-risk scenario drives the weighted fair value below current price, the verdict cannot be `Attractive`.
- If a key assumption failure reduces margin of safety below 10%, downgrade the verdict by one band.
- Document the reconciliation in the "何种证据会改变观点" field.

## 10) Required Output Block

Always include:

1. The chosen downside anchor and why it fits
2. Route-appropriate intrinsic value range
3. Margin-of-safety percentage and band
4. Value-trap diagnostic summary
5. Market-implied expectation check
6. Final value-investing verdict (`Attractive / Neutral / Unattractive`)
