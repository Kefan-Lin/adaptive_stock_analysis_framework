"""LIVE-mode data sources and discovery (NOT point-in-time).

These modules power live discovery, where using current/as-reported data is fine.
They are deliberately separate from the PIT backtest path and must never be
imported by it.

- `akshare_source` — US/ADR/foreign quarterly fundamentals via akshare
  (Eastmoney). NON-PIT (period-end only, no announcement date) -> forbidden in
  the backtest; fills the foreign-filer gap (BILI, NOK) for live use.
- `akshare_ashare` — China A-share data. This one IS point-in-time-capable
  because A-share earnings carry an announcement date (最新公告日期).
- `discover` — the live discovery entrypoint.
"""
