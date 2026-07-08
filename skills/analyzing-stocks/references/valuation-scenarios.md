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
- Probability discipline: start from a **default prior of 25 / 50 / 25** (Bear / Base /
  Bull). Deviations beyond **±15 pp** on any scenario require stated evidence; the
  **Bull scenario may not silently carry the thesis** via a probability shift in place
  of an assumption change.
- Bear plausibility benchmark: compare the Bear KPI path against the name's (or
  industry's) **worst historical drawdown** (revenue/margin/KPI). A generic −10% /
  −20% Bear is too mild for cyclicals; **a milder Bear must be justified** in one line.

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
- a framework or gate methodology change that first quantifies already-disclosed facts
  (e.g. a newly mandatory gate); attribute the revision to the gate, and never use it to
  launder a price- or sentiment-driven change

If price changed but the valuation drivers did not, keep Bear/Base/Bull fair values
unchanged and update only the margin-of-safety, expected-return, market-implied
expectations, and position-sizing discussion. If a scenario value changes, include
a bridge explaining the prior value, current value, change, and reason.

Any incremental or event-review update that moves a single scenario fair value by more
than 20%, or Weighted Fair Value by more than 15%, must republish the full scenario
assumption table (earnings base and multiple/discount rate per scenario), not just a
qualitative bridge. For cyclical or commodity-linked names it must also re-run the
`Cycle-Trough Cross-Check Gate`.

### Structural Re-rating Gate

Before finalizing any reassessment, test whether new evidence changes the business
regime rather than only the next-period earnings estimate. This is mandatory when
management commentary, filings, or contracts point to any of:

- contracted revenue visibility, take-or-pay terms, backlog conversion quality, lease
  duration, regulated asset-base visibility, or subscription/renewal durability
- lower earnings volatility, lower funding risk, lower refinancing risk, or lower
  commodity/cycle exposure
- higher customer lock-in, switching cost, pricing power, or recurring mix
- structurally higher or lower reinvestment returns, capital intensity, or dilution

If the regime changed, include a sensitivity that separates old-regime and new-regime
valuation. A structurally less volatile business may deserve a lower discount rate or
higher valuation multiple, but only if the evidence shows durable visibility rather than
one favorable quarter. Conversely, a business losing visibility should use a higher
discount rate or lower valuation multiple even if near-term earnings are strong.

Do not bury this inside the Bull case when it could plausibly affect Base valuation.
State whether the evidence is strong enough to update the headline Base case or only
strong enough for an upside/downside sensitivity.

### Earnings Base Re-basing Gate

The Structural Re-rating Gate above governs the *multiple or discount rate*. This
gate governs the *earnings or cash-flow base level itself*.
**Re-rating changes the multiple; re-basing changes the earnings base level.** Both
can happen at once, and both must be tested.

Trigger this gate whenever the latest-quarter annualized run-rate diverges materially
from the trailing full-year or TTM base (see the earnings-base representativeness check
in [financial-diagnostics](financial-diagnostics.md)). This is the symmetric counterpart
to peak-earnings normalization: just as a cyclical peak means trailing earnings
*overstate* steady-state power, a genuine inflection means **trailing earnings
understate forward earnings power**, and a multiple anchored on the trailing base will
systematically undervalue the company.

Required handling:

1. Classify the divergence as a **structural step-change** (re-base toward a forward
   run-rate base) or a **one-off / peak / pulled-forward** event (keep the normalized
   trailing base). Do not default to skepticism: a strong quarter is not automatically
   noise, and is not automatically signal.
2. Re-basing earnings **up** requires corroborating evidence beyond the reported
   number — for example new capacity online, signed contracts or backlog, order book,
   price or channel confirmation, gross-margin sustainability, and cash conversion of
   the new profit. The evidentiary bar is the same one used to resist over-re-rating;
   do not clear it on **one favorable quarter** alone.
3. If the evidence supports a step-change, set the headline Base on the forward
   run-rate base (not on trailing earnings) and say so; if it only supports a possible
   step-change, carry it as an upside sensitivity while Base holds the trailing base.
4. Record the result in the report's earnings-base re-basing block so the numerator
   used for valuation is never silently the trailing figure.

### Cycle-Trough Cross-Check Gate

The two gates above adjust value **upward**: re-rating lifts the multiple, re-basing
lifts the earnings base. This gate is their **symmetric downside counterpart**. It does
not undo them — a step-change or re-rating that cleared its evidentiary bar stands. Its
job is to bound how much of any re-based or re-rated floor is actually evidence-backed
and force the residual cyclicality to stay visible, so an earnings base set at or near a
cycle peak is not silently treated as steady-state.

Trigger this gate whenever the company is classified **cyclical or commodity-linked**
(including `Cyclical + Structural`) in [industry-structure](industry-structure.md), and
Bear/Base/Bull fair values are being set or changed — in full reports **and** in
incremental or event-review updates that touch scenario values. It is a cross-check, not
a veto: it cannot weaken the `Structural Re-rating Gate` or `Earnings Base Re-basing
Gate`, only expose the part of the floor those gates did not justify.

Produce every item below as a required row, not optional guidance:

1. **Cycle-position statement**: `early / mid / late / peak`, with the evidence used —
   pricing vs cost curve, margin vs history, inventory, capex cycle, supply announcements.
2. **Historical amplitude table**: peak-to-trough % change of revenue, gross margin, and
   EPS (use FCF or book value per share where EPS goes negative) over at least the last
   two completed cycles. If the company is too young, use the closest industry proxy and
   say so.
3. **Floor-coverage arithmetic**: quantify the share of current run-rate revenue and
   earnings protected by *disclosed* contractual mechanisms — take-or-pay, minimum-revenue
   clauses, price floors/collars, hedge book, backlog with cancellation terms,
   regulated/contracted revenue share. The Bear case may credit floor protection only up
   to that disclosed coverage; stress the uncovered remainder at mid-cycle or
   historical-trough economics, whichever the evidence supports.
4. **Explicit trough anchor inside the Bear case**: a trough-year earnings scenario
   (trough earnings × trough multiple) or an asset-based floor (P/B, NAV, replacement
   cost). State which anchor is used and show its value even when the headline Bear is set
   above it. Where an old trough price is not citable (e.g. delisted or pre-spin intraday
   lows), carry book value per share as a Fact from filings and label the trough price or
   multiple an Inference with its method stated; do not fabricate a citation.
5. **Gap statement**: if the headline Bear sits above the trough anchor, express the gap
   as the Bear's *implied* earnings and multiple and test those against the amplitude
   table (item 2) — the Bear is a scenario present value while the anchor is a bottom-tick,
   so compare like with like at the earnings level rather than on the raw price gap. The
   gap may be credited only to quantified floor coverage plus structural arguments that
   already passed the upward gates; and an argument that passed only *qualitatively* may
   support the Bear's multiple or duration but must never lift the Bear's earnings level to
   at or near the current run-rate. If the residual cannot be explained, pull the Bear down
   to what the evidence supports.
6. **Probability-asymmetry check**: when cycle-position evidence says late-cycle or peak,
   keeping symmetric scenario probabilities requires an explicit one-line justification;
   otherwise fatten the Bear tail.
7. **Base-over-run-rate check**: when cycle position is late or peak, a Base normalized
   earnings level at or above the latest annualized run-rate requires an explicit one-line
   justification (the mirror of the probability check). This does not override a Base that
   cleared the `Earnings Base Re-basing Gate` — that cleared evidence *is* the
   justification — but it stops an over-run-rate Base that never cleared re-basing from
   escaping the cross-check, since the gate otherwise binds only the Bear.

Record the result in the report's cycle-trough cross-check block, opening with a one-line
`Gate verdict`: `Bear stands` / `Bear pulled down` / `insufficient disclosure (Confidence
lowered)`. The historical amplitude table (item 2) is fed from the earnings-base
representativeness check in [financial-diagnostics](financial-diagnostics.md) whenever the
divergence is a cyclical peak.

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
6. Contracted or re-rating cases: visibility duration, contract coverage, customer
   concentration, earnings volatility, discount rate or valuation multiple

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
8. Cycle-trough cross-check block for cyclical or commodity-linked names: `Gate verdict`,
   cycle-position statement, historical amplitude table, floor-coverage arithmetic, Bear
   trough anchor, gap statement, probability-asymmetry check, and the Base-over-run-rate
   check (per the `Cycle-Trough Cross-Check Gate`)
