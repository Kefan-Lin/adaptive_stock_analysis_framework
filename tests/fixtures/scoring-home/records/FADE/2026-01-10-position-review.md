---
schema: decision-record/v1
symbol: FADE
market: US
date: 2026-01-10
mode: position-review
price_at_decision: 200.0
currency: USD
stance: Reduce
position_size: Core
confidence: Medium
weighted_fair_value: 150
scenarios: {bear: 120, base: 160, bull: 210}
candidate_tier: Tactical Candidate
valuation_zone: Exhaustion
execution_method: Reduce
triggers:
  trim_exit:
    - {type: price, level: 205, direction: above}
next_earnings: null
review_by: 2026-06-01
source_report: null
action_taken: null
---

# FADE — position review (fixture)

Fictional self-contained decision record for tests.
