# Source Policy

## Objective

Force time-sensitive equity research to rely on primary sources before using summaries or market commentary.

## Source Hierarchy

Use this order unless the source does not exist:

1. Regulatory filings and official announcements
2. Earnings release, investor presentation, prepared remarks, official transcript
3. Company website disclosures, capital action notices, proxy, annual meeting materials
4. Reputable market data services and exchange data
5. Reputable media or third-party summaries

If a primary source conflicts with a secondary source, primary wins.

## Mandatory Internet Verification

Before finalizing any report, verify:
- Latest share price and date
- Latest quarterly or annual filing
- Latest guidance or outlook change
- Latest major capital action: buyback, dividend, issuance, M&A, refinancing

If current data cannot be verified, say so explicitly and lower confidence.

## Listing Line and Jurisdiction Rules

- Anchor the report on the security the user can actually trade, but reconcile it with the primary listing when ADRs, dual listings, or local lines differ.
- State which exchange line is the valuation anchor and which filing regime supplies the primary evidence.
- If the ADR is thinly traded but the local line is liquid, say so and downgrade sizing for execution friction.

## Evidence Ledger Rules

For every material number:
- Include date or reporting period
- Include source type
- Distinguish `Fact`, `Inference`, and `Assumption`

Preferred citation style inside the report:
- `Fact (FY2025 10-K)`
- `Fact (Q4 2025 earnings release)`
- `Inference (based on gross margin trend FY2023-FY2025)`
- `Assumption (base-case revenue CAGR 8%)`

## Primary Source Checklist

Use as many as available:

### US / SEC names

- `10-K / 10-Q / 20-F / 6-K / 8-K`
- earnings release and earnings deck
- conference call transcript or prepared remarks
- proxy statement for compensation/governance

### HK / HKEX names

- HKEX annual report, interim report, and results announcement
- inside information, allotment, buyback, dividend, placement, circular, or refinancing notice
- management presentation or webcast when provided

### CN / A-share names

- A-share annual / interim / quarterly reports
- `业绩预告` and `业绩快报`
- exchange announcements for placements, convertibles, buybacks, M&A, and major contracts

### Cross-market supplements

- debt presentation or credit agreement for leveraged names
- regulator or exchange statistics for banks, insurers, utilities, and other regulated sectors

## Accounting-Basis Mapping

- State whether the numbers are under `US GAAP`, `IFRS`, `PRC GAAP`, or another local basis.
- When comparing peers across standards, call out the line items most likely to break comparability: fair-value marks, impairment timing, lease treatment, capitalized R&D, reserve accounting, and regulatory capital definitions.
- If a mapping is uncertain, do not smooth it away; lower confidence and keep the assumptions visible.

## Currency and FX Normalization

When the primary reporting currency differs from the analysis or comparison currency:

1. **State the reporting currency** at the top of the evidence ledger (Section 10.4).
2. **Income-statement items** (revenue, gross profit, EBITDA, net income):
   use **period-average** exchange rates for the reporting period.
3. **Balance-sheet items** (cash, debt, book value, net assets):
   use **period-end** exchange rates.
4. Do not mix period-average and period-end rates within the same table or comparison.
5. Source the FX rates from the company's own filing footnotes when provided;
   otherwise cite a reputable data source and the date retrieved.
6. For cross-name comparisons, convert all names to a common currency using a
   consistent rate vintage (same quarter-end or year-end) and note this as an Assumption.
7. For ADR or dual-listed names, verify that USD/ADR valuations are reconciled with
   the primary-listing currency before finalizing a price target.

If FX rates cannot be sourced reliably, lower confidence and flag as a data gap.

## Failure Conditions

Do not finalize a confident stance if:
- You only have media summaries for a current event
- The latest reporting period is missing
- Capital structure is unclear
- Share count or dilution is stale
- The filing jurisdiction or accounting basis is unclear for the tradable line you are valuing
