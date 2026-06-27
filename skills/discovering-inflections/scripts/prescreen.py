#!/usr/bin/env python
"""Stage-1 broad pre-screen for Implementation A.

Filters a universe to the depressed base (the A hard gate) with reconstructable
point-in-time data, so the LLM only spends judgment on plausible turnarounds.

Usage:
  prescreen.py --as-of 2024-06-30 [--tickers file.txt] [--limit 50] [--sample 150]

With --tickers, screens that list; otherwise screens a random sample of the SEC
universe (a stand-in for a sector/theme/screener-export seed in live use).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# allow running as a script from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from inflection_discovery.pit.prices import pit_prices  # noqa: E402
from inflection_discovery.pit.universe import random_control_tickers  # noqa: E402
from inflection_discovery.scorecard.score import score_A  # noqa: E402
from inflection_discovery.pit.fundamentals import pit_fundamentals  # noqa: E402


def screen(tickers, as_of, limit):
    out = []
    for t in tickers:
        try:
            p = pit_prices(t, as_of)
            if p is None or p.empty or len(p) < 60:
                continue
            a = score_A(p)
            if not a["gate"]:
                continue
            f = pit_fundamentals(t, as_of)
            if not f.available:
                continue
            out.append((t, a["score"], a["evidence"][0]))
        except Exception:
            continue
        if len(out) >= limit:
            break
    out.sort(key=lambda r: r[1], reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", required=True)
    ap.add_argument("--tickers", default=None, help="newline-delimited ticker file")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--sample", type=int, default=150)
    args = ap.parse_args()

    if args.tickers:
        tickers = [l.strip().upper() for l in Path(args.tickers).read_text().splitlines() if l.strip()]
    else:
        tickers = random_control_tickers(args.sample)

    rows = screen(tickers, args.as_of, args.limit)
    print(f"Depressed-base longlist @ {args.as_of} ({len(rows)} names):")
    for t, a, ev in rows:
        print(f"  {t:6} A={a:.2f}  {ev}")


if __name__ == "__main__":
    main()
