---
schema: decision-record/v1
symbol: ACME
market: US
date: 2026-07-01
mode: position-review
price_at_decision: 110.0
currency: USD
stance: Hold
position_size: Starter
confidence: Medium
weighted_fair_value: 140
scenarios: {bear: 80, base: 135, bull: 190}
candidate_tier: Core Candidate
valuation_zone: Hold
execution_method: No Action
triggers:
  add_on:
    - {type: price, level: 90, direction: below}
  trim_exit:
    - {type: price, level: 185, direction: above}
next_earnings: 2026-08-20
review_by: 2026-10-01
related_symbols: [1234.HK]
source_report: null
action_taken: null
---

# ACME — position review (fixture)

Fictional record body.
