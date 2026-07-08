# Macro Overlay

## Objective

Provide a text-first, regime-aware adjustment layer so that key valuation inputs
(discount rate, terminal growth, working-capital assumptions) reflect the macro
environment at the time of the report.
This file does not require real-time data feeds.  The analyst asserts the current
regime based on available public information, then applies the adjustment rules below.

Constraint: Keep the framework text-first and repository-local; do not add market-data
dependencies to enforce these adjustments.

## How to Use

1. Identify the current regime for each of the four dimensions (Rates, Inflation, FX, Commodity).
2. Apply the adjustments in Sections 2–5 to the relevant valuation inputs.
3. Note the regime assessment and any adjustments in Section 10.4 (Evidence Ledger) of the report.
4. If two or more dimensions are in a stress regime simultaneously, apply the adjustments
   independently and note the combined effect in the valuation assumptions table (Section 7.1).

## 1) Rate Regime

Assess the direction of policy rates at the time of the report:

| Regime | Signal | Effect on discount rate |
| --- | --- | --- |
| `Falling` | Central bank cutting or signaling imminent cuts; long-end yields declining | Reduce WACC / cost of equity by 50–100 bps vs the 5-year average |
| `Neutral` | Policy rates stable; market pricing 0–1 cuts in 12 months | Use trailing 5-year average WACC as baseline |
| `Rising` | Central bank hiking or rates above 5-year average by 100+ bps | Add 50–150 bps to WACC vs baseline |
| `Elevated / Plateau` | Rates near cycle peak, market pricing cuts 12–24 months out | Use current rate level but widen the valuation band |

**Per-family adjustments:**
- **Operating companies (DCF):** Apply the rate regime adjustment to WACC directly.
- **Banks / insurers:** A rising-rate regime expands NIM (positive) but also raises credit risk
  (negative offset); note the net sign rather than a simple WACC adjustment.
- **Real estate (NAV / cap-rate):** Rising rates expand cap rates; for every 100 bps of rising-rate
  regime, add 25–50 bps to the cap-rate assumption in the Bear scenario.
- **Biotech (rNPV):** Discount rate for terminal value is rate-sensitive; in rising-rate regime,
  add 50–100 bps to the rNPV discount rate.
- **Regulated utilities / telecom (DDM / DCF):** Allowed ROE often lags rate moves by 1–2 years;
  note the regulatory lag in the assumption table.

**Floor interaction:** these regime adjustments apply on top of the discount-rate build
in `value-investing-lens.md` (§3 Discount Rate Construction) and
**may not breach the discount-rate floor** (risk-free + 300 bps for equities). A
`Falling`-rate cut that would push the rate below the floor is capped at the floor.

## 2) Inflation Regime

| Regime | Signal | Key adjustments |
| --- | --- | --- |
| `Low / Anchored` | Headline CPI < 3%, stable expectations | Standard cost and revenue growth assumptions |
| `Moderate` | CPI 3–5%, partially transmitted to input costs | Add 50–100 bps to cost CAGR; check pricing-power evidence before passing through |
| `High / Unanchored` | CPI > 5% or expectations de-anchored | Explicitly model cost pass-through lag; stress-test margin compression in Bear scenario |

**Per-family adjustments:**
- **Operating companies:** Apply cost-inflation stress in Bear scenario if inflation is `High`.
  Test whether the business has pricing power (moat section score ≥ 3 on intangibles or switching cost)
  before assuming full pass-through in Base.
- **Real estate:** High inflation is typically positive for replacement-cost NAV and rent resets
  (where leases have CPI linkage); note this in the Bull scenario assumption.
- **Banks / insurers:** Moderate inflation may support higher nominal loan growth; high inflation
  raises credit risk and loss provisions; note in diagnostics.
- **Commodity producers:** Inflation is often correlated with commodity prices; cycle-position
  overlay from `industry-playbooks.md` takes precedence.

## 3) FX Regime

Assess the direction of the most relevant currency pair for the name being analyzed:

| Regime | Signal | Adjustment |
| --- | --- | --- |
| `Home-currency strengthening` | USD/EUR/CNY appreciating vs revenue currencies | Reduce reported-currency revenue growth by FX drag estimate |
| `Home-currency weakening` | USD/EUR/CNY depreciating | Potential FX tailwind; verify whether costs are also in the same currency |
| `Volatile / uncertain` | > 10% FX move in trailing 12 months | Widen revenue range in Bear/Bull; note hedging policy from filing |

**Currency normalization rule (cross-name comparisons):**
When comparing names with different reporting currencies or running a multi-name portfolio analysis,
state the reporting currency, the period-average and period-end FX rates used, and the USD-equivalent
key metrics.  Use **period-average** rates for income statement items (revenue, EBITDA, net income)
and **period-end** rates for balance-sheet items (debt, book value, cash).
Do not mix rate types within the same line item.
Document this in Section 10.4 (Evidence Ledger) as an Assumption with the source.

**Cross-listed names (also covered in `source-policy.md`):**
When the tradable line is an ADR or a dual-listed H-share, verify that FX assumptions are
applied to the *primary reporting currency*, not the trading currency of the tradable line.

## 4) Commodity Cycle Regime

Use only for names with primary exposure to a commodity price (resource, energy, materials sector).
For all other sectors, skip this section.

| Regime | Signal | Adjustment |
| --- | --- | --- |
| `Trough` | Price below marginal cost; producers cutting capex | Use trough price in Bear; mid-cycle in Base; recovery in Bull |
| `Mid-cycle` | Price near long-run incentive cost | Use mid-cycle in Base; ±20% in Bear/Bull |
| `Peak` | Price materially above marginal cost; new capacity entering | Use peak in Bull; mid-cycle in Base; trough in Bear |
| `Transitional` | Structural shift (energy transition, new technology) altering cost curve | Explicitly model two sub-scenarios: old-cycle and new-cycle |

This section cross-references the `Cyclical Asset Producer` archetype in `industry-playbooks.md`.

## 5) Combined Stress Scenario

If two or more dimensions are simultaneously in a `stress` regime (Rising rates + High inflation +
Home-currency weakening + Commodity trough), run a **combined macro stress** scenario:
- In the Bear scenario, stack all stress adjustments simultaneously.
- Label this scenario explicitly: `Bear (macro stress)`.
- Compare the combined Bear fair value to current price; if the combined Bear value is below
  current price, the margin of safety is negative at macro-stress — note in Section 9.0
  Red-Team Gate.

## 6) Required Output Block

At the top of Section 7.1 (Valuation Assumptions Table), include a one-line macro regime
summary before the scenario table:

```
Macro regime: Rates [Falling/Neutral/Rising/Elevated], Inflation [Low/Moderate/High],
FX [direction for key pair], Commodity [applicable / not applicable]
Regime adjustments applied: [list adjustments made, or "none"]
```
