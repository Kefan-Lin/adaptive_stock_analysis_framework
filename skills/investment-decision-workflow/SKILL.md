---
name: investment-decision-workflow
description: "Use when the user wants an end-to-end public-equity decision workflow: analyze a new stock idea, convert an existing valuation report into an action plan, review an existing stock/options position, or react to earnings, sharp price moves, technical damage, valuation changes, or option assignment risk. Orchestrates analyzing-stocks as the research and valuation engine, then produces a decision brief and execution sheet."
---

# Investment Decision Workflow

## Purpose

Run the user's end-to-end investment decision process:

`Idea Intake -> Research & Valuation Engine -> Action Sheet Adapter -> Execution Plan -> Position Review`

Use this skill as the top-level orchestrator. Reuse `$analyzing-stocks` for research and valuation; do not replace it with a looser trading template.

## Mode Routing

Choose the mode automatically and state `Mode` plus `Reason` at the top of the output.

Priority when multiple modes match:

1. `Position Review`
2. `Event Review`
3. `Existing Report to Action`
4. `New Idea Decision`

Modes:

- `New Idea Decision`: user gives a new ticker/company and asks whether it is worth buying, building a position in, or selling puts on.
- `Existing Report to Action`: user references a prior report, local thesis, or asks to turn research into an action sheet.
- `Position Review`: user provides existing stock holdings, cost basis, open option legs, assignment risk, cash, margin, or asks what to do with a live position.
- `Event Review`: user mentions earnings, major disclosure, sharp price move, technical break, valuation regime change, or option leg nearing assignment.

If mode routing is ambiguous and materially changes required inputs, ask one concise clarification. Otherwise proceed.

## Required Data Discipline

Before saying whether an action is executable now, perform `Live Verification`:

- current share price and date
- latest filing, earnings release, guidance, and material capital action
- next earnings date or similarly binary event
- option-chain terms when recommending or managing options
- technical state used by the Technical Execution Filter
- actual holdings, cost basis, open option legs, cash/margin impact for `Position Review`

If required live or position data is missing, output `Missing Inputs` and give only conditional sizing or conditional execution. Do not invent holdings or assume no existing exposure.

### State Home

Before asking the user for position or prior-report inputs, resolve the private
state home defined in
[decision-records](../analyzing-stocks/references/decision-records.md):

1. Read `~/.investing-home`; the trimmed content is the state-home path.
2. If the pointer file is missing, offer once per session to create it and the
   state-home skeleton; if declined, continue stateless.
3. If the pointer exists but the directory is unreadable, say so and continue
   stateless. Never invent state.

When the state home resolves, read `portfolio.yaml` and each target symbol's
latest decision record (identity and tie-break rules per decision-records)
before declaring `Missing Inputs`. An explicit in-session user statement
overrides file state; write the correction back at session end after user
confirmation.

## Research & Valuation Engine

Use `$analyzing-stocks` when a current valuation report is missing, stale, incomplete, or needs a full rerun.

Action-level outputs must be backed by a current upstream valuation. Do not put `needs future refresh`, `future reassessment`, or equivalent language into an executable current-position plan for any name that drives a buy/add/reduce/exit decision, has material portfolio exposure, or lacks a complete current valuation.

The upstream report must provide or be refreshed to provide:

- `Stance`: `Buy / Add / Hold / Reduce / Avoid`
- `Position Size`: `Core / Starter / Speculative / Watch-Avoid`
- `Bear / Base / Bull`
- `Weighted Fair Value`
- `Margin of Safety`
- `Confidence`
- value-trap judgment
- Red-Team Gate result
- `Add-on Trigger`
- `Trim/Exit Trigger`
- monitor list
- evidence ledger

Do not change Bear/Base/Bull fair values solely because current price changed. Price changes update margin of safety, expected return, market-implied expectations, valuation zone, and execution posture unless valuation drivers changed.

## Adversarial Stress-Test (optional escalation)

When bull and bear cases are both credible, the call is high-stakes or contested, or the name is a top portfolio driver, run `$debating-stocks` before finalizing the Decision Brief. It runs a fact-checked bull/bear (or multi-stakeholder) debate and returns cruxes, confidence, scenario expected returns measured from the current price, and flip conditions. Feed its verdict into the Red-Team / value-trap line of the Decision Brief; it informs `Stance` and `Most likely error` but does not override the Valuation Evidence Gate.

## Existing Report Path

For `Existing Report to Action`, `Position Review`, and `Event Review`, use this path:

`Existing Report / Prior Thesis -> Stale Check -> Incremental Valuation Update -> Decision Brief -> Execution Sheet`

### Stale Check

Decide whether the old report/thesis/action sheet can be used as the starting point.

When a state home is configured, resolve `Prior report / thesis anchor` from
the symbol's latest decision record automatically (latest by `date`, same-date
ties by the mode priority in decision-records). A user-pasted report still
takes precedence when newer.

Check:

- price drift from the old report anchor
- new filings, earnings releases, guidance, or company disclosures
- buyback, dividend, issuance, M&A, refinancing, or other capital action
- passed catalysts or monitor dates
- material technical state change
- earnings date and binary event calendar
- option-chain relevance for option execution
- holdings, cost basis, open option legs, cash/margin gaps for position work

If stale inputs are material, refresh the affected research/valuation modules before producing execution advice.

### Action-Blocking Refresh Gate

This gate prevents an action sheet from deferring required research.

Before `Decision Brief` or `Execution Sheet`, classify each security:

- `Current enough`: upstream valuation is complete and live verification did not identify material stale inputs.
- `Refresh required before action`: upstream valuation is missing, incomplete, stale, or contradicted by new material evidence.
- `Conditional only`: required live or position data is missing, so only conditional sizing or conditional execution is allowed.

If `Refresh required before action` applies, run `$analyzing-stocks` first and refresh the affected research/valuation modules before giving any concrete `Buy`, `Add`, `Reduce`, `Exit`, target weight, or order-level plan.

Hard triggers for `Refresh required before action`:

- no current full valuation report exists for the security
- old report lacks Bear/Base/Bull, Weighted Fair Value, margin of safety, confidence, Red-Team/value-trap check, add trigger, or trim/exit trigger
- position exposure is material to the portfolio, normally `>= 2% - 3%` of net liquidation value, or the security is one of the top portfolio drivers
- the proposed action would change exposure materially, normally `>= 1%` of net liquidation value
- new earnings, guidance, filing, capital action, financing, commodity-price regime, regulatory event, or thesis KPI has arrived after the old anchor
- the old conclusion says `needs refresh`, `future reassessment`, `stale`, or equivalent before action

After refreshing, replace the stale placeholder with the refreshed `Weighted Fair Value`, `Bear/Base/Bull`, `Stance`, `Position Size`, `Add-on Trigger`, `Trim/Exit Trigger`, and updated portfolio action. Do not leave `needs future refresh` as a current recommendation for material positions; use it only as a post-decision monitor after the current decision is fully supported.

### Incremental Valuation Update

Update only what new evidence justifies:

- keep Bear/Base/Bull if valuation drivers did not change
- update Bear/Base/Bull only for changed fundamentals, discount rate, multiple, net debt, share count, capital action, regulation, litigation, financing, or structural regime evidence
- run the Structural Re-rating Gate when revenue visibility, earnings volatility, contract quality, reinvestment economics, or risk premium changed
- run the Earnings Base Re-basing Gate when the latest-quarter annualized run-rate diverges materially from the trailing full-year or TTM earnings base, so a profit-center inflection is re-based onto a forward run-rate instead of being valued on unrepresentative trailing earnings (re-rating changes the multiple; re-basing changes the earnings base level)
- run the Cycle-Trough Cross-Check Gate when the name is cyclical or commodity-linked and any scenario value is set or changed, so a re-based or re-rated floor is bounded by disclosed contract coverage and an explicit trough anchor; it is the symmetric downside counterpart to the two upward gates and does not weaken them
- any update that moves a single scenario fair value by more than 20%, or Weighted Fair Value by more than 15%, must republish the full scenario assumption table (earnings base and multiple/discount rate per scenario), not just a qualitative bridge, and for cyclical names must re-run the Cycle-Trough Cross-Check Gate
- update margin of safety, market-implied expectations, and position discipline for price moves
- re-check Red-Team Gate, value-trap status, Add-on Trigger, Trim/Exit Trigger, and Position Size

### Valuation Evidence Gate

WFV can be refreshed only after new evidence changes intrinsic-value drivers. Do not raise Weighted Fair Value because the share price rose, the chart broke out, the valuation multiple expanded, market narrative improved, or a sell-side target-price upgrade appeared.

Evidence that may justify a WFV change:

- realized revenue, order, contract, or backlog improvement
- gross margin, FCF margin, ROIC, unit economics, or capital-efficiency improvement
- management guidance raised with verifiable support from backlog, customer contracts, constrained capacity, take-or-pay agreements, PPAs, long-term supply agreements, or similar evidence
- industry structure change such as HBM long-term agreements, optical networking order durability, power PPA / capacity revenue lock-in, or other supply-demand evidence
- discount-rate, risk-premium, share-count, net-debt, litigation, regulation, financing, or capital-allocation changes
- a structural earnings-base re-basing: the latest-quarter annualized run-rate exceeds the trailing base AND corroborating evidence (new capacity online, signed backlog or order book, price/channel confirmation, gross-margin sustainability, cash conversion) clears the Earnings Base Re-basing Gate — one favorable quarter alone does not

For cyclical or commodity-linked names, any WFV change — especially one justified by a re-based or re-rated earnings floor near a cycle peak — must also clear the Cycle-Trough Cross-Check Gate: credit floor protection only up to disclosed contract coverage, anchor the Bear on a trough-earnings or asset-based floor, and fatten the Bear tail unless symmetric probabilities are explicitly justified.

If the only new evidence is price action, sell-side target-price upgrade, or sentiment, trigger reassessment and market-implied-expectations analysis, but keep WFV unchanged until fundamentals support the change.

## Candidate & Valuation Mapping

Map upstream research into the user's decision language:

- `Core Candidate`: durable quality, quality-adjusted mispricing, and enough valuation support for potential core ownership.
- `Tactical Candidate`: temporary, cyclical, or event-driven mispricing with weaker long-term compounding quality.
- `Reject`: insufficient quality, insufficient valuation gap, unbounded downside, failed value-trap checks, or no willingness to own.

Map price to `Quality-Adjusted Valuation Zone`:

- `Accumulation Zone`: payoff/risk supports buying or eligible sell-put execution.
- `Hold Zone`: holding is acceptable; new exposure requires stronger evidence or better execution.
- `Exhaustion Zone`: stop adding, reduce sell-put aggressiveness, and consider trimming.
- `Invalidation Zone`: triggered by Thesis Break, not price alone.

High-quality Core Candidates may allow staged entry with a smaller margin of safety than lower-quality names; do not use a one-size-fits-all PE or discount rule.

## Technical Execution Filter

Technical analysis is an execution filter, not the investment engine. It can adjust timing, pacing, option structure, and review triggers, but cannot create a thesis, admit a rejected security, override valuation zone, or exceed exposure limits.

Standardize four checks:

1. `Trend Regime`: rising, range-bound, falling.
2. `Key Level`: support, resistance, prior high/low, long-term moving-average area.
3. `Volume/Price Confirmation`: breakout quality, pullback quality, failed support, or lack of demand.
4. `Momentum Risk Filter`: daily and weekly RSI/MACD overbought, oversold, and bullish/bearish divergence. Weekly signals carry more weight than daily signals.

Use overbought or bearish divergence to pause chase buying and reduce sell-put aggressiveness. Use oversold or bullish divergence only to improve execution for a security that already passes research and valuation gates.

## Option Execution Rules

Sell cash-secured puts only when all are true:

- candidate is not `Reject`
- user is willing to own the underlying at the net assignment price
- net assignment price is inside the relevant Accumulation Zone
- annualized premium or net breakeven discount clears the Premium Hurdle
- Equivalent Exposure stays inside the position limit
- Earnings Risk Block does not apply

Suggested starting hurdles:

- `Core Candidate`: net assignment price in Accumulation Zone and simple annualized premium around `12% - 15%` or better.
- `Tactical Candidate`: net assignment price in Accumulation Zone and simple annualized premium around `20% - 25%` or better.
- `Reject`: no sell puts.

Use simple annualized premium math first:

`premium / notional * 365 / days-to-expiry`

Add complexity only if the user asks.

## Earnings Risk Rules

Do not gamble on earnings.

`Earnings Risk Block`:

- Default: do not open new short puts that cross earnings or similarly binary disclosures.
- High IV or attractive premium is not enough.
- Rare exception: small Core Candidate exposure where the user is already willing to own through the event at the net assignment price.

`Earnings Risk Exit`:

- Existing short puts that cross earnings must trigger Event Review.
- Default objective is to close, reduce, or restructure before the event to remove or lower event exposure.
- Do not roll a short put through earnings just to avoid realizing a loss.
- Rolling is acceptable only when it avoids carrying short-put risk across the event or materially reduces Equivalent Exposure under an explicit Core Candidate exception.

Stock ownership can cross earnings as `Ownership Event Risk` when the position is sized as long-term ownership. Do not make large new pre-earnings buys just to bet on the report.

## Exposure & Stop Rules

Use `Equivalent Exposure` for stock plus option obligations. Cash-secured puts count by the stock exposure the user would take if assigned.

### Portfolio Risk Budget

For `Position Review`, portfolio plans, and multi-name action sheets, use stock-equivalent exposure rather than spot holdings alone.

- `stock-equivalent exposure = stock market value + cash-secured put assigned reserve + delta-adjusted directional ETF/option exposure`
- cash-secured put assigned reserve is locked for assignment or for closing the put; do not count it again as free cash, AI-buying cash, quality-buying cash, or crisis reserve
- set or preserve a cash reserve floor before recommending new buys; if the floor would be breached, output `No Action`, a conditional trigger, or a funding source
- enforce a single-name cap using stock-equivalent exposure, not just shares owned
- treat hedge puts as risk offsets only by reasonable net delta; do not count hedges as cash
- if the user's stated risk budget differs from the default, use the user's cap and show whether the plan fits it

For concentrated portfolio reviews, explicitly show sleeve targets, single-name cap, cash reserve floor, and assignment reserve before the execution table.

### Capital Allocation Waterfall

When multiple opportunities are eligible at once, apply this order before any single-name order plan:

1. Lock every open cash-secured put assigned reserve.
2. Preserve the cash reserve floor.
3. Fund high-conviction existing target exposures only when price and thesis gates are both met.
4. Fund higher-quality core candidates that are below target and inside Accumulation Zone.
5. Fund quality cash-flow / ballast candidates only from their reserved sleeve, not from assignment reserve.
6. Stop adding risk when portfolio drawdown approaches the user's max drawdown budget; prefer defensive swaps over higher gross exposure.

### Rebalance Rule

Upside drift does not automatically become a new target weight.

- positions inside target range can run without mechanical trading
- positions above target range plus tolerance require valuation and thesis review
- positions above the single-name cap must stop adding and be reduced toward the allowed range unless a fresh full report and explicit risk budget support the exception
- sleeves above their cap must pause new buys and rebalance after valuation repair
- speculative or venture buckets that rise above their cap must be trimmed; they do not graduate into core holdings solely because they rose

Valid execution outcomes:

- `Buy now`
- `Stage buy`
- `Sell cash-secured put`
- `Wait`
- `Reduce / Exit`
- `No Action`

`No Action` is a valid result when no trade clears thesis quality, valuation zone, exposure, technical, event-risk, or premium constraints.

Use `Do-Not-Initiate Rule` to stop opening new legs when price, premium, event risk, exposure, or thesis quality no longer supports the plan, even if an earlier plan listed unfilled legs.

Allow limited `Thesis-Upgrade Entry` only when new evidence raises intrinsic value or lowers risk enough to upgrade the thesis. Momentum alone is not enough.

## Output Contract

For current decisions, output these sections in order.

### 1. Mode & Inputs

- `Mode`:
- `Reason`:
- `Live Verification`:
- `Missing Inputs`:

### 2. Stale Check

Use for existing report, position, and event modes. For new ideas, write `N/A - New Idea Decision`.

- `Prior report / thesis anchor`:
- `Stale items`:
- `Refresh needed before action?`:
- `Action-Blocking Refresh Gate`: `Current enough / Refresh required before action / Conditional only`

### 3. Incremental Valuation Update

For new ideas, use the current `$analyzing-stocks` output or state that full valuation is required first.

- `Bear / Base / Bull change`:
- `Weighted Fair Value change`:
- `Valuation Evidence Gate`:
- `Margin of Safety update`:
- `Structural Re-rating Gate`:
- `Earnings Base Re-basing Gate`:
- `Cycle-Trough Cross-Check`: (cyclical/commodity-linked names; else `N/A`)
- `Red-Team / value-trap update`:
- `Add-on / Trim-Exit trigger status`:

### 4. Decision Brief

- `Candidate Tier`: `Core Candidate / Tactical Candidate / Reject`
- `Valuation Zone`: `Accumulation / Hold / Exhaustion / Invalidation`
- `Thesis status`:
- `Main risk`:
- `Most likely error`:
- `Action allowed?`:

### 5. Execution Sheet

- `Execution Method`: `Buy now / Stage buy / Sell cash-secured put / Wait / Reduce / Exit / No Action`
- `Current Exposure`:
- `Max Equivalent Exposure`:
- `Portfolio Risk Budget`: sleeve target, single-name cap, cash reserve floor, assignment reserve, and stock-equivalent exposure
- `Capital Allocation Waterfall`:
- `Rebalance Rule`:
- `Order / level plan`:
- `Technical Execution Filter`:
- `Option Suitability`:
- `Premium Hurdle`:
- `Earnings Risk Block / Exit`:
- `Do-Not-Initiate Rule`:
- `Review Trigger`:

Keep execution language concrete. If the evidence does not support a concrete order, say `No Action` or provide conditional branches instead of forcing a trade.

### 6. Decision Record

When a state home is configured, persist the outcome per
[decision-records](../analyzing-stocks/references/decision-records.md):

- For every symbol that received at least a `Stance` or an `Execution Method`,
  write or update `records/<SYMBOL>/YYYY-MM-DD-<mode>.md` (record identity
  `(symbol, date, mode)`; same identity updates in place) and append or update
  the symbol's `INDEX.md` row.
- After the user confirms an execution, backfill `action_taken` and update
  `portfolio.yaml`.
- A pure `Missing Inputs` / conditional-only outcome creates no record.
- Without a state home, skip this section (stateless behavior).
