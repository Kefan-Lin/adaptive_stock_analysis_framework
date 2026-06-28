#!/usr/bin/env python
"""Per-stock price curves around the detection point (T): 6 months before and 18
months after. Normalized to 100 at T, with a vertical marker at T. Colored by the
post-T outcome (green up / red down). Self-contained HTML, opens offline.

T per name = the detection anchor: positives use t*-3mo (the hit date); negatives
use their as-of evaluation date. Prices via yfinance (split-adjusted, consistent
within each window). Output: reports/price_curves.html

Usage: .venv/bin/python reports/make_price_curves.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inflection_discovery.benchmark import load_benchmark  # noqa: E402
from inflection_discovery.pit.prices import _raw_history  # noqa: E402

HERE = ROOT / "reports"
V2 = json.loads((HERE / "backtest_results_v2.json").read_text())
GREEN, RED, ACC, MUT = "#16a34a", "#dc2626", "#2563eb", "#94a3b8"
PRE, POST = 183, 548  # 6 months before T, 18 months after T


def verdicts():
    pos = V2["top_20"]["summary"]["positives"]["detail"]  # aligned with benchmark order
    neg = {x["ticker"]: x["trap"] for x in V2["top_20"]["summary"]["negatives"]["detail"]}
    return pos, neg


def curve_svg(close: pd.Series, T: pd.Timestamp) -> str:
    w = close[(close.index >= T - pd.Timedelta(days=PRE)) & (close.index <= T + pd.Timedelta(days=POST))].dropna()
    if len(w) < 10:
        return None, "no price data"
    n_pre = int((w.index < T).sum())
    if n_pre < 30:
        return None, "short history pre-T (unreliable base)"
    base = w.asof(T)
    if pd.isna(base) or base <= 0:
        base = float(w.iloc[0])
    norm = (w / base * 100.0).tolist()
    dates = list(w.index)
    # index of T (first date >= T)
    it = next((i for i, d in enumerate(dates) if d >= T), len(dates) - 1)
    n = len(norm)
    W, H, pl, pr, pt, pb = 240, 96, 6, 6, 10, 10
    pw, ph = W - pl - pr, H - pt - pb
    ymin, ymax = min(norm), max(norm)
    rng = max(ymax - ymin, 1e-6)

    def X(i):
        return pl + (i / (n - 1)) * pw

    def Y(v):
        return pt + (1 - (v - ymin) / rng) * ph

    pre_pts = " ".join(f"{X(i):.1f},{Y(norm[i]):.1f}" for i in range(0, it + 1))
    post_pts = " ".join(f"{X(i):.1f},{Y(norm[i]):.1f}" for i in range(it, n))
    post_ret = norm[-1] / norm[it] - 1.0 if norm[it] else 0.0
    pre_ret = norm[it] / norm[0] - 1.0 if norm[0] else 0.0
    if abs(post_ret) > 8.0:
        return None, f"suspect data ({post_ret*100:+.0f}%, likely split/spin artifact)"
    pcol = GREEN if post_ret >= 0 else RED
    xt = X(it)
    y100 = Y(100.0)
    svg = f"""<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="none" style="display:block;height:84px;width:100%">
      <line x1="{pl}" y1="{y100:.1f}" x2="{W-pr}" y2="{y100:.1f}" stroke="var(--line)" stroke-dasharray="2 3"/>
      <line x1="{xt:.1f}" y1="{pt}" x2="{xt:.1f}" y2="{H-pb}" stroke="{MUT}" stroke-width="1"/>
      <polyline points="{pre_pts}" fill="none" stroke="{MUT}" stroke-width="1.4"/>
      <polyline points="{post_pts}" fill="none" stroke="{pcol}" stroke-width="1.8"/>
    </svg>"""
    return (svg, pre_ret, post_ret), None


def card(ticker, sub, chip_html, svg, pre_ret, post_ret):
    pcol = GREEN if post_ret >= 0 else RED
    return f"""<div class="card">
      <div class="hd"><span class="tk">{ticker}</span> {chip_html}</div>
      <div class="sub">{sub}</div>
      {svg}
      <div class="rets"><span class="pre">pre 6m {pre_ret*100:+.0f}%</span>
        <span class="post" style="color:{pcol}">post 18m {post_ret*100:+.0f}%</span></div>
    </div>"""


def chip(text, kind):
    bg = {"hit": "#dcfce7", "miss": "#f1f5f9", "flagged": "#fee2e2", "avoided": "#dcfce7"}[kind]
    fg = {"hit": "#166534", "miss": "#64748b", "flagged": "#991b1b", "avoided": "#166534"}[kind]
    return f'<span class="chip" style="background:{bg};color:{fg}">{text}</span>'


pos_detail, neg_trap = verdicts()
rows = load_benchmark()
pos_cards, neg_cards, skipped = [], [], []
pos_i = 0
for r in rows:
    T = r.hit_date()
    if T is None:
        continue
    close = _raw_history(r.ticker)
    if close is not None and not close.empty and "Close" in close:
        res, reason = curve_svg(close["Close"], T)
    else:
        res, reason = None, "no price data"
    if res is None:
        skipped.append(f"{r.ticker} ({reason})")
        if r.label == "positive":
            pos_i += 1
        continue
    svg, pre, post = res
    sub = f"{r.inflection_type} · T={T.date()}"
    if r.label == "positive":
        hit = pos_detail[pos_i]["hit"] if pos_i < len(pos_detail) else False
        c = chip("hit (top-20)", "hit") if hit else chip("miss", "miss")
        pos_cards.append(card(r.ticker, sub, c, svg, pre, post))
        pos_i += 1
    elif r.label == "negative":
        trap = neg_trap.get(r.ticker, False)
        c = chip("flagged (trap)", "flagged") if trap else chip("avoided", "avoided")
        neg_cards.append(card(r.ticker, sub, c, svg, pre, post))

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inflection Discovery — price curves around detection</title>
<style>
  :root {{ --fg:#0f172a; --mut:#64748b; --line:#e2e8f0; --bg:#fff; --soft:#f8fafc; }}
  @media (prefers-color-scheme:dark){{:root{{--fg:#e5e7eb;--mut:#9ca3af;--line:#27303f;--bg:#0b0f17;--soft:#111827;}}}}
  *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,"PingFang SC",sans-serif;color:var(--fg);background:var(--bg);margin:0}}
  .wrap{{max-width:980px;margin:0 auto;padding:28px 18px 60px}}
  h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:15px;margin:26px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
  .meta{{color:var(--mut);font-size:13px;margin-bottom:14px}}
  .legend{{font-size:12px;color:var(--mut);margin:8px 0 4px}}
  .sw{{display:inline-block;width:18px;height:0;border-top:2px solid;vertical-align:middle;margin:0 4px 0 12px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
  .card{{border:1px solid var(--line);border-radius:10px;padding:10px 10px 8px;background:var(--soft)}}
  .hd{{display:flex;align-items:center;justify-content:space-between;gap:6px}}
  .tk{{font-weight:700;font-size:14px}} .sub{{font-size:11px;color:var(--mut);margin:1px 0 6px}}
  .chip{{font-size:10.5px;padding:2px 7px;border-radius:999px;font-weight:600;white-space:nowrap}}
  .rets{{display:flex;justify-content:space-between;font-size:11.5px;margin-top:4px}} .pre{{color:var(--mut)}} .post{{font-weight:700}}
</style></head><body><div class="wrap">
  <h1>Price curves around the detection point</h1>
  <div class="meta">Each curve: 6 months before → T (detection) → 18 months after. Normalized to 100 at T;
    grey = pre-T, colored = post-T (green up / red down). Vertical line = T.
    Recent names (2025 T) have a shorter realized post-window — the line ends at the latest data.</div>
  <div class="legend"><span class="sw" style="border-color:{MUT}"></span>before T (setup)
    <span class="sw" style="border-color:{GREEN}"></span>after T, up
    <span class="sw" style="border-color:{RED}"></span>after T, down</div>

  <h2>Positives — {len(pos_cards)} names (should rise after T)</h2>
  <div class="grid">{''.join(pos_cards)}</div>

  <h2>Negatives — {len(neg_cards)} names (traps should keep falling / stay flat)</h2>
  <div class="grid">{''.join(neg_cards)}</div>

  <div class="meta" style="margin-top:20px">No price data (skipped): {', '.join(skipped) or '—'}.
    T = t*-3mo for positives, as-of date for negatives. Source: yfinance · regenerate via reports/make_price_curves.py</div>
</div></body></html>"""

(HERE / "price_curves.html").write_text(html)
print("wrote", HERE / "price_curves.html", f"({len(html)} bytes); pos={len(pos_cards)} neg={len(neg_cards)} skipped={len(skipped)}")
