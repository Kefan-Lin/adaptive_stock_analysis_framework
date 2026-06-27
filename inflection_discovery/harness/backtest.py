"""Point-in-time backtest harness for Implementation B.

For each benchmark name we reconstruct the as-of-T universe (a random
depressed-base control arm + the name) and ask whether the name ranks into the
top-N by D. Metrics are reported with n and Wilson CIs against the control arm.
This is a discrimination probe, not a generalizable accuracy estimate.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional, Sequence

import pandas as pd

from ..config import CACHE_DIR
from ..benchmark import load_benchmark, BenchmarkRow
from ..engine_b import score_universe
from ..pit.prices import forward_return
from ..pit.universe import data_available, random_control_tickers
from .metrics import mean, wilson


def build_control_universe(
    n_sample: int = 140, keep: int = 30, ref_date: str = "2023-06-30",
    exclude: Sequence[str] = (), seed: int = 42,
) -> List[str]:
    """Random operating companies with reconstructable data — the unbiased arm.

    Cached to disk so re-runs are stable and cheap. Survivorship caveat: sampled
    from the current SEC ticker map, so it cannot include pre-today delistings
    (documented in the spec); the curated delisted negatives test that path.
    """
    cache = CACHE_DIR / f"control_universe_{keep}_{seed}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out: List[str] = []
    for t in random_control_tickers(n_sample, seed=seed, exclude=exclude):
        try:
            if data_available(t, ref_date):
                out.append(t)
        except Exception:
            pass
        if len(out) >= keep:
            break
    cache.write_text(json.dumps(out))
    return out


def evaluate_row(row: BenchmarkRow, control: Sequence[str], top_n: int,
                 with_text: bool) -> Dict:
    out = {
        "ticker": row.ticker, "label": row.label, "type": row.inflection_type,
        "notes": row.notes, "dates": [], "no_data": True,
    }
    hit_date = row.hit_date()
    for dt in row.as_of_dates():
        universe = list(control) + [row.ticker]
        eligible, scored = score_universe(universe, dt, top_n=top_n, with_text=with_text)
        had_data = any(c.ticker == row.ticker for c in scored)
        self_c = next((c for c in scored if c.ticker == row.ticker), None)
        topn = eligible[:top_n]
        in_top = any(c.ticker == row.ticker for c in topn)
        rank = next((c.rank for c in topn if c.ticker == row.ticker), None)
        out["dates"].append({
            "as_of": str(pd.Timestamp(dt).date()),
            "is_hit_date": hit_date is not None and pd.Timestamp(dt) == pd.Timestamp(hit_date),
            "in_topN": in_top,
            "rank": rank,
            "eligible_n": len(eligible),
            "gate": bool(self_c.passes_A_gate) if self_c else None,
            "scores": self_c.scores if self_c else None,
        })
        out["no_data"] = out["no_data"] and (not had_data)
    return out


def run_backtest(top_n: int = 10, with_text: bool = False,
                 control_keep: int = 30) -> Dict:
    rows = load_benchmark()
    bench_tickers = {r.ticker for r in rows}
    control = build_control_universe(keep=control_keep, exclude=bench_tickers)
    evals = [evaluate_row(r, control, top_n, with_text) for r in rows]
    return {
        "top_n": top_n, "with_text": with_text,
        "control_universe": control, "control_n": len(control),
        "rows": evals,
    }


def summarize(results: Dict) -> Dict:
    rows = results["rows"]
    control = results["control_universe"]
    top_n = results["top_n"]

    def find(label):
        return [r for r in rows if r["label"] == label]

    # --- positives: hit at the fixed hit-date; lead from earliest in-topN ---
    pos = find("positive")
    pos_with_data = [r for r in pos if not r["no_data"]]
    hits, leads = 0, []
    pos_detail = []
    for r in pos_with_data:
        hit_day = next((d for d in r["dates"] if d["is_hit_date"]), None)
        is_hit = bool(hit_day and hit_day["in_topN"])
        hits += 1 if is_hit else 0
        # lead: earliest as-of (largest months before t_star) that was in topN
        in_dates = [d for d in r["dates"] if d["in_topN"]]
        lead_m = None
        if in_dates:
            earliest = min(pd.Timestamp(d["as_of"]) for d in in_dates)
            # months before the last (closest) date which is ~ t_star - 1mo
            ref = max(pd.Timestamp(d["as_of"]) for d in r["dates"])  # t_star - 1mo
            lead_m = round((ref - earliest).days / 30.0) + 1
            leads.append(lead_m)
        pos_detail.append({"ticker": r["ticker"], "type": r["type"],
                           "hit": is_hit, "lead_months": lead_m})

    # --- negatives: trap if in topN at ANY tested date ---
    neg = find("negative")
    neg_with_data = [r for r in neg if not r["no_data"]]
    traps = sum(1 for r in neg_with_data if any(d["in_topN"] for d in r["dates"]))
    neg_detail = [{"ticker": r["ticker"], "type": r["type"],
                   "trap": any(d["in_topN"] for d in r["dates"])}
                  for r in neg_with_data]

    # --- controls (plumbing): must NOT appear ---
    ctrl = find("control")
    ctrl_detail = [{"ticker": r["ticker"],
                    "appeared": any(d["in_topN"] for d in r["dates"]),
                    "no_data": r["no_data"]} for r in ctrl]
    border = [{"ticker": r["ticker"],
               "in_topN": any(d["in_topN"] for d in r["dates"]),
               "gate": (r["dates"][0]["gate"] if r["dates"] else None),
               "no_data": r["no_data"]} for r in find("borderline")]

    excluded = [r["ticker"] + " (" + r["label"] + ")" for r in rows if r["no_data"]]

    # --- forward return: hits vs control base rate (6 & 12 mo) ---
    def fwd(tkrs_dates, months):
        vals = [forward_return(t, d, months) for t, d in tkrs_dates]
        return mean(vals)

    hit_picks = []
    for r in pos_with_data:
        hd = next((d for d in r["dates"] if d["is_hit_date"] and d["in_topN"]), None)
        if hd:
            hit_picks.append((r["ticker"], hd["as_of"]))
    base_date = "2023-06-30"
    picks_fwd6 = fwd(hit_picks, 6)
    picks_fwd12 = fwd(hit_picks, 12)
    ctrl_fwd6 = mean([forward_return(t, base_date, 6) for t in control])
    ctrl_fwd12 = mean([forward_return(t, base_date, 12) for t in control])

    n_pos = len(pos_with_data)
    n_neg = len(neg_with_data)
    return {
        "top_n": top_n,
        "control_n": len(control),
        "positives": {
            "n": n_pos, "hits": hits,
            "hit_rate": wilson(hits, n_pos),
            "mean_lead_months": mean(leads) if leads else float("nan"),
            "detail": pos_detail,
        },
        "negatives": {
            "n": n_neg, "traps": traps,
            "trap_rate": wilson(traps, n_neg),
            "detail": neg_detail,
        },
        "controls_plumbing": ctrl_detail,
        "borderline": border,
        "excluded_no_data": excluded,
        "forward_return": {
            "picks_6m": picks_fwd6, "picks_12m": picks_fwd12,
            "control_6m": ctrl_fwd6, "control_12m": ctrl_fwd12,
            "n_picks": len(hit_picks),
        },
    }
