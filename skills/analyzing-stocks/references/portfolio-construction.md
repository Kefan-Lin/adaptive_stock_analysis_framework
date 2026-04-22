# Portfolio Construction

## Objective

Translate per-name sizing recommendations from `portfolio-sizing.md` into
portfolio-level discipline by checking sector concentration, correlation,
and factor tilt before confirming a position size.
This file addresses the gap between "this name is Core-quality" and
"I can actually size it Core given what else is in the portfolio."

## When to Use

After completing per-name sizing in Section 9 of the report template,
run the three checks below if the recommended tier is `Core` or if the
portfolio already has material exposure to the same sector or KPI driver.
For `Starter` and `Speculative` names, these checks are advisory.

## Check 1: Sector Concentration

| Sector / industry skill | Default soft cap | Hard cap |
| --- | --- | --- |
| Software platforms | 25% | 35% |
| Financials (banks + insurers combined) | 25% | 35% |
| Healthcare + biotech | 20% | 30% |
| Real estate (REITs + developers) | 15% | 25% |
| Resources, energy, materials | 20% | 30% |
| Industrials + transport | 20% | 30% |
| Semiconductors + hardware | 20% | 30% |
| Consumer + retail | 20% | 30% |
| Utilities + telecom | 15% | 25% |

Rules:
- If adding this position would push the sector above the **soft cap**, downgrade
  the position one tier (e.g., Core → Starter).
- If adding this position would push the sector above the **hard cap**, cap the
  position at `Starter` regardless of per-name conviction.
- If the portfolio is concentrated (fewer than 10 names total), tighten all
  sector caps by 5 percentage points.

## Check 2: KPI-Driver Correlation

Two names are considered **high-correlation** if they share the same primary KPI driver
— use the KPI tree from each report's Section 3 to identify the driver.

Common high-correlation pairs:
- Two software platforms both driven by ARR / NRR: high correlation
- Two commodity producers driven by the same commodity price: high correlation
- A bank and an insurer both driven by credit spreads: moderate-to-high correlation
- A REIT and a homebuilder both driven by cap rates and credit: moderate correlation

Rule:
- If the new name has **high correlation** with a name already at `Core` size,
  cap the new name at `Starter` unless the combined weight would still leave
  the two names below 12% of the portfolio.
- If the new name has **moderate correlation** with a `Core` name, the per-name
  sizing from `portfolio-sizing.md` stands, but document the correlation pair
  in the sizing rationale.

## Check 3: Factor Tilt

Classify each name into one or more factor buckets at time of purchase:

| Factor | Signal |
| --- | --- |
| `Value` | Margin of safety ≥ 25%, P/E or P/TBV below sector median |
| `Quality` | Financial quality score ≥ 4.0, moat verdict Strong or Defendable |
| `Growth` | Revenue CAGR above sector median and reinvestment runway intact |
| `Momentum` | Price 3M and 12M above sector median (note: not a value-investing signal) |
| `Defensive` | Regulated or contracted cash flows, low cyclicality |

Portfolio-level guidance:
- Avoid having more than 60% of the portfolio in a single factor at any time.
- A portfolio with 50%+ `Growth` factor exposure is vulnerable to rate re-rating;
  note this when interest-rate risk is elevated (from `macro-overlay.md` if present).
- `Momentum` alone without `Value` or `Quality` support does not meet the
  value-investing discipline of this framework — flag as advisory only.

## Check 4: Geographic / Currency Concentration

- If more than 40% of portfolio revenue is from a single currency (USD, CNY, EUR),
  note the FX concentration and whether the portfolio is adequately diversified.
- If more than 30% of portfolio revenue is from a single country (not home market),
  flag geopolitical concentration and cross-reference `risk-register.md` bucket 8.

## Required Output Block

When running portfolio construction checks for a new name, include:

1. Sector weight before and after adding this name
2. Sector cap status: `below soft cap / approaching soft cap / at hard cap`
3. Highest-correlation existing holding and the shared KPI driver
4. Primary factor bucket(s) for this name
5. Portfolio-level factor tilt after adding this name
6. Final confirmed tier after portfolio checks (may differ from per-name recommendation)
7. Rationale if tier was adjusted by portfolio constraints

## Integration Points

- Upstream: `portfolio-sizing.md` sets the per-name tier; this file adjusts for portfolio context.
- Upstream: `risk-register.md` bucket 8 (geopolitical/FX) feeds Check 4.
- Upstream: `macro-overlay.md` (when present) informs factor-tilt sensitivity in Check 3.
- Downstream: Section 9.1 of `report-template.md` records the final confirmed tier and rationale.
