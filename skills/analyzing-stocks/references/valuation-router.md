# Valuation Router

## Objective

Match valuation method to industry economics instead of defaulting to one generic DCF template.

## Routing Table

| Skill | Primary method | Secondary method | Key decision variables |
| --- | --- | --- | --- |
| `$analyzing-software-platforms` | FCFF DCF | EV/EBIT or P/E | ARR, NRR, FCF conversion, SBC |
| `$analyzing-consumer-retail` | FCFE or DCF | EV/EBIT or P/E | same-store sales, gross margin, inventory, cash conversion |
| `$analyzing-industrials-transport` | Through-cycle DCF | EV/EBITDA | backlog, utilization, service mix, capex |
| `$analyzing-semiconductors-hardware` | Through-cycle DCF | EV/Sales or EV/EBITDA | utilization, ASP, yield, mix, capex intensity |
| `$analyzing-resource-energy-materials` | Mid-cycle DCF or NAV | EV/resource or EV/EBITDA | realized price, cost curve, reserve life, cycle position |
| `$analyzing-banks` | P/TBV with ROTE/Gordon logic | P/E | NIM, credit cost, CET1, ROTCE |
| `$analyzing-insurers` | P/B with excess capital | Dividend-based or earnings yield | combined ratio, float, reserves, solvency |
| `$analyzing-real-estate` | NAV | FFO/AFFO multiple | occupancy, lease rollover, LTV, debt ladder |
| `$analyzing-healthcare-biotech` | SOTP or rNPV | Peer multiple | pipeline probability, peak sales, runway, dilution |
| `$analyzing-utilities-telecom` | DCF or DDM | EV/EBITDA | regulated return, asset base, ARPU, churn, dividend cover |
| Conglomerate / holding company (multi-segment, no dominant engine) | Sum-of-parts (SOTP) | Per-segment family + holdco bridge | segment value, holdco net debt, central cost, holding-company discount |

## Hard Rules

1. Banks and insurers must not be valued with generic enterprise DCF as the only method.
2. Commodity or cyclical businesses must use mid-cycle or through-cycle normalization.
3. Biotech and similar asset portfolios must probability-adjust asset values.
4. Asset-heavy real estate must anchor on NAV or FFO/AFFO logic.
5. Genuine multi-segment conglomerates and holding companies must use sum-of-parts: value each
   material segment with its own family, then net holdco items and any holding-company discount.

## Required Output Block

Include:
1. Chosen primary method with reason
2. Chosen secondary method with reason
3. Why the method matches industry economics
4. Main assumptions that drive value
