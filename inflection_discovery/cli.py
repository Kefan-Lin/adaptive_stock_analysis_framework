"""CLI: canary battery, backtest, or live discovery.

  python -m inflection_discovery.cli canary
  python -m inflection_discovery.cli backtest --top-n 10 [--with-text] [--out results.json]
  python -m inflection_discovery.cli discover --tickers BILI,NOK,MU      # live (non-PIT)
  python -m inflection_discovery.cli ashare-backtest                     # China A-share PIT
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .harness import run_backtest, summarize, run_battery


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["backtest", "canary", "discover", "ashare-backtest"])
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--with-text", action="store_true")
    ap.add_argument("--control-keep", type=int, default=30)
    ap.add_argument("--tickers", default="", help="comma-separated, for discover")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.cmd == "canary":
        ok = True
        for r in run_battery():
            print(("PASS" if r["passed"] else "FAIL"), r["name"], "::", r["detail"])
            ok = ok and r["passed"]
        return 0 if ok else 1

    if a.cmd == "discover":
        from .live.discover import discover_live
        tickers = [t.strip().upper() for t in a.tickers.split(",") if t.strip()]
        eligible, _ = discover_live(tickers, top_n=a.top_n, with_text=a.with_text)
        print("LIVE discovery (NON-PIT). Ranked eligible candidates:")
        for c in eligible[: a.top_n]:
            s = c.scores
            print(f"  #{c.rank} {c.ticker:6} D={s['D']:.2f} A={s['A']:.2f} "
                  f"B={'NA' if s['B'] is None else round(s['B'],2)} "
                  f"C={'NA' if s['C'] is None else round(s['C'],2)} | {c.evidence['source'][0]}")
        return 0

    if a.cmd == "ashare-backtest":
        from .ashare.backtest import run_ashare_backtest
        print(json.dumps(run_ashare_backtest(), default=str, indent=2))
        return 0

    res = run_backtest(top_n=a.top_n, with_text=a.with_text, control_keep=a.control_keep)
    summ = summarize(res)
    if a.out:
        Path(a.out).write_text(json.dumps({"summary": summ, "raw": res}, default=str, indent=2))
    print(json.dumps(summ, default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
