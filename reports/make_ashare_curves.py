#!/usr/bin/env python
"""A-share price curves around an inflection anchor: 6 months before -> 18 after.

NOTE: the A-share path is LIVE-only (no PIT benchmark — akshare gives no clean
point-in-time data), so unlike the US benchmark these anchors are HAND-PICKED
illustrative inflection / cyclical-top dates, not mechanism-detected. hfq prices
are point-in-time-safe, so the curves themselves are honest. Output:
reports/ashare_curves.html

Usage: .venv/bin/python reports/make_ashare_curves.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inflection_discovery.ashare.data import ashare_prices  # noqa: E402

GREEN, RED, MUT = "#16a34a", "#dc2626", "#94a3b8"
PRE, POST = 183, 548

# (code, name, anchor T, story) — illustrative
TURNAROUNDS = [
    ("601919", "中远海控 COSCO", "2021-03-31", "shipping super-cycle"),
    ("002594", "比亚迪 BYD", "2021-06-30", "EV ramp (DM-i / blade)"),
    ("601127", "赛力斯 Seres", "2023-09-30", "AITO M7 + Huawei"),
    ("601899", "紫金矿业 Zijin", "2020-09-30", "copper / gold cycle"),
    ("300750", "宁德时代 CATL", "2020-06-30", "EV battery boom"),
]
CAUTIONARY = [
    ("601919", "中远海控 COSCO", "2022-07-31", "freight-rate peak → fall"),
    ("002607", "中公教育 Offcn", "2021-03-31", "post-peak collapse"),
    ("002460", "赣锋锂业 Ganfeng", "2022-07-31", "lithium peak → bust"),
]

_CACHE: dict = {}


def prices(code):
    if code not in _CACHE:
        _CACHE[code] = ashare_prices(code)
    return _CACHE[code]


def curve(close: pd.Series, T: pd.Timestamp):
    w = close[(close.index >= T - pd.Timedelta(days=PRE)) & (close.index <= T + pd.Timedelta(days=POST))].dropna()
    if len(w) < 10 or int((w.index < T).sum()) < 20:
        return None, None, None
    base = w.asof(T)
    if pd.isna(base) or base <= 0:
        base = float(w.iloc[0])
    norm = (w / base * 100.0).tolist()
    dates = list(w.index)
    it = next((i for i, d in enumerate(dates) if d >= T), len(dates) - 1)
    n = len(norm)
    W, H, pl, pr, pt, pb = 240, 96, 6, 6, 10, 10
    pw, ph = W - pl - pr, H - pt - pb
    ymin, ymax = min(norm), max(norm)
    rng = max(ymax - ymin, 1e-6)
    X = lambda i: pl + (i / (n - 1)) * pw
    Y = lambda v: pt + (1 - (v - ymin) / rng) * ph
    pre_pts = " ".join(f"{X(i):.1f},{Y(norm[i]):.1f}" for i in range(0, it + 1))
    post_pts = " ".join(f"{X(i):.1f},{Y(norm[i]):.1f}" for i in range(it, n))
    post_ret = norm[-1] / norm[it] - 1.0 if norm[it] else 0.0
    pre_ret = norm[it] / norm[0] - 1.0 if norm[0] else 0.0
    pcol = GREEN if post_ret >= 0 else RED
    xt, y100 = X(it), Y(100.0)
    svg = f"""<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="none" style="display:block;height:84px;width:100%">
      <line x1="{pl}" y1="{y100:.1f}" x2="{W-pr}" y2="{y100:.1f}" stroke="var(--line)" stroke-dasharray="2 3"/>
      <line x1="{xt:.1f}" y1="{pt}" x2="{xt:.1f}" y2="{H-pb}" stroke="{MUT}"/>
      <polyline points="{pre_pts}" fill="none" stroke="{MUT}" stroke-width="1.4"/>
      <polyline points="{post_pts}" fill="none" stroke="{pcol}" stroke-width="1.8"/></svg>"""
    return svg, pre_ret, post_ret


def card(code, name, T, story):
    svg, pre, post = curve(prices(code)["Close"] if not prices(code).empty else pd.Series(dtype=float), pd.Timestamp(T))
    if svg is None:
        return f'<div class="card"><div class="hd"><span class="tk">{code}</span></div><div class="sub">{name} · no data</div></div>'
    pcol = GREEN if post >= 0 else RED
    return f"""<div class="card"><div class="hd"><span class="tk">{name}</span><span class="cd">{code}</span></div>
      <div class="sub">{story} · T={T}</div>{svg}
      <div class="rets"><span class="pre">pre 6m {pre*100:+.0f}%</span>
        <span class="post" style="color:{pcol}">post 18m {post*100:+.0f}%</span></div></div>"""


t_cards = "".join(card(*x) for x in TURNAROUNDS)
c_cards = "".join(card(*x) for x in CAUTIONARY)
html = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A-share price curves around inflection</title>
<style>
  :root {{ --fg:#0f172a; --mut:#64748b; --line:#e2e8f0; --bg:#fff; --soft:#f8fafc; }}
  @media (prefers-color-scheme:dark){{:root{{--fg:#e5e7eb;--mut:#9ca3af;--line:#27303f;--bg:#0b0f17;--soft:#111827;}}}}
  *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--fg);background:var(--bg);margin:0}}
  .wrap{{max-width:980px;margin:0 auto;padding:28px 18px 60px}}
  h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:15px;margin:24px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
  .meta{{color:var(--mut);font-size:13px;margin-bottom:8px}}
  .warn{{background:var(--soft);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:8px;padding:10px 12px;font-size:12.5px;margin:10px 0 4px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
  .card{{border:1px solid var(--line);border-radius:10px;padding:10px;background:var(--soft)}}
  .hd{{display:flex;align-items:center;justify-content:space-between;gap:6px}}
  .tk{{font-weight:700;font-size:13.5px}} .cd{{font-size:11px;color:var(--mut)}}
  .sub{{font-size:11px;color:var(--mut);margin:1px 0 6px}}
  .rets{{display:flex;justify-content:space-between;font-size:11.5px;margin-top:4px}} .pre{{color:var(--mut)}} .post{{font-weight:700}}
</style></head><body><div class="wrap">
  <h1>A-share price curves around inflection (±6 / +18 months)</h1>
  <div class="meta">Normalized to 100 at T · grey = pre-T · green up / red down post-T · vertical line = T.</div>
  <div class="warn"><b>Illustrative, not a PIT backtest.</b> The A-share path is LIVE-only (akshare has no clean
    point-in-time data), so these anchor dates are hand-picked known inflection / cyclical-top points, not
    mechanism-detected. hfq prices are point-in-time-safe, so the curves are honest.</div>
  <h2>Turnarounds (cyclical / narrative upturns)</h2>
  <div class="grid">{t_cards}</div>
  <h2>Cyclical tops &amp; value destruction (the cautionary side)</h2>
  <div class="grid">{c_cards}</div>
  <div class="meta" style="margin-top:18px">hfq prices via akshare · regenerate via reports/make_ashare_curves.py</div>
</div></body></html>"""
(ROOT / "reports" / "ashare_curves.html").write_text(html)
print("wrote reports/ashare_curves.html", f"({len(html)} bytes)")
