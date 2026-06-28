#!/usr/bin/env python
"""Generate a self-contained HTML visualization of the backtest results.

Reads reports/backtest_results.json (v1, 30-name control) and
reports/backtest_results_v2.json (v2, realistic 65-name control) and writes
reports/backtest.html — no external dependencies, opens offline.

Usage: .venv/bin/python reports/make_report_html.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = json.loads((HERE / "backtest_results.json").read_text())
V2 = json.loads((HERE / "backtest_results_v2.json").read_text())


def pct(x):
    return f"{x*100:.0f}%"


def bar(label, value, vmax, color, sub=""):
    w = 0 if vmax == 0 else max(1.0, value / vmax * 100)
    return f"""<div class="row">
      <div class="rl">{label}</div>
      <div class="rt"><div class="fill" style="width:{w:.1f}%;background:{color}"></div>
        <span class="val">{value*100:.0f}%{(' · '+sub) if sub else ''}</span></div>
    </div>"""


def metric_card(title, value, sub, tone="neutral"):
    return f"""<div class="card {tone}"><div class="ct">{title}</div>
      <div class="cv">{value}</div><div class="cs">{sub}</div></div>"""


def positives_rows():
    d10 = {(r["ticker"], i): r for i, r in enumerate(V2["top_10"]["summary"]["positives"]["detail"])}
    d20 = V2["top_20"]["summary"]["positives"]["detail"]
    rows = []
    for i, r in enumerate(d20):
        h10 = V2["top_10"]["summary"]["positives"]["detail"][i]["hit"]
        h20 = r["hit"]
        lead = r["lead_months"]
        chip10 = '<span class="hit">✓</span>' if h10 else '<span class="miss">·</span>'
        chip20 = '<span class="hit">✓</span>' if h20 else '<span class="miss">·</span>'
        rows.append(
            f"<tr><td class='tk'>{r['ticker']}</td><td class='ty'>{r['type']}</td>"
            f"<td class='c'>{chip10}</td><td class='c'>{chip20}</td>"
            f"<td class='c'>{lead if (h10 or h20) and lead else '—'}</td></tr>"
        )
    return "\n".join(rows)


def negatives_rows():
    n10 = {x["ticker"]: x["trap"] for x in V2["top_10"]["summary"]["negatives"]["detail"]}
    n20 = {x["ticker"]: x["trap"] for x in V2["top_20"]["summary"]["negatives"]["detail"]}
    rows = []
    for t in n10:
        f10 = '<span class="bad">flagged</span>' if n10[t] else '<span class="good">avoided</span>'
        f20 = '<span class="bad">flagged</span>' if n20.get(t) else '<span class="good">avoided</span>'
        rows.append(f"<tr><td class='tk'>{t}</td><td class='c'>{f10}</td><td class='c'>{f20}</td></tr>")
    return "\n".join(rows)


s10 = V2["top_10"]["summary"]
s20 = V2["top_20"]["summary"]
fr = s10["forward_return"]
v1h10 = V1["top_10"]["summary"]["positives"]["hit_rate"][0]
v2h10 = s10["positives"]["hit_rate"][0]

hit10 = s10["positives"]["hit_rate"]
hit20 = s20["positives"]["hit_rate"]
trap10 = s10["negatives"]["trap_rate"]

ACC = "#2563eb"   # picks / positive
GREY = "#94a3b8"  # control
RED = "#dc2626"   # trap

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inflection Discovery — Backtest Results</title>
<style>
  :root {{ --fg:#0f172a; --mut:#64748b; --line:#e2e8f0; --bg:#ffffff; --soft:#f8fafc; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg:#e5e7eb; --mut:#9ca3af; --line:#27303f; --bg:#0b0f17; --soft:#111827; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif;
    color:var(--fg); background:var(--bg); margin:0; line-height:1.5; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:32px 20px 64px; }}
  h1 {{ font-size:24px; margin:0 0 4px; }}
  h2 {{ font-size:16px; margin:34px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line); }}
  .meta {{ color:var(--mut); font-size:13px; margin-bottom:18px; }}
  .banner {{ background:var(--soft); border:1px solid var(--line); border-left:3px solid {ACC};
    border-radius:8px; padding:12px 14px; font-size:13.5px; color:var(--fg); }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin:14px 0; }}
  .card {{ border:1px solid var(--line); border-radius:10px; padding:14px; background:var(--soft); }}
  .card .ct {{ font-size:12px; color:var(--mut); }}
  .card .cv {{ font-size:26px; font-weight:700; margin:4px 0 2px; }}
  .card .cs {{ font-size:12px; color:var(--mut); }}
  .card.good .cv {{ color:#16a34a; }} .card.warn .cv {{ color:{RED}; }}
  .row {{ display:flex; align-items:center; gap:10px; margin:7px 0; }}
  .rl {{ width:160px; font-size:13px; color:var(--mut); text-align:right; }}
  .rt {{ position:relative; flex:1; background:var(--soft); border-radius:6px; height:26px; border:1px solid var(--line); }}
  .fill {{ height:100%; border-radius:6px 0 0 6px; }}
  .val {{ position:absolute; left:8px; top:0; line-height:26px; font-size:12.5px; font-weight:600; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:6px; }}
  th,td {{ text-align:left; padding:7px 8px; border-bottom:1px solid var(--line); }}
  th {{ color:var(--mut); font-weight:600; font-size:12px; }}
  td.c {{ text-align:center; }} td.tk {{ font-weight:600; }} td.ty {{ color:var(--mut); }}
  .hit {{ color:#16a34a; font-weight:700; }} .miss {{ color:var(--mut); }}
  .good {{ color:#16a34a; }} .bad {{ color:{RED}; }}
  .note {{ font-size:13px; color:var(--mut); }}
  .note li {{ margin:4px 0; }}
  .legend {{ font-size:12px; color:var(--mut); margin-top:6px; }}
  .sw {{ display:inline-block; width:10px; height:10px; border-radius:2px; vertical-align:middle; margin:0 4px 0 10px; }}
</style></head>
<body><div class="wrap">
  <h1>Inflection Discovery — Backtest Results</h1>
  <div class="meta">Engine B · point-in-time · free data · 2026-06-28</div>
  <div class="banner"><b>Read first:</b> a discrimination <b>smoke-test, not generalizable accuracy</b>.
    n = {s10['positives']['n']} positive events / {s10['negatives']['n']} trap tickers; every rate carries a wide
    95% CI. PIT integrity is verified at runtime (4-canary leak battery passes; 131 tests pass).</div>

  <h2>The selectivity correction</h2>
  <div class="note">v1 used a thin 30-name control arm (median ~{V1['top_10']['summary']['median_eligible_n']} eligible/date),
    so "top-10" was barely selective and the hit rate was inflated. v2 uses a realistic
    {V2['top_10']['control_n']}-name arm (median ~{s10['median_eligible_n']} eligible/date). Top-10 hit rate:</div>
  {bar("v1 (thin, 30 ctrl)", v1h10, 1.0, GREY)}
  {bar("v2 (realistic, 65 ctrl)", v2h10, 1.0, ACC)}
  <div class="note legend">The drop from {pct(v1h10)} → {pct(v2h10)} is the honest finding: D does not push the
    specific inflections into the absolute top-10 against ~{s10['median_eligible_n']} depressed peers.</div>

  <h2>Headline metrics (v2, realistic universe)</h2>
  <div class="cards">
    {metric_card("Hit rate · top-10", pct(hit10[0]), f"{s10['positives']['hits']}/{s10['positives']['n']} · CI {pct(hit10[1])}–{pct(hit10[2])}")}
    {metric_card("Hit rate · top-20", pct(hit20[0]), f"{s20['positives']['hits']}/{s20['positives']['n']} · CI {pct(hit20[1])}–{pct(hit20[2])}")}
    {metric_card("Trap rate · top-10", pct(trap10[0]), f"{s10['negatives']['traps']}/{s10['negatives']['n']} · lower=better", "warn")}
    {metric_card("Fwd return 12m", f"+{fr['picks_12m']*100:.0f}%", f"picks vs +{fr['control_12m']*100:.0f}% control", "good")}
  </div>

  <h2>Forward return — picks vs control universe</h2>
  {bar("Picks · 6 months", fr['picks_6m'], max(fr['picks_12m'],fr['control_12m']), ACC)}
  {bar("Control · 6 months", fr['control_6m'], max(fr['picks_12m'],fr['control_12m']), GREY)}
  {bar("Picks · 12 months", fr['picks_12m'], max(fr['picks_12m'],fr['control_12m']), ACC)}
  {bar("Control · 12 months", fr['control_12m'], max(fr['picks_12m'],fr['control_12m']), GREY)}
  <div class="legend"><span class="sw" style="background:{ACC}"></span>top-N picks
    <span class="sw" style="background:{GREY}"></span>depressed control universe ·
    the top of the ranking outperforms even though top-10 recall is modest.</div>

  <h2>Positives — did it surface the inflection?</h2>
  <table><thead><tr><th>Ticker</th><th>Type</th><th>top-10</th><th>top-20</th><th>Lead (mo)</th></tr></thead>
  <tbody>{positives_rows()}</tbody></table>

  <h2>Negatives — did it avoid the trap?</h2>
  <table><thead><tr><th>Ticker</th><th>top-10</th><th>top-20</th></tr></thead>
  <tbody>{negatives_rows()}</tbody></table>
  <div class="legend">Plumbing controls (CRDO, NBIS) correctly never surfaced — the A gate excludes loved growth.
    Excluded (no PIT data): {', '.join(sorted(set(x.split(' ')[0] for x in s10['excluded_no_data']))) or '—'}.</div>

  <h2>Honest limitations</h2>
  <ul class="note">
    <li><b>Weak top-10 recall (21%):</b> D surfaces the strongest inflections (AXTI, MU, NVDA) but doesn't out-rank all depressed peers.</li>
    <li><b>Hard traps persist:</b> PTON (margin bounce off a deep trough), ZM (cheap+flat "dead money"), INTC-fakestart (depressed + rich AI/foundry narrative).</li>
    <li><b>Value traps vs real turnarounds are not separable on free numeric signals</b> — richer (LLM / Implementation A) judgment is the real next step.</li>
    <li>Forward return is regime-noisy (small n); foreign-filer quarterly gap & post-spin gating remain.</li>
  </ul>
  <div class="meta" style="margin-top:24px">Source: reports/backtest_results_v2.json · regenerate via reports/make_report_html.py</div>
</div></body></html>"""

(HERE / "backtest.html").write_text(html)
print("wrote", HERE / "backtest.html", f"({len(html)} bytes)")
