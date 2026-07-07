"""Known-dead tickers whose provider series can no longer realize the loss.

yfinance re-anchors recycled tickers to the current live entity and DROPS the
delisted leg entirely (verified 2026-07-07 on BBBY/HTZ/SPCE/SHLD: BBBY's
24-year "history" bottoms at $2.65 — the 2023 collapse to pennies is gone).
No series-shape detector can recover a leg the source deleted, so deaths are
recorded as explicit curated facts, same class as the benchmark labels.
Forward-looking use only (a death date is post-T information, which
forward_return legitimately uses); pit_prices never consults this.

Semantics of an entry, as consumed by forward_return:
- death_date: the day the ticker symbol stopped referencing the old entity
  (delisting / ticker reassignment). From that day on, provider prices under
  the symbol are someone else's; windows reaching it realize terminal_value,
  windows ending before it use the normal path, and a T on/after it returns
  None (the old entity did not exist at T).
- terminal_value: curated recovery per share to the old common (0.0 when the
  confirmed plan cancelled the equity with zero recovery).
"""

DEAD_TICKERS = {
    # Bed Bath & Beyond: Ch.11 filed 2023-04-23; Nasdaq delisting ended the
    # BBBY listing 2023-05-03 (the claim continued OTC as BBBYQ); the confirmed
    # plan cancelled the common with zero recovery, effective 2023-09-30.
    # death_date is the delisting — from then on "BBBY" no longer references
    # the old entity — and the zero-recovery plan fixes terminal_value at 0.
    "BBBY": {
        "death_date": "2023-05-03",
        "terminal_value": 0.0,
        "note": "Ch.11 2023-04-23; delisted 2023-05-03 (continued OTC as "
                "BBBYQ); common cancelled 2023-09-30 with zero recovery; "
                "ticker later recycled",
    },
}
