#!/usr/bin/env python
"""Build a self-contained single-page dashboard that INLINES the three report
HTMLs via iframe srcdoc (so it works under file:// — plain iframe `src` to local
files is blocked by Chrome). Each report keeps its own CSS, isolated per iframe.

Run after the three report generators. Usage:
  .venv/bin/python reports/make_dashboard.py
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent


def esc(s: str) -> str:
    # minimal srcdoc attribute escaping (double-quoted attribute)
    return s.replace("&", "&amp;").replace('"', "&quot;")


def load(name: str) -> str:
    p = HERE / name
    return esc(p.read_text()) if p.exists() else "<p style='padding:20px'>missing: " + name + "</p>"

TABS = [
    ("abcompare", "A vs B (LLM vs code)", "ab_compare.html"),
    ("backtest", "Backtest metrics (B)", "backtest.html"),
    ("us", "US price curves", "price_curves.html"),
    ("ashare", "A-share curves", "ashare_curves.html"),
]

frames = "".join(
    f'<iframe class="view" id="f-{key}" srcdoc="{load(fname)}" title="{label}" '
    f'style="display:{"block" if i == 0 else "none"}"></iframe>'
    for i, (key, label, fname) in enumerate(TABS)
)
tabs = "".join(
    f'<button class="tab{" on" if i == 0 else ""}" data-key="{key}">{label}</button>'
    for i, (key, label, _) in enumerate(TABS)
)

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inflection Discovery — Dashboard</title>
<style>
  :root {{ --fg:#0f172a; --mut:#64748b; --line:#e2e8f0; --bg:#fff; --acc:#2563eb; }}
  @media (prefers-color-scheme:dark){{:root{{--fg:#e5e7eb;--mut:#9ca3af;--line:#27303f;--bg:#0b0f17;--acc:#60a5fa;}}}}
  *{{box-sizing:border-box}} body{{margin:0;font-family:-apple-system,Segoe UI,Roboto,"PingFang SC",sans-serif;color:var(--fg);background:var(--bg)}}
  header{{padding:16px 22px 0}} h1{{font-size:19px;margin:0 0 2px}} .sub{{color:var(--mut);font-size:12.5px;margin:0 0 12px}}
  nav{{display:flex;gap:6px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--line);padding:0 22px}}
  .tab{{appearance:none;background:none;border:none;border-bottom:2px solid transparent;color:var(--mut);font-size:13.5px;padding:9px 12px;cursor:pointer;font-family:inherit}}
  .tab:hover{{color:var(--fg)}} .tab.on{{color:var(--acc);border-bottom-color:var(--acc);font-weight:600}}
  .docs{{margin-left:auto;display:flex;gap:14px;font-size:12.5px}} .docs a{{color:var(--mut);text-decoration:none}} .docs a:hover{{color:var(--acc)}}
  .view{{width:100%;height:calc(100vh - 112px);border:none;background:var(--bg)}}
</style></head>
<body>
  <header><h1>Inflection Discovery — results dashboard</h1>
    <p class="sub">Earnings / narrative turnaround finder · point-in-time backtest (discrimination probe) + live discovery</p></header>
  <nav>{tabs}
    <span class="docs">
      <a href="comparison-report.md">comparison report ↗</a>
      <a href="akshare-integration.md">akshare notes ↗</a>
      <a href="../docs/plans/2026-06-28-inflection-discovery-design.md">design spec ↗</a>
    </span></nav>
  {frames}
  <script>
    var tabs = document.querySelectorAll('.tab');
    tabs.forEach(function (b) {{
      b.addEventListener('click', function () {{
        tabs.forEach(function (x) {{ x.classList.remove('on'); }});
        b.classList.add('on');
        document.querySelectorAll('.view').forEach(function (v) {{ v.style.display = 'none'; }});
        document.getElementById('f-' + b.dataset.key).style.display = 'block';
      }});
    }});
  </script>
</body></html>"""

(HERE / "dashboard.html").write_text(html)
print("wrote reports/dashboard.html", f"({len(html)} bytes; inlined {len(TABS)} reports)")
