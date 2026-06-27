"""CLI: run the canary battery or the backtest.

  python -m inflection_discovery.cli canary
  python -m inflection_discovery.cli backtest --top-n 10 [--with-text] [--out results.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .harness import run_backtest, summarize, run_battery


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["backtest", "canary"])
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--with-text", action="store_true")
    ap.add_argument("--control-keep", type=int, default=30)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.cmd == "canary":
        ok = True
        for r in run_battery():
            print(("PASS" if r["passed"] else "FAIL"), r["name"], "::", r["detail"])
            ok = ok and r["passed"]
        return 0 if ok else 1

    res = run_backtest(top_n=a.top_n, with_text=a.with_text, control_keep=a.control_keep)
    summ = summarize(res)
    if a.out:
        Path(a.out).write_text(json.dumps({"summary": summ, "raw": res}, default=str, indent=2))
    print(json.dumps(summ, default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
