# Fictional existing-report decision brief — QHT

Illustrative workflow display of `fictional-card.json`. The ID below is a
fictional example of the exact value returned by a successful save; a real
record may cite it only after `scorecard.read_snapshot` resolves that version
under the same state home and QHT tradable line. This fixture does not save
a private record or claim that the sample ID exists.

## Mode & Inputs

- Mode: Existing Report to Action. Prior report: `fictional-report.md`, valuation as of 2026-04-01.
- Live Verification: not supplied in this fixture. Missing Inputs: current quote, next filing/event, actual portfolio and options. Execution remains conditional.

## Stale Check / Incremental Valuation Update

- The original FCFE method, adjusted per-share owner earnings, five-year horizon, and 2026-04-01 valuation date are retained. Bear 20 means supply interruption; Base 35 means stable renewals; Bull 50 means customer expansion, all USD. This display does not recalculate or reapprove them.
- The original USD 30 market price (2026-04-01), USD 35 fair value and stated 14% margin of safety are sourced from the card's price reference. Current margin and market-implied expectations need a current quote; no new fair value is made up.
- Action-Blocking Refresh Gate: Conditional only until current valuation and live data are verified under the existing workflow rules.

## Decision Brief

- Research scorecard: `2026-11-07-0123456789abcdef0123456789abcdef` (fictional exact-ID shape). Company quality uses eight independent dimension judgments with their own confidence and assessment dates; it supplies no aggregate or new stance.
- Material issue, unverified: supplier concentration may break the thesis on interruption. Verify purchasing contracts and alternate sources; this is a question, not a fraud finding.
- Material issue, confirmed: inventory writedown of USD 2 million in the fictional 2026-03-15 annual report, page 7. It lowers reported earnings quality; check subsequent provisions and sales. Its effect remains visible independently of any high dimension scores.
- Evidence gap: supplier contract and cash-flow detail are unavailable. Thesis falsifier: retention decline. Portfolio fit: insufficient information because no portfolio was provided. Execution conditions: not assessed; no decision yet.
- Prior judgment conflict: a hypothetical old `Hold` record with an older 0–5 moat assessment may sound firmer than the new card's medium-confidence industry judgment. The older moat score measures its legacy valuation input; the new dimension asks about industry economics. Review supply discipline and retention evidence before interpreting the discrepancy; neither score is converted into the other or silently substituted in valuation.
- Candidate Tier, Valuation Zone, Action allowed: withheld pending current upstream analysis, live verification and portfolio inputs. No score-driven trade rule is inferred.

## Execution Sheet / Decision Record

- No concrete order, size, option terms or execution method is produced from this fixture. No `decision-record/v1` record is written without a supported stance. A separate completed research run can still save its card independently.
- If a later supported decision cites a real saved version, its record keeps `(symbol, date, mode)` identity, sets `scorecard_snapshot_id` to that exact ID, and retains the prior valuation fields and scenario meanings unless a separately justified valuation update occurs.

## Fixture review

Checked against `fictional-card.json`: both material issues retain status,
impact and verification; the inventory fact is dated and sourced; the supplier
contract and cash-flow gap remains explicit; original valuation method, basis,
horizon and scenario meanings are preserved. The old stance/score is labeled
hypothetical and its difference is explained as a review question. This is a
content review of fictional output, not evidence of live model behavior.
