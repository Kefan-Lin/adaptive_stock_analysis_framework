#!/usr/bin/env python
"""Self-contained HTML for the A (LLM) vs B (code) comparison-mode backtest.

Reads reports/backtest_results_A.json (top-10) and backtest_results_A_top20.json
(top-20) — each holds {"A": {...}, "B": {...}} from harness.llm_backtest, where B
is recomputed in the SAME run on the identical control arm (and reproduces the
stored v2 numbers). Writes reports/ab_compare.html. Opens offline.

Usage: .venv/bin/python reports/make_ab_compare.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
T10 = json.loads((HERE / "backtest_results_A.json").read_text())
T20 = json.loads((HERE / "backtest_results_A_top20.json").read_text())

ACC, GREY, GREEN, RED = "#2563eb", "#94a3b8", "#16a34a", "#dc2626"


def pct(x):
    return f"{x*100:.0f}%"


def summ(doc, eng):
    return doc[eng]["summary"]


def card(title, a_val, b_val, sub, good_high=True):
    a_better = (a_val >= b_val) if good_high else (a_val <= b_val)
    return f"""<div class="card">
      <div class="ct">{title}</div>
      <div class="cv"><span class="a">{pct(a_val)}</span>
        <span class="vs">vs</span><span class="b">{pct(b_val)}</span></div>
      <div class="cs">{sub} · {'A wins' if a_better else 'B wins' if a_val!=b_val else 'tie'}</div>
    </div>"""


def bar(label, a, b):
    aw = max(1.0, a * 100); bw = max(1.0, b * 100)
    return f"""<div class="brow"><div class="bl">{label}</div>
      <div class="bwrap">
        <div class="btrack"><div class="bfill" style="width:{aw:.0f}%;background:{ACC}"></div><span>A {pct(a)}</span></div>
        <div class="btrack"><div class="bfill" style="width:{bw:.0f}%;background:{GREY}"></div><span>B {pct(b)}</span></div>
      </div></div>"""


a10, b10 = summ(T10, "A"), summ(T10, "B")
a20, b20 = summ(T20, "A"), summ(T20, "B")

# per-name (positives): top-10 + top-20 hit flags for each engine
p10A = {d["ticker"]: d["hit"] for d in a10["positives"]["detail"]}
# tickers repeat (MU x2) — use order-aligned lists instead
posA10 = a10["positives"]["detail"]; posA20 = a20["positives"]["detail"]
posB10 = b10["positives"]["detail"]; posB20 = b20["positives"]["detail"]
pos_rows = ""
for i in range(len(posA20)):
    tk = posA20[i]["ticker"]; ty = posA20[i]["type"]
    def chip(flag):
        return f'<span class="hit">✓</span>' if flag else '<span class="miss">·</span>'
    pos_rows += (f"<tr><td class='tk'>{tk}</td><td class='ty'>{ty}</td>"
                 f"<td class='c'>{chip(posA10[i]['hit'])}</td><td class='c'>{chip(posA20[i]['hit'])}</td>"
                 f"<td class='c'>{chip(posB10[i]['hit'])}</td><td class='c'>{chip(posB20[i]['hit'])}</td></tr>")

negA10 = {d["ticker"]: d["trap"] for d in a10["negatives"]["detail"]}
negA20 = {d["ticker"]: d["trap"] for d in a20["negatives"]["detail"]}
negB10 = {d["ticker"]: d["trap"] for d in b10["negatives"]["detail"]}
negB20 = {d["ticker"]: d["trap"] for d in b20["negatives"]["detail"]}
neg_rows = ""
for tk in negA20:
    def fchip(flag):  # flagged==surfaced==BAD for a trap
        return '<span class="bad">surfaced</span>' if flag else '<span class="good">avoided</span>'
    neg_rows += (f"<tr><td class='tk'>{tk}</td>"
                 f"<td class='c'>{fchip(negA10.get(tk))}</td><td class='c'>{fchip(negA20.get(tk))}</td>"
                 f"<td class='c'>{fchip(negB10.get(tk))}</td><td class='c'>{fchip(negB20.get(tk))}</td></tr>")

fr10A, fr10B = a10["forward_return"], b10["forward_return"]

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A (LLM) vs B (code) — comparison-mode backtest</title>
<style>
  :root {{ --fg:#0f172a; --mut:#64748b; --line:#e2e8f0; --bg:#fff; --soft:#f8fafc; }}
  @media (prefers-color-scheme:dark){{:root{{--fg:#e5e7eb;--mut:#9ca3af;--line:#27303f;--bg:#0b0f17;--soft:#111827;}}}}
  *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,"PingFang SC",sans-serif;color:var(--fg);background:var(--bg);margin:0}}
  .wrap{{max-width:900px;margin:0 auto;padding:30px 20px 64px}}
  h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:15px;margin:28px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
  .meta{{color:var(--mut);font-size:13px;margin-bottom:14px}}
  .banner{{background:var(--soft);border:1px solid var(--line);border-left:3px solid {ACC};border-radius:8px;padding:11px 13px;font-size:13px;margin-bottom:8px}}
  .warn{{border-left-color:#d97706}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}}
  .card{{border:1px solid var(--line);border-radius:10px;padding:13px;background:var(--soft)}}
  .ct{{font-size:12px;color:var(--mut)}} .cv{{font-size:22px;font-weight:700;margin:5px 0 3px}}
  .cv .a{{color:{ACC}}} .cv .b{{color:{GREY}}} .cv .vs{{font-size:12px;color:var(--mut);margin:0 7px;font-weight:400}}
  .cs{{font-size:11.5px;color:var(--mut)}}
  .brow{{display:flex;gap:12px;align-items:center;margin:9px 0}} .bl{{width:150px;font-size:13px;color:var(--mut);text-align:right}}
  .bwrap{{flex:1;display:flex;flex-direction:column;gap:4px}}
  .btrack{{position:relative;background:var(--soft);border:1px solid var(--line);border-radius:5px;height:22px}}
  .bfill{{height:100%;border-radius:5px 0 0 5px}} .btrack span{{position:absolute;left:7px;top:0;line-height:22px;font-size:11.5px;font-weight:600}}
  table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}}
  th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}}
  th{{color:var(--mut);font-weight:600;font-size:11.5px}} td.c{{text-align:center}} td.tk{{font-weight:600}} td.ty{{color:var(--mut);font-size:11.5px}}
  .hit{{color:{GREEN};font-weight:700}} .miss{{color:var(--mut)}} .good{{color:{GREEN};font-size:11.5px}} .bad{{color:{RED};font-size:11.5px;font-weight:600}}
  .grp{{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}}
</style></head><body><div class="wrap">
  <h1>A (LLM judgment) vs B (code features) — comparison-mode backtest</h1>
  <div class="meta">Same frozen ≤T EDGAR corpus · same A-gate, momentum, 65-name control arm, D-formula & metrics · only B/C/trap judgment is swapped.</div>
  <div class="banner"><b>What changed vs the engine-B run.</b> B here is <b>recomputed in the same harness</b> and
    reproduces the stored v2 numbers exactly (top-10 3/14 hit, 4/9 trap; top-20 6/14, 5/9) — proving the only
    variable is the engine. B ran text-free (numeric only); A adds earnings + <b>narrative</b> + trap judgment read
    from the same filings.</div>
  <div class="banner warn"><b>Read as an upper bound.</b> The LLM already knows these outcomes, so A's benchmark
    rates are <b>memorization-contaminated</b> — a discrimination probe, not generalizable accuracy. The control arm
    stays B-scored on purpose (LLM-scoring 65 random tickers would be <i>more</i> biased). Positives scored at the
    fixed hit-date (t*−3mo); per-A lead-time not measured. n = 14 positives / 9 traps, wide Wilson CIs.</div>

  <h2>Headline — A vs B</h2>
  <div class="grp">top-10</div>
  <div class="cards">
    {card("Hit rate · top-10", a10['positives']['hit_rate'][0], b10['positives']['hit_rate'][0], f"{a10['positives']['hits']}/{a10['positives']['n']} vs {b10['positives']['hits']}/{b10['positives']['n']}", True)}
    {card("Trap rate · top-10", a10['negatives']['trap_rate'][0], b10['negatives']['trap_rate'][0], f"{a10['negatives']['traps']}/{a10['negatives']['n']} vs {b10['negatives']['traps']}/{b10['negatives']['n']} · lower better", False)}
  </div>
  <div class="grp">top-20</div>
  <div class="cards">
    {card("Hit rate · top-20", a20['positives']['hit_rate'][0], b20['positives']['hit_rate'][0], f"{a20['positives']['hits']}/{a20['positives']['n']} vs {b20['positives']['hits']}/{b20['positives']['n']}", True)}
    {card("Trap rate · top-20", a20['negatives']['trap_rate'][0], b20['negatives']['trap_rate'][0], f"{a20['negatives']['traps']}/{a20['negatives']['n']} vs {b20['negatives']['traps']}/{b20['negatives']['n']} · lower better", False)}
  </div>

  <h2>Recall &amp; trap-avoidance (A blue / B grey)</h2>
  {bar("Hit rate · top-10", a10['positives']['hit_rate'][0], b10['positives']['hit_rate'][0])}
  {bar("Hit rate · top-20", a20['positives']['hit_rate'][0], b20['positives']['hit_rate'][0])}
  {bar("Trap rate · top-10 (lower=better)", a10['negatives']['trap_rate'][0], b10['negatives']['trap_rate'][0])}
  {bar("Trap rate · top-20 (lower=better)", a20['negatives']['trap_rate'][0], b20['negatives']['trap_rate'][0])}
  <div class="meta" style="margin-top:10px">Forward return 12m, top-10 picks vs depressed control: <b>A +{fr10A['picks_12m']*100:.0f}%</b> ({fr10A['n_picks']} picks)
    vs control +{fr10A['control_12m']*100:.0f}% · B +{fr10B['picks_12m']*100:.0f}% ({fr10B['n_picks']} picks) vs +{fr10B['control_12m']*100:.0f}%. A's wider recall did not dilute pick quality.</div>

  <h2>Positives — did it surface the inflection?</h2>
  <table><thead><tr><th>Ticker</th><th>Type</th><th>A·top10</th><th>A·top20</th><th>B·top10</th><th>B·top20</th></tr></thead>
  <tbody>{pos_rows}</tbody></table>
  <div class="meta">A's extra recall (BB, NOK, COHR, INTC-2025, LITE, NFLX) is the narrative/earnings judgment B can't make text-free.
    Shared misses: SNDK &amp; AMD fail the depressed-base A gate (post-spin / already-rallied); META's catalyst post-dates T; BILI is a quarterly-XBRL-less ADR.</div>

  <h2>Negatives — did it avoid the trap?</h2>
  <table><thead><tr><th>Ticker</th><th>A·top10</th><th>A·top20</th><th>B·top10</th><th>B·top20</th></tr></thead>
  <tbody>{neg_rows}</tbody></table>
  <div class="meta"><b>A's structural-decline judgment</b> avoids LUMN / PTON / FOSL that B's mechanical filter surfaced.
    A's two residual misses are the intrinsically-hard cases the design predicted: <b>ZM</b> (dead-money with a
    pristine balance sheet — no trap signal, only "no turn") and <b>INTC-2023 fake-start</b> (reads like a real
    trough on the as-of numbers). Even the LLM gets these two wrong — that is the honest floor.</div>

  <div class="meta" style="margin-top:22px">Source: reports/backtest_results_A*.json · authored judgments reports/llm_scores.json · regenerate via reports/make_ab_compare.py</div>
</div></body></html>"""

(HERE / "ab_compare.html").write_text(html)
print("wrote reports/ab_compare.html", f"({len(html)} bytes)")
