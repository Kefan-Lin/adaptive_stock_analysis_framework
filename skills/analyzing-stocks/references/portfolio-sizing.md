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
- Liquidity passes the execution gate below
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

## Execution Liquidity Gate

Check the actual tradable line, not just the company-level market cap.

- `Average daily traded value` over the last 20 trading days:
  - `>= USD 25m` or local-currency equivalent: eligible for `Core` if other requirements are met
  - `USD 5m - 25m`: usually caps the position at `Starter`
  - `< USD 5m`: downgrade one tier automatically
  - `< USD 1m` or frequent zero-volume days: default to `Speculative` or `Watch-Avoid`
- Typical `bid-ask spread`:
  - `<= 0.50%`: acceptable for normal sizing
  - `0.51% - 1.50%`: downgrade one tier
  - `> 1.50%`: no `Core`; consider `Speculative` unless the thesis is exceptionally strong and size is small
- `low-turnover` names, especially those with episodic liquidity, should be treated as one tier worse than market cap alone suggests.

## Auto-Downgrade Rules

Downgrade one tier automatically if:
- The industry is biotech, early-stage growth infra, micro-cap resource, or distressed turnaround
- Current data quality is incomplete
- Thesis depends mainly on fast variables rather than invariants
- The tradable line is an `ADR` with materially worse liquidity than the primary listing
- The name is `micro-cap` or effectively micro-cap in free float / execution terms
- The order would likely move the market because of low depth or wide spreads

Downgrade two tiers or block `Core` outright if:
- The tradable line combines `low-turnover` with a persistently wide `bid-ask spread`
- Settlement, capital-control, or local-market frictions make exits materially harder than entries

## Trigger Format

Always output:
- `Add-on Trigger`: the condition that upgrades conviction or size
- `Trim/Exit Trigger`: the condition that reduces conviction or breaks the thesis

## Required Output Block

Include:
1. Position size tier
2. Size range
3. Why the name qualifies for that tier
4. Tradable line, liquidity tier, and spread assessment
5. Add-on trigger
6. Trim/exit trigger
