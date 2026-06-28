# akshare Integration & A-share Variant

**Date:** 2026-06-28 · Added after evaluating whether [akshare](https://github.com/akfamily/akshare)
could fill the project's data gaps. Env is now uv-managed (`pyproject.toml` + `uv.lock`).

## What akshare can and cannot do for us (verified empirically)

| Need | akshare? | Evidence |
|---|---|---|
| US/ADR/foreign **quarterly** fundamentals (coverage) | ✅ yes | `stock_financial_us_report_em` returns standardized quarterly statements for BILI (37q), NOK (85q), etc. — fills the gap the SEC us-gaap/ifrs pipeline left (BILI annual-only, NOK no quarterly XBRL). |
| US **point-in-time** backtest | ❌ no | returns only `REPORT_DATE` (period end), no announcement/filing date; values current-restated → same look-ahead as yfinance fundamentals. SEC EDGAR remains the only free US PIT source. |
| **A-share** fundamentals (coverage) | ✅ yes | `stock_financial_abstract_ths(按单季度)` gives per-stock quarterly revenue/YoY/gross-margin/inventory-days. |
| **A-share point-in-time** backtest | ❌ no (corrected) | `stock_yjbb_em` 最新公告日期 is the **latest** disclosure date, not the original announcement: for a 2021-Q1 snapshot **97% of rows show 2022 dates** (re-disclosed by the annual report) and values are restated. So A-share fundamentals also can't be reconstructed as-originally-filed on free data. |
| Analyst **estimate-revision** PIT history | ❌ no | `stock_profit_forecast_em` is a current consensus snapshot, no historical time-series. |

**Bottom line:** akshare is excellent for **coverage and LIVE discovery** (US/ADR/
foreign + the entire A-share market, free), but it does **not** provide clean
point-in-time data for *any* market — so it does not enable a generalizable
backtest. That still needs a paid point-in-time dataset. (hfq A-share prices *are*
PIT-safe, but with restated fundamentals a price-only backtest isn't worth much.)

## What was built

### #1 — akshare LIVE coverage for US/ADR/foreign names
- `inflection_discovery/live/akshare_source.py` — `live_fundamentals(ticker)` builds
  the standard `Fundamentals` from akshare's US statements.
- `inflection_discovery/live/discover.py` — `discover_live(tickers)` / `score_one_live`:
  SEC us-gaap/ifrs when it has ≥4 quarters, else akshare fallback; prices from
  yfinance; C from filings. **LIVE only, walled off from the PIT backtest.**
- CLI: `python -m inflection_discovery.cli discover --tickers BILI,NOK,MU`
- Result: BILI now scores **B=0.54** (was NA via SEC-only); NOK gets full B +
  inventory. In a live run today only BILI surfaces (the others aren't depressed now).

### #2 — China A-share LIVE discovery variant
- `inflection_discovery/ashare/data.py` — `ashare_prices` (hfq) + `ashare_fundamentals`
  (THS per-stock quarterly).
- `inflection_discovery/ashare/discover.py` — `discover_ashare(codes)`: A from hfq
  prices (reuses `score_A`), B from precomputed YoY/margin/inventory-days, a light
  secular ¬trap. **LIVE only** (PIT not free-achievable, per the correction above).
- CLI: `python -m inflection_discovery.cli ashare-discover --tickers 601919,002594`
- Demo: surfaces depressed turnarounds (BYD `002594` A=0.84, Seres `601127` A=1.00);
  the A gate correctly filters non-depressed names (Maotai, Cambricon).

## Honesty note
My initial akshare assessment over-claimed an "A-share PIT" capability. On
verification, akshare's announcement dates are latest-revision and its values are
restated, so A-share is LIVE-only like the US path. This is documented rather than
papered over, consistent with the rest of the project's discrimination-probe framing.

## Tests
131 pass (uv-managed Python 3.12 / pandas 3.0). New: `tests/test_live_akshare.py`,
`tests/test_ashare.py`. The 4-canary PIT leak battery still guards the US backtest.
