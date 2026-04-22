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

## Market-Specific Disclosure Checklist

Each market has a distinct disclosure calendar and mandatory-announcement regime.
Do not apply the "absence = red flag" intuition from one market to another.
A missing quarterly report is normal for HKEX names; it is a red flag for SEC names.

### US / SEC — Key Disclosure Calendar

| Document | Frequency | Deadline after period-end | Where to find |
| --- | --- | --- | --- |
| 10-K | Annual | 60 / 75 / 90 days (by filer size) | EDGAR |
| 10-Q | Quarterly (Q1–Q3) | 40 / 45 days | EDGAR |
| 8-K | Current events (material) | 4 business days | EDGAR |
| Proxy (DEF 14A) | Annual | Before AGM | EDGAR |
| Earnings release | Quarterly | No statutory deadline (usually 2–4 weeks after quarter) | IR website / 8-K |

Absence markers: Missing 10-Q filing beyond deadline → NT 10-Q extension notice required;
if not filed, downgrade confidence to `Low`.

---

### HK / HKEX — Key Disclosure Calendar

| Document | Frequency | Deadline after period-end | Where to find |
| --- | --- | --- | --- |
| Annual report (年报) | Annual | 4 months after fiscal year-end | HKEX EDGAR / company IR |
| Interim report (中期报告) | Semi-annual | 3 months after H1 year-end | HKEX EDGAR / company IR |
| Preliminary results announcement (业绩公告) | Semi-annual (H1 + full year) | Usually within 2–3 months | HKEX news release |
| Inside information (内幕消息) | As triggered | Within 1 business day | HKEX news release |
| Connected transactions (关连交易) | As triggered | Before completion | HKEX circular |
| Notifiable transactions (须予披露交易) | By size threshold | Before or at completion | HKEX circular |

Key HKEX differences vs SEC:
- **No quarterly reports (季报)** are required; only semi-annual.  Missing quarterly data is normal.
- Preliminary results announcements (业绩公告) are often issued before the full annual/interim report.
- HKEX Listing Rules require disclosure of continuing connected transactions annually; check for
  related-party dependency that may not be obvious from the financial statements alone.
- Management forward guidance is rarely quantitative (no EPS guidance convention); treat
  absence of guidance as neutral, not as a red flag.

---

### CN / A-share — Key Disclosure Calendar

| Document | Frequency | Deadline after period-end | Where to find |
| --- | --- | --- | --- |
| 年度报告 (Annual) | Annual | April 30 | CNINFO / SZSE / SSE |
| 半年度报告 (Interim) | Semi-annual | August 31 | CNINFO / SZSE / SSE |
| 季度报告 Q1 / Q3 | Quarterly | April 30 / October 31 | CNINFO / SZSE / SSE |
| 业绩预告 (Profit warning / estimate) | As triggered | Before 1 month prior to filing | Exchange announcements |
| 业绩快报 (Preliminary results) | Voluntary (most large-caps publish) | Before full annual report | Exchange announcements |
| 重大事项公告 (Material events) | As triggered | Immediately | Exchange announcements |
| 问询函 / 监管函 (Regulatory inquiry) | As triggered | Published on exchange | Exchange announcements |

Key A-share differences vs SEC:
- Quarterly reports (季报) exist but are **condensed** with limited disclosure; they are less
  detailed than SEC 10-Q filings.  Treat Q1/Q3 as preliminary indicators, not full diagnostics.
- 业绩预告 is **mandatory** for companies expecting a significant profit change
  (≥ 50% YoY or expected loss); absence of a 业绩预告 when the market expects a major swing
  is not the same as absence on SEC — check whether the company is in a mandatory-disclosure
  threshold before treating absence as a red flag.
- 问询函 (exchange inquiry letters) and company responses are publicly available; search for
  recent inquiry letters when accounting quality is in question — they often surface undisclosed
  risks that the auditor has not yet flagged.
- PRC GAAP lease accounting, fair-value marks, and goodwill impairment rules differ from IFRS
  and US GAAP; always confirm the accounting basis before peer comparisons.
- State-owned enterprises (SOEs) may have additional disclosures to SASAC; these are not always
  on exchange platforms.

---

### Disclosure Absence Rules by Market

| Market | Missing quarterly report | Missing interim report | Missing annual report |
| --- | --- | --- | --- |
| US / SEC | Red flag (NT filing required) | Not applicable | Red flag beyond deadline |
| HK / HKEX | Normal (no quarterly requirement) | Red flag if > 3 months post H1 | Red flag if > 4 months post FY |
| CN / A-share | Condensed Q1/Q3 → normal; full quarterly detail absent = normal | Red flag if > August 31 | Red flag if > April 30 |

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
