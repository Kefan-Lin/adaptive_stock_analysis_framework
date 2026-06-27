"""Inflection Discovery — upstream discovery stage for the adaptive stock
analysis framework.

Surfaces companies at an earnings or narrative inflection (depressed base +
turning second derivative) and routes candidates into `analyzing-stocks`.

Layout:
  config.py         shared constants (cache dir, SEC user-agent, rate limits)
  edgar.py          SEC EDGAR client (CIK map, companyfacts, submissions)
  pit/              point-in-time reconstruction (prices, fundamentals, text, universe)
  scorecard/        the A/B/C/D taxonomy + scoring (shared IP)
  contract.py       candidate contract dataclass + validator
  routing.py        hand-off adapter to analyzing-stocks
  harness/          backtest runner, metrics, canary battery
  engine_b/         code-first Inflection Score pipeline (Implementation B)
  benchmark/        labeled (ticker, as-of, label) dataset + loader
"""

__version__ = "0.1.0"
