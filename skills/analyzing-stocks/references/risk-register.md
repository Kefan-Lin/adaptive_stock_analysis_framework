# Risk Register

## Objective

Force a structured, category-by-category risk enumeration before sign-off.
Replace a free-text "top 3 risks" summary with a mandatory taxonomy sweep that prevents
analysts from anchoring only on the most-salient risk and missing structural threats.

## When to Use

Complete this register at the end of the diagnostics phase, before writing the
Investment Conclusion (Section 9 of the report template).
Two or more `High` entries require documented mitigation or offsetting margin-of-safety
or catalyst evidence; absent that documentation, reduce stance by at least one tier and
block any `Buy` or `Core` stance.

## Risk Taxonomy

For each category below, answer: `Low / Medium / High / N/A` and provide one-line evidence.
"N/A" is acceptable only when the category structurally cannot apply to this business
(e.g., no debt → no covenant risk; state-owned monopoly → no competition risk).

### 1. Regulatory & Policy Risk
- Definition: Changes in laws, tariffs, sector regulation, licensing, or government policy
  that could materially impair revenue, cost structure, or market access.
- Prompt: Is the business subject to pending regulatory proceedings, price controls,
  data/content rules, environmental mandates, or geopolitical trade restrictions?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 2. Customer & Revenue Concentration Risk
- Definition: Dependence on a small number of customers, platforms, or products
  such that losing one could cause a step-down in earnings.
- Prompt: Does any single customer, channel, or geography represent ≥ 20% of revenue?
  Does the company lack long-term contracts or pricing power with key buyers?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 3. Supply Chain & Input Cost Risk
- Definition: Vulnerability to commodity price volatility, single-source suppliers,
  logistics disruptions, or input cost inflation that cannot be passed through.
- Prompt: Are key inputs (components, energy, raw materials, talent) sourced from
  concentrated or geopolitically sensitive suppliers? Is there a cost-pass-through lag?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 4. Leverage & Covenant Risk
- Definition: Debt load, maturity structure, or financial covenants that could constrain
  operations, trigger refinancing stress, or accelerate in a downturn.
- Prompt: What is the nearest maturity wall? Are there maintenance covenants (leverage,
  interest coverage, LTV)? What is the headroom under the tightest covenant today?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 5. Accounting & Earnings Quality Risk
- Definition: Risk that reported earnings or book value do not faithfully represent
  economic reality due to aggressive accounting, frequent restatements, or opaque adjustments.
- Prompt: Are there large or recurring "adjusted" items, aggressive revenue recognition,
  unusual receivables/inventory build, low FCF/net-income conversion, or auditor changes?
  Use `financial-diagnostics.md` Section 3 (Accounting and Governance Red Flags) as checklist.
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 6. Litigation, ESG & Contingent Liability Risk
- Definition: Material lawsuits, environmental liabilities, pension obligations,
  product-liability exposure, or governance issues that could require unexpected cash outflows
  or impair reputation and license-to-operate.
- Prompt: Are there significant ongoing litigations, EPA/environmental orders, underfunded
  pension plans, or ESG controversies flagged in recent proxy or annual filing?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 7. Competitive & Disruption Risk
- Definition: Threat from new entrants, substitute technologies, platform shifts,
  or secular demand decline that could erode the business moat faster than the market expects.
- Prompt: Is a new technology, business model, or well-capitalized competitor meaningfully
  eating into pricing power or market share? Is the moat durability verdict < 3.0?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

### 8. Geopolitical & FX Risk
- Definition: Exposure to cross-border political risk, currency mismatch between
  revenues and costs, or capital-repatriation constraints for cross-listed or overseas operators.
- Prompt: Does a meaningful revenue/cost share sit in a jurisdiction with elevated
  political risk or capital controls? Is there unhedged FX exposure on the P&L or balance sheet?
- Rating: `Low / Medium / High / N/A`
- Evidence (1 line):

## Aggregated Risk Verdict

After completing all eight categories:

| Risk count | Highest rating present | Directive |
| --- | --- | --- |
| 0–1 High entries | — | Proceed normally; document in Section 10.1 |
| 2+ High entries | — | Require documented mitigation or offsetting margin-of-safety / catalyst evidence; absent that, reduce stance by at least one tier and block `Buy`/`Core` |
| Any High + Low margin of safety | — | Stance cannot exceed `Hold`; size cannot exceed `Starter` |

- Overall risk level: `Low / Medium / High`
- Stance constraint from risk register (if any):

## Integration Points

- Feeds Section 10.1 (Risk) in `report-template.md`: replace free-text bullets with
  the eight-bucket table, noting only the buckets rated Medium or High.
- Feeds Red-Team Gate in Section 9: the two or three highest-rated buckets become
  the required "what would make me wrong" answers.
- Cross-references `financial-diagnostics.md` Section 3 for accounting red flags.
- Cross-references `value-investing-lens.md` Section 6 (Value-Trap Diagnostics) for
  balance-sheet and dilution risk signals.
