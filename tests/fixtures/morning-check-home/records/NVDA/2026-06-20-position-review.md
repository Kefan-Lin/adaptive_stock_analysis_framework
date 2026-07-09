---
schema: decision-record/v1
symbol: NVDA
market: US
date: 2026-06-20
mode: position-review
price_at_decision: 145.0
currency: USD
stance: Hold
position_size: Core
confidence: Medium
weighted_fair_value: 160
scenarios: {bear: 100, base: 155, bull: 210}
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: Sell cash-secured put
triggers:
  add_on:
    - {type: price, level: 120, direction: below}
next_earnings: 2026-07-11
review_by: 2026-09-30
source_report: null
action_taken: null
---

# NVDA — position review (fixture)

Fictional self-contained decision record for tests.
