# Portfolio Sizing

## Objective

Convert research conviction into a disciplined position-size recommendation.

## Tier Definitions

| Tier | Size | Default use |
| --- | --- | --- |
| `Core` | `6% - 10%` | High-quality, high-conviction, strong downside protection |
| `Starter` | `2% - 5%` | Thesis works but timing, catalyst, or uncertainty is not fully resolved |
| `Speculative` | `0.5% - 2%` | High uncertainty, financing risk, turnaround risk, or binary outcomes |
| `Watch-Avoid` | `0%` | No entry, or exit/reduce only |

## Allocation Rules

### Core

Require all of:
- Financial quality is high
- Confidence is high
- Margin of safety is at least `25%`
- Liquidity is acceptable
- No severe value-trap flags

### Starter

Use when:
- The thesis is credible
- Margin of safety exists but is not wide enough for `Core`
- Catalysts or execution timing remain uncertain

### Speculative

Use when any of these dominate:
- Cash runway or refinancing risk
- Binary regulatory, clinical, or project outcomes
- Turnaround depends on execution that is not yet proven
- Dilution is likely

### Watch-Avoid

Use when any of these hold:
- No meaningful margin of safety
- Two or more severe value-trap failures
- Downside is hard to bound
- Financial quality is weak

## Auto-Downgrade Rules

Downgrade one tier automatically if:
- The industry is biotech, early-stage growth infra, micro-cap resource, or distressed turnaround
- Current data quality is incomplete
- Thesis depends mainly on fast variables rather than invariants

## Trigger Format

Always output:
- `Add-on Trigger`: the condition that upgrades conviction or size
- `Trim/Exit Trigger`: the condition that reduces conviction or breaks the thesis

## Required Output Block

Include:
1. Position size tier
2. Size range
3. Why the name qualifies for that tier
4. Add-on trigger
5. Trim/exit trigger
