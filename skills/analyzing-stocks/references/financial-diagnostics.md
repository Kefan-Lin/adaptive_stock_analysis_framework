# Financial Statement Diagnostics

## Objective

Assess earnings quality, balance sheet resilience, and cash-flow convertibility before assigning valuation confidence.

## 1) Normalize the Dataset

Before ratio work:

1. Align periods (TTM, fiscal year, quarter) and currency.
2. Separate recurring vs non-recurring items.
3. Note accounting policy changes and restatements.
4. Track share count evolution (basic and diluted).

If restatements are frequent, lower confidence.

## 2) Income Statement Checks

### Growth Quality

- Revenue growth split: volume, price, mix, FX, M&A.
- Compare reported growth vs organic growth.
- Check customer or segment concentration drift.

### Margin Quality

- Gross margin trend vs input costs and pricing.
- Operating margin vs SG&A intensity and R&D productivity.
- Gap between GAAP and adjusted operating metrics.

Interpretation rule:
- Margin expansion with weak operating cash flow is suspect.

## 3) Balance Sheet Checks

| Area | Core checks | Risk signal |
| --- | --- | --- |
| Leverage | Net debt/EBITDA, interest coverage, maturity wall | Coverage deterioration, near-term refinancing pressure |
| Liquidity | Cash, revolver, working capital seasonality | Reliance on short-term funding |
| Asset quality | Inventory turns, receivable aging, goodwill mix | Slow turns, rising write-down risk |
| Contingent risk | Off-balance liabilities, guarantees, legal reserves | Hidden leverage or tail liabilities |

Stress test two downside cases:
- `Mild`: revenue down 10%
- `Severe`: revenue down 20%

State covenant and liquidity implications.

## 4) Cash Flow and Capital Efficiency

Key diagnostics:

1. CFO vs net income trend (cash conversion).
2. FCF margin stability across cycle.
3. Capex split: maintenance vs growth.
4. Working capital efficiency (DSO, DIO, DPO).
5. ROIC vs WACC spread and trend.

Rule of thumb:
- Strong business quality usually shows persistent positive `ROIC - WACC`.

## 5) Accounting and Governance Red Flags

Flag and explain impact if any are present:

- Revenue recognition policy changes that boost near-term sales.
- Large recurring "one-time" adjustments.
- Receivables growing materially faster than revenue.
- Inventory growth without matching demand signal.
- Aggressive capitalization that suppresses expenses.
- SBC dilution inconsistent with per-share value creation.
- Pension/legal/environmental obligations with weak disclosure.

## 6) Financial Quality Scoring (Suggested)

Score each category `0-5`, then weight:

- Growth quality: 20%
- Margin quality: 20%
- Balance sheet strength: 25%
- Cash-flow quality: 25%
- Accounting/governance quality: 10%

Weighted score bands:
- `>=4.0`: high quality
- `3.0-3.9`: acceptable with watch items
- `<3.0`: fragile quality

## 7) Required Output Block

Include:

1. Financial quality scorecard table
2. Top 5 confirmed strengths/weaknesses
3. Balance sheet stress-test result
4. Cash conversion verdict (`Strong / Neutral / Weak`)
5. Items that can invalidate forecasts
