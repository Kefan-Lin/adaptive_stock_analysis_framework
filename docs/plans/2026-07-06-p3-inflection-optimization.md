# P3 Inflection-Discovery Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the audited flaws in the inflection-discovery branch and wire it into the framework per the P3 roadmap (discover → `debating-stocks` trap gate → `analyzing-stocks` → `mode: new-idea` decision records), so the branch merges into main with CI green and honest reporting.

**Architecture:** Work happens on branch `p3-optimize` (P3 tip `1745ee2` + main `c119e65` already merged; `.gitignore` resolved). Three phases: (1) merge-enabling — CI-safe test split, artifact hygiene, code minors; (2) methodology honesty — dead-name/ADV metric fixes, backtest rerun, report v4 corrections; (3) roadmap wiring — canonical symbols on the candidate contract, debate-gated routing, record hand-off. Merge to main at the end.

**Tech Stack:** Python (package: pandas/yfinance/requests/bs4/akshare, pytest-style tests in `inflection_discovery/tests/`); repo tests stay stdlib `unittest` + PyYAML only. Two interpreters: `.venv/bin/python` (PyYAML-only, mirrors main CI) and `.venv-p3/bin/python` (package deps).

**Audit sources (read for context, do not re-derive):** methodology findings C1/C2/I1/I2/M1–M4 and engineering findings are summarized in the Task descriptions below; the audited branch report is `reports/comparison-report.md` (v3).

---

## Execution Rules

- One task per commit (Task 8 may produce two). No unrelated cleanup.
- TDD for every code task: failing test → watch fail → implement → watch pass → commit.
- Package tests run with `.venv-p3/bin/python -m pytest`; repo tests with `.venv/bin/python -m unittest`. NEVER the global interpreter.
- CI-sim gate before every commit that touches `tests/` or `.github/`: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py'` must pass (this venv has only PyYAML, mirroring main CI).
- Privacy: fictional examples only in repo files; no personal holdings/paths.
- Commit messages: plain imperative; end with the `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` footer.
- Network calls allowed in Task 8 (rerun) and network-gated tests only; everything else must work offline.

## File Structure

| Path | Action | Responsibility |
| --- | --- | --- |
| `inflection_discovery/tests/` | Create (move 7 files) | package tests, pytest, deps required |
| `tests/test_contract.py` | Keep in place | pandas-free contract schema tests (main CI) |
| `tests/test_discovering_inflections_contract.py` | Create | string-level skill contract tests (main CI) |
| `.github/workflows/ci.yml` | Modify | add `inflection-tests` job |
| `inflection_discovery/scorecard/score.py` | Modify | `_yoy` positive-base guard |
| `inflection_discovery/harness/__init__.py` | Modify | drop eager pandas imports |
| `inflection_discovery/harness/canary.py` | Modify | offline soft-fail |
| `inflection_discovery/edgar.py` | Modify | SEC UA placeholder guard |
| `inflection_discovery/pit/prices.py` | Modify | dead-name gap detection; `median_dollar_adv` |
| `inflection_discovery/harness/backtest.py` + `llm_backtest.py` | Modify | ADV eligibility filter + `excluded_illiquid` |
| `inflection_discovery/symbols.py` | Create | canonical-symbol bridge (bare code → `.SH/.SZ/.BJ`, HK pad, US pass) |
| `inflection_discovery/contract.py` | Modify | `symbol`/`market` fields + validation + `make_routing` |
| `skills/discovering-inflections/SKILL.md` | Modify | debate-gated Stage 3 + record hand-off + updated claims |
| `skills/discovering-inflections/agents/openai.yaml` | Create | platform parity (mirror sibling skills) |
| `scripts/validate_repo.py` | Modify | register the skill in FULL_REQUIRED |
| `reports/sample_holdout.py` | Create | seeded, reproducible holdout sampler (for the NEXT holdout) |
| `reports/comparison-report.md` | Modify | v4: rerun tables + C1/C2/M1–M4 corrections |
| `docs/plans/2026-06-28-inflection-discovery-design.md` | Modify | spec sync where promises change |

---

### Task 1: Branch setup — DONE by orchestrator

`p3-optimize` created from `1745ee2`, `main` merged, `.gitignore` resolved as union, merge committed. This plan document is committed on the branch. No action.

---

### Task 2: Environment + test relocation + network gating

**Files:**
- Create: `.venv-p3` (local only), `inflection_discovery/tests/` (move 7 test files)
- Modify: moved test files' internal paths; add skip guards
- Keep: `tests/test_contract.py` (stays for main CI)

- [x] **Step 1: Create the package venv and copy the data cache**

```bash
python3 -m venv .venv-p3 && .venv-p3/bin/pip install --quiet -r inflection_discovery/requirements.txt pytest
cp -R "/Users/kefanlin/Desktop/personal_projects/adaptive_stock_analysis_framework/.claude/worktrees/compassionate-thompson-93ff22/.cache_inflection" .cache_inflection 2>/dev/null || echo "no cache to copy"
echo ".venv-p3/" >> .gitignore
```

Expected: pip succeeds; cache copied (speeds Task 8; gitignored).

- [x] **Step 2: Confirm the current red state (CI-sim fails before the move)**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
```

Expected: errors (`ModuleNotFoundError: No module named 'pandas'`) — this is the bug being fixed.

- [x] **Step 3: Move the 7 pandas-dependent test files**

```bash
mkdir -p inflection_discovery/tests
git mv tests/test_ashare.py tests/test_canary.py tests/test_live_akshare.py tests/test_llm_backtest.py tests/test_metrics.py tests/test_pit_fundamentals.py tests/test_scorecard.py inflection_discovery/tests/
```

(`tests/test_contract.py` stays — it is pandas-free and guards the candidate schema in main CI.)

- [x] **Step 4: Fix repo-relative paths inside the moved files**

The moved files sit one directory deeper. `grep -n "parents\[1\]" inflection_discovery/tests/*.py` and change each to `parents[2]` (e.g. `test_llm_backtest.py:19` `REPORTS = Path(__file__).resolve().parents[1] / "reports"` → `parents[2]`). Verify no other relative assumptions: `grep -n "Path(__file__)" inflection_discovery/tests/*.py`.

- [x] **Step 5: Gate network tests behind an env flag**

At the top of each module that hits the live network (`test_canary.py`, `test_ashare.py`, `test_live_akshare.py`) add:

```python
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_NETWORK_TESTS"),
    reason="live-network test; set RUN_NETWORK_TESTS=1 to run",
)
```

If a module mixes offline and live tests, apply the marker per-test instead of module-wide — inspect each and keep genuinely offline assertions unguarded.

- [x] **Step 6: Verify both suites**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv-p3/bin/python -m pytest inflection_discovery/tests tests/test_contract.py -q
```

Expected: unittest suite ALL PASS (172 main tests + test_contract); pytest passes with network tests SKIPPED.

- [x] **Step 7: Commit**

```bash
git add -A tests inflection_discovery/tests .gitignore
git commit -m "Split package tests out of main CI's discovery path; gate live-network tests"
```

---

### Task 3: CI job for the package suite

**Files:**
- Modify: `.github/workflows/ci.yml`

- [x] **Step 1: Append the job** (same indentation level as `test:`):

```yaml
  inflection-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install package dependencies
        run: pip install -r inflection_discovery/requirements.txt pytest
      - name: Package tests (offline subset)
        run: python -m pytest inflection_discovery/tests -v
```

- [x] **Step 2: Sanity-check the workflow parses and CI-sim still green**

```bash
.venv/bin/python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
```

Expected: `yaml ok`; main suite passes.

- [x] **Step 3: Commit** — `git add .github/workflows/ci.yml && git commit -m "Add CI job running the inflection package tests with real dependencies"`

---

### Task 4: Artifact hygiene — generated outputs out of git

**Files:**
- Delete from tracking (keep generators + fixtures): `reports/*.html`, `reports/backtest_results*.json`, `reports/holdout_results.json`, `excalidraw.log`
- Modify: `.gitignore`

- [x] **Step 1: Untrack generated outputs**

```bash
git rm --cached reports/ab_compare.html reports/ashare_curves.html reports/backtest.html reports/dashboard.html reports/price_curves.html reports/backtest_results.json reports/backtest_results_A.json reports/backtest_results_A_top20.json reports/backtest_results_v2.json reports/holdout_results.json excalidraw.log
```

KEEP tracked (test fixtures / provenance / docs): `inflection_discovery/benchmark/benchmark.csv`, `reports/llm_scores.json`, `reports/llm_holdout_scores.json`, `reports/holdout_universe.json`, `reports/*.md`, `reports/make_*.py`, `reports/run_holdout.py`.

- [x] **Step 2: Ignore them going forward** — append to `.gitignore`:

```
reports/*.html
reports/backtest_results*.json
reports/holdout_results.json
*.log
```

- [x] **Step 3: Verify fixtures still resolve**

```bash
.venv-p3/bin/python -m pytest inflection_discovery/tests/test_llm_backtest.py -q
git status --short | head -20
```

Expected: pass (fixtures untouched); deletions + .gitignore staged, no stray changes.

- [x] **Step 4: Commit** — `git commit -am "Untrack generated report artifacts and stray log; keep fixtures and generators"`

---

### Task 5: Code minors — `_yoy` guard, lazy harness imports, offline-soft canaries, SEC UA guard

**Files:**
- Modify: `inflection_discovery/scorecard/score.py`, `inflection_discovery/harness/__init__.py`, `inflection_discovery/harness/canary.py`, `inflection_discovery/edgar.py`
- Test: `inflection_discovery/tests/test_scorecard.py`, `inflection_discovery/tests/test_canary.py`, new asserts

- [x] **Step 1: Failing test — `_yoy` on a negative prior base emits nothing**

Append to `inflection_discovery/tests/test_scorecard.py` (match its existing synthetic-frame style):

```python
def test_yoy_skips_negative_prior_base():
    import pandas as pd
    from inflection_discovery.scorecard.score import _yoy
    idx = pd.to_datetime(["2024-03-31", "2025-03-31"])
    s = pd.Series([-10.0, 5.0], index=idx)
    out = _yoy(s)
    assert idx[1] not in out.index, "negative prior base must not produce a sign-flipped growth rate"
```

Run: `.venv-p3/bin/python -m pytest inflection_discovery/tests/test_scorecard.py::test_yoy_skips_negative_prior_base -q` → FAIL (currently returns −1.5).

- [x] **Step 2: Fix `_yoy`** — in `score.py` (~line 50) replace the base guard:

```python
        # Growth vs a non-positive base is sign-flipped/meaningless (loss-making
        # EPS, negative OCF): only compute the ratio off a strictly positive base.
        if series[prior] > 0:
            g = series[e] / series[prior] - 1.0
            out[e] = max(clip_range[0], min(clip_range[1], g))
```

Run the test → PASS. Run the whole scorecard file → all pass.

- [x] **Step 3: Lazy harness imports.** Replace `inflection_discovery/harness/__init__.py` with:

```python
"""Harness namespace. Submodules import pandas; import them directly
(`from inflection_discovery.harness import metrics`) so that pandas-free
consumers can import the package without the heavy dependencies."""
```

Then fix any `from inflection_discovery.harness import X` usages found by:
`grep -rn "from inflection_discovery.harness import\|from .harness import" inflection_discovery reports tests skills` — point each at the submodule (e.g. `from inflection_discovery.harness.backtest import run_backtest`).

- [x] **Step 4: Offline-soft canaries.** In `canary.py`, wrap each network-dependent canary body (the SEC/yfinance fetches, e.g. `filing_lag_canary` ~line 41) so a fetch failure returns a failed-but-not-raised result, matching the file's existing result type:

```python
    try:
        ...existing body...
    except Exception as exc:  # offline / SEC throttled: fail soft, never crash the battery
        return CanaryResult(name="filing_lag", passed=False, detail=f"unreachable: {exc}")
```

(Adapt `CanaryResult(...)` to the module's actual result constructor — read the file first.) Add a test in `test_canary.py` (offline, unguarded by the network marker) that monkeypatches the fetch function to raise and asserts `run_battery()` returns without raising and marks that canary failed.

- [x] **Step 5: SEC UA guard.** In `edgar.py`, at the single choke point where HTTP requests are issued (grep `SEC_USER_AGENT`), insert before the request:

```python
    if "contact@example.com" in SEC_USER_AGENT:
        raise RuntimeError(
            "Set SEC_USER_AGENT='<project> <your-email>' before live SEC calls "
            "(SEC fair-access policy; the placeholder UA gets throttled)."
        )
```

Offline test (monkeypatch the env/constant, assert `RuntimeError` on the fetch entry function without any network I/O).

- [x] **Step 6: Verify both suites + commit**

```bash
.venv-p3/bin/python -m pytest inflection_discovery/tests tests/test_contract.py -q
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
git commit -am "Guard _yoy base, soften offline canaries, lazy harness imports, require real SEC UA"
```

---

### Task 6: Dead-name fix — trading-gap truncation in `forward_return` (audit I2)

**Files:**
- Modify: `inflection_discovery/pit/prices.py` (`forward_return`, line ~60)
- Test: `inflection_discovery/tests/test_pit_fundamentals.py` or new `inflection_discovery/tests/test_prices.py`

Recycled tickers (BBBY) make yfinance serve a NEW entity's prices under the old symbol, so the spec's "dead name contributes its realized loss" is violated (−35% instead of ≈−100%).

- [x] **Step 1: Failing test** (offline, synthetic — new file `inflection_discovery/tests/test_prices.py`):

```python
import pandas as pd
import pytest

from inflection_discovery.pit import prices


def _frame(dates, closes):
    idx = pd.to_datetime(dates)
    return pd.DataFrame({"Close": closes, "Volume": [1e6] * len(idx)}, index=idx)


def test_forward_return_truncates_at_trading_gap(monkeypatch):
    # Old entity trades to 2023-05 at pennies; ticker recycled 2025-09 at $5.
    dates = list(pd.bdate_range("2022-06-01", "2023-05-01")) + list(pd.bdate_range("2025-09-01", "2026-07-01"))
    closes = [10.0] * 232 + [0.08] + [5.0] * (len(dates) - 233)
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, closes))
    r = prices.forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12)
    assert r is not None and r <= -0.9, f"recycled ticker must not mask the collapse, got {r}"


def test_forward_return_no_gap_unchanged(monkeypatch):
    dates = pd.bdate_range("2022-01-01", "2023-12-31")
    monkeypatch.setattr(prices, "_raw_history", lambda t: _frame(dates, [10.0] * len(dates)))
    r = prices.forward_return("OK", pd.Timestamp("2022-06-30"), months=12)
    assert r == pytest.approx(0.0)
```

Adjust the `closes` construction so the last pre-gap close is 0.08 (count the bdate_range length at test-writing time — compute it in the test instead of hardcoding 232: `n_old = len(pd.bdate_range("2022-06-01", "2023-05-01")); closes = [10.0]*(n_old-1) + [0.08] + [5.0]*...`). Run → first test FAILS (returns ≈ −0.5 from the recycled $5).

- [x] **Step 2: Implement gap truncation** in `forward_return` after `fut = df[df.index <= end_date]["Close"].dropna()`:

```python
    window = fut[fut.index > T]
    if len(window) >= 2:
        gaps = window.index.to_series().diff()
        breaks = gaps[gaps > pd.Timedelta(days=30)]
        if not breaks.empty:
            # Trading stopped for 30+ days inside the window: the original line
            # died (delisting); anything after is a recycled ticker or relist.
            # Realize the loss at the last pre-gap close (spec: dead names
            # contribute their realized loss, never a successor's prices).
            window = window[window.index < breaks.index[0]]
            fut = window
```

(Keep the existing `fut.empty` guard after this; if truncation empties the window, fall through to the pre-existing behavior of using the last close ≤ T+months from before T — i.e. return None as today.) Run tests → PASS.

- [x] **Step 3: Recycled-ticker canary** (network-gated). In `canary.py`, add to the battery:

```python
def recycled_ticker_canary() -> "CanaryResult":
    """BBBY died in 2023; its ticker was recycled. forward_return must realize
    the collapse, not the successor entity's price."""
    try:
        r = forward_return("BBBY", pd.Timestamp("2022-06-30"), months=12)
        ok = r is not None and r <= -0.9
        return CanaryResult(name="recycled_ticker", passed=ok, detail=f"BBBY 12m fwd = {r}")
    except Exception as exc:
        return CanaryResult(name="recycled_ticker", passed=False, detail=f"unreachable: {exc}")
```

(Adapt constructor/registration to the module's existing pattern.)

- [x] **Step 4: Verify + commit**

```bash
.venv-p3/bin/python -m pytest inflection_discovery/tests -q
git add -A && git commit -m "Floor dead names at their last pre-gap close; add recycled-ticker canary"
```

---

### Task 7: ADV liquidity haircut (audit I1 — spec promise, unimplemented)

**Files:**
- Modify: `inflection_discovery/pit/prices.py` (new helper), `inflection_discovery/harness/backtest.py` + `inflection_discovery/harness/llm_backtest.py` (eligibility), `inflection_discovery/scorecard/taxonomy.py` (threshold constant)
- Test: `inflection_discovery/tests/test_prices.py`, `inflection_discovery/tests/test_metrics.py`

- [x] **Step 1: Failing tests**

```python
def test_median_dollar_adv(monkeypatch):
    dates = pd.bdate_range("2024-01-01", "2024-06-30")
    df = pd.DataFrame({"Close": [10.0] * len(dates), "Volume": [200_000] * len(dates)}, index=dates)
    monkeypatch.setattr(prices, "pit_prices", lambda t, T, lookback_days=None: df)
    adv = prices.median_dollar_adv("X", pd.Timestamp("2024-06-30"))
    assert adv == pytest.approx(2_000_000.0)


def test_median_dollar_adv_empty(monkeypatch):
    monkeypatch.setattr(prices, "pit_prices", lambda t, T, lookback_days=None: pd.DataFrame())
    assert prices.median_dollar_adv("X", pd.Timestamp("2024-06-30")) is None
```

Run → FAIL (`median_dollar_adv` undefined).

- [x] **Step 2: Implement the helper** in `pit/prices.py`:

```python
def median_dollar_adv(ticker: str, T, days: int = 60) -> Optional[float]:
    """Median daily dollar volume over the trailing `days` sessions as of T.

    Point-in-time (uses pit_prices). None when no data — callers treat None as
    'cannot verify liquidity' and exclude, counting the name, never guessing.
    """
    df = pit_prices(ticker, T, lookback_days=days * 3)
    if df is None or df.empty or "Close" not in df or "Volume" not in df:
        return None
    tail = df.tail(days)
    dv = (tail["Close"] * tail["Volume"]).dropna()
    return float(dv.median()) if len(dv) else None
```

Run → PASS.

- [x] **Step 3: Threshold in the taxonomy.** In `scorecard/taxonomy.py`, next to `TRAP_CEILING`, add:

```python
# Spec §Metrics liquidity haircut: names whose trailing-60-session median
# dollar volume at the as-of date is below this are not costlessly investable;
# they are excluded from top-N eligibility and counted as excluded_illiquid.
MIN_ADV_USD = 1_000_000.0
```

- [x] **Step 4: Wire into eligibility.** Read `harness/backtest.py` `score_universe`/`evaluate_row` and `harness/llm_backtest.py` (~line 100, where `passes_A_gate` and the trap ceiling gate top-N membership). At the same gate, exclude names with `median_dollar_adv(ticker, date) or 0.0) < MIN_ADV_USD` — treating `None` as excluded — and collect them into an `excluded_illiquid` list surfaced in `summarize`'s output next to `excluded_no_data`. Add a metrics-level test in `test_metrics.py` with synthetic candidates where one name fails only the ADV gate: assert it is absent from top-N and present in `excluded_illiquid`.

- [x] **Step 5: Spec sync.** In `docs/plans/2026-06-28-inflection-discovery-design.md` §Metrics, change "A liquidity haircut / minimum-ADV filter is applied" to state the concrete rule: trailing-60-session median dollar ADV ≥ $1M at the as-of date, else excluded and counted (`excluded_illiquid`).

- [x] **Step 6: Verify + commit**

```bash
.venv-p3/bin/python -m pytest inflection_discovery/tests -q
git add -A && git commit -m "Implement the spec's minimum-ADV liquidity haircut with excluded-illiquid accounting"
```

---

### Task 8: Rerun the backtests and publish report v4 (audit C1, C2, M1–M4)

**Files:**
- Create: `reports/sample_holdout.py` (seeded sampler for future holdouts)
- Modify: `reports/comparison-report.md` (v4), `skills/discovering-inflections/SKILL.md` (claims paragraph), `reports/run_holdout.py` (median + sensitivity output)
- Regenerated (untracked): `reports/backtest_results*.json`, `reports/holdout_results.json`

This task needs network. Export `SEC_USER_AGENT="inflection-discovery-research <contact-email>"` before running (the orchestrator supplies the real contact address at dispatch time — never commit it); the cache in `.cache_inflection/` makes reruns mostly cache-hits.

- [x] **Step 1: Extend `run_holdout.py` output** with, per arm: mean, **median**, per-name table, leave-one-out and leave-two-out (drop the 1–2 largest winners) means, and a `ceiling_boundary` note listing any cleared name whose `trap` equals `TRAP_CEILING` exactly. Pure-python additions to its existing summary dict; no scoring changes (scores stay the frozen `llm_holdout_scores.json`).

- [x] **Step 2: Write the seeded sampler** `reports/sample_holdout.py`:

```python
"""Reproducible holdout sampler (audit C2). Usage:
    python reports/sample_holdout.py --source <ticker-list.txt> --n 16 --seed 20260706 --out reports/holdout_universe_next.json
Writes {"_meta": {"seed":…, "source":…, "sha256":…, "generated":…}, "tickers":[…]}.
The source file must be a point-in-time listing snapshot (one ticker per line);
its sha256 is recorded so the draw is verifiable."""
```

Implement with `argparse` + `random.Random(seed).sample`; record `_meta` exactly as documented. Offline unit test (`inflection_discovery/tests/test_sample_holdout.py`): same seed + source → identical draw; `_meta.sha256` matches the file.

- [x] **Step 3: Rerun engine B, the A harness, and the holdout returns** with the Task-6/7 metric layer:

```bash
export SEC_USER_AGENT="inflection-discovery-research kflin1996+sec@gmail.com"
.venv-p3/bin/python -m inflection_discovery.cli backtest 2>/dev/null || .venv-p3/bin/python -c "import json; from inflection_discovery.harness.backtest import run_backtest, summarize; r = run_backtest(); print(json.dumps(summarize(r), indent=2))" > reports/backtest_results_v4.json
.venv-p3/bin/python -c "from inflection_discovery.harness import llm_backtest"  # then run its main per its __main__ block
.venv-p3/bin/python reports/run_holdout.py > reports/holdout_results_v4.json
```

(Read `cli.py` and each module's `__main__` for the real entry points before running; the commands above show intent, use the actual interfaces. Results land as untracked JSON — fine, the report tables are the durable artifact.)

- [x] **Step 4: Update `reports/comparison-report.md` to v4.** Required content:
  1. New A-vs-B and B tables from the rerun (post-ADV, post-dead-name numbers), each noting `excluded_illiquid` counts.
  2. **C1 correction block** in the holdout section: cleared/flagged shown as mean AND median; leave-one/two-out sensitivity; the LESL `trap = 0.70 = TRAP_CEILING` inclusive-boundary fact; explicit sentence that the trap-screen split is **two-name-fragile and threshold-boundary-dependent — treat as suggestive, not validated**.
  3. **C2 reproducibility disclaimer**: the 2026-01-31 holdout's sampling is not reproducible (no seed/source committed; evidence file not in repo; scores+results same commit) and the pool is survivorship-filtered; future holdouts must use `reports/sample_holdout.py`.
  4. One-line disclosures: price-only returns vs dividend-heavy control (~1.6pp, conservative); "top-10 picks" = surfaced labeled positives, not a tradeable basket; control arm fixed at 2023-06-30 ref-date (effective n 53–65 by date); A scores are hand-authored frozen files (no runtime LLM loop).
- [x] **Step 5: Sync the SKILL.md claims paragraph** ("What this does and does not claim") to the v4 numbers and the downgraded holdout language — the current text says "trap/quality screen generalized"; it must now say the blind trap-screen evidence is suggestive but two-name-fragile (C1) and non-reproducible (C2).

- [x] **Step 6: Verify + commit (two commits)**

```bash
.venv-p3/bin/python -m pytest inflection_discovery/tests -q
git add reports/sample_holdout.py inflection_discovery/tests/test_sample_holdout.py reports/run_holdout.py
git commit -m "Add seeded holdout sampler; holdout output gains median and sensitivity"
git add reports/comparison-report.md skills/discovering-inflections/SKILL.md docs/plans/2026-06-28-inflection-discovery-design.md
git commit -m "Report v4: rerun with ADV+dead-name metrics; downgrade holdout claims per audit"
```

---

### Task 9: Canonical-symbol bridge on the candidate contract

**Files:**
- Create: `inflection_discovery/symbols.py`
- Modify: `inflection_discovery/contract.py`, `inflection_discovery/ashare/discover.py` (~lines 78–101), `inflection_discovery/live/discover.py`
- Test: `tests/test_contract.py` (stays pandas-free), new `inflection_discovery/tests/` case if pandas needed

- [x] **Step 1: Failing tests** — append to `tests/test_contract.py` (stdlib-only):

```python
def test_canonical_symbol_bridge():
    from inflection_discovery.symbols import canonical_symbol
    assert canonical_symbol("600519", exchange="SSE") == ("600519.SH", "CN")
    assert canonical_symbol("000001", exchange="SZSE") == ("000001.SZ", "CN")
    assert canonical_symbol("430047", exchange="BSE") == ("430047.BJ", "CN")
    assert canonical_symbol("700", exchange="HKEX") == ("0700.HK", "HK")
    assert canonical_symbol("AXTI") == ("AXTI", "US")


def test_symbol_patterns_match_repo_validator():
    """The bridge must stay in lockstep with scripts/validate_records.py."""
    import importlib.util, pathlib
    from inflection_discovery.symbols import SYMBOL_PATTERNS as PKG
    spec = importlib.util.spec_from_file_location(
        "validate_records", pathlib.Path(__file__).resolve().parents[1] / "scripts" / "validate_records.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert {k: p.pattern for k, p in PKG.items()} == {k: p.pattern for k, p in mod.SYMBOL_PATTERNS.items()}
```

Note: `scripts/validate_records.py` imports `yaml` at module level — if `exec_module` fails on that in the pandas-free venv, PyYAML IS installed there (main venv), so it works; in `.venv-p3` install pyyaml too (`pip install pyyaml`). Run → FAIL (module missing).

- [x] **Step 2: Implement `inflection_discovery/symbols.py`:**

```python
"""Canonical-symbol bridge (decision-records contract, spec §Canonical Symbol Form).

Providers speak bare codes (akshare: 600519); the framework's records layer
speaks canonical identities (600519.SH). SYMBOL_PATTERNS mirrors
scripts/validate_records.py verbatim; a contract test keeps them in lockstep.
"""
from __future__ import annotations

import re
from typing import Tuple

SYMBOL_PATTERNS = {
    "US": re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,2})?$"),
    "HK": re.compile(r"^\d{4,5}\.HK$"),
    "CN": re.compile(r"^\d{6}\.(SH|SZ|BJ)$"),
    "KR": re.compile(r"^\d{6}\.(KS|KQ)$"),
    "AU": re.compile(r"^[A-Z0-9]{1,6}\.AX$"),
}

_CN_SUFFIX = {"SSE": ".SH", "SZSE": ".SZ", "BSE": ".BJ"}


def canonical_symbol(code: str, exchange: str = "") -> Tuple[str, str]:
    """Return (canonical_symbol, market) for a provider code + exchange hint."""
    code = code.strip().upper()
    if exchange in _CN_SUFFIX and code.isdigit() and len(code) == 6:
        sym = code + _CN_SUFFIX[exchange]
        return sym, "CN"
    if exchange in ("HKEX", "SEHK") and code.isdigit():
        sym = code.zfill(4) + ".HK" if len(code) <= 4 else code + ".HK"
        return sym, "HK"
    for market, pattern in SYMBOL_PATTERNS.items():
        if pattern.match(code):
            return code, market
    raise ValueError(f"cannot canonicalize {code!r} (exchange={exchange!r})")
```

Run tests → PASS.

- [x] **Step 3: Extend the candidate contract.** In `contract.py`: add fields `symbol: str = ""` and `market: str = ""` to `Candidate`; in `validate()`, when `symbol` is non-empty require `market` present and `SYMBOL_PATTERNS[market].match(symbol)` (import from `.symbols`); extend `make_routing(ticker, exchange="", currency="USD")` to call `canonical_symbol` (fall back to `(ticker, "US")` on ValueError with the error recorded — never crash routing) and include `"symbol"`/`"market"` keys. Update `ashare/discover.py` (`score_one_ashare` emits `exchange="SSE"/"SZSE"`) and `live/discover.py` to pass their exchange through. Add validator tests to `tests/test_contract.py` (bad: `symbol="600519"`+`market="CN"` → violation; good: `"600519.SH"`).

- [x] **Step 4: Verify + commit**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv-p3/bin/python -m pytest inflection_discovery/tests tests/test_contract.py -q
git add -A && git commit -m "Candidates carry canonical symbol+market; bridge locksteps with records validator"
```

---

### Task 10: Debate-gated routing + record hand-off in the skill

**Files:**
- Modify: `skills/discovering-inflections/SKILL.md` (Stage 3)
- Create: `tests/test_discovering_inflections_contract.py` (stdlib-only, runs in main CI)

- [x] **Step 1: Failing contract tests** — new `tests/test_discovering_inflections_contract.py`:

```python
"""String-level contract tests for the discovering-inflections skill wiring (P3)."""
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "discovering-inflections" / "SKILL.md"


class DiscoveringInflectionsWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_stage3_routes_through_debating_stocks_trap_gate(self) -> None:
        self.assertIn("debating-stocks", self.text)
        self.assertIn("value-trap", self.text)

    def test_survivors_become_new_idea_records(self) -> None:
        self.assertIn("mode: new-idea", self.text)
        self.assertIn("decision-records", self.text)
        self.assertIn("INDEX.md", self.text)

    def test_candidates_use_canonical_symbols(self) -> None:
        self.assertIn("canonical", self.text)
        self.assertIn("600519.SH", self.text)


if __name__ == "__main__":
    unittest.main()
```

Run: `.venv/bin/python -m unittest tests.test_discovering_inflections_contract -v` → FAIL.

- [x] **Step 2: Rewrite Stage 3** in `SKILL.md` (replace the current "### Stage 3 — Rank and route" block):

```markdown
### Stage 3 — Rank, debate-gate, route, record

1. **Rank** eligible candidates (pass A gate, trap_risk under ceiling, ADV
   floor) by `D`.
2. **Debate gate (mandatory for anything that will be routed):** for each
   top-N candidate, run `$debating-stocks` as the value-trap gate — the
   candidate contract's `evidence` and `thesis` are the debate brief; the
   question is "genuine inflection or value trap / head-fake?". This is the
   judgment layer the backtest showed free numeric signals cannot provide.
   A candidate whose verdict is trap/likely-trap stops here (log it with the
   verdict's cruxes; do not route).
3. **Route survivors** to `$analyzing-stocks` using the `routing` block
   (exchange, currency, tradable line, `suggested_style = turnaround`) plus
   the `thesis` as scope. Candidates carry canonical `symbol` + `market`
   (e.g. akshare `600519` → `600519.SH`) per
   `skills/analyzing-stocks/references/decision-records.md`.
4. **Record:** when a private state home is configured (see
   [decision-records](../analyzing-stocks/references/decision-records.md)
   resolution rules), offer to persist each routed survivor as a
   `mode: new-idea` decision record plus its `INDEX.md` row, so discovery
   output lands in the same per-symbol timeline the decision workflow reads.
```

- [x] **Step 3: Run tests + both suites; commit**

```bash
.venv/bin/python -m unittest tests.test_discovering_inflections_contract -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
git add -A && git commit -m "Wire Stage 3: debate-gated routing and new-idea record hand-off"
```

---

### Task 11: Platform parity + repo registration

**Files:**
- Create: `skills/discovering-inflections/agents/openai.yaml`
- Modify: `scripts/validate_repo.py` (FULL_REQUIRED), `tests/test_discovering_inflections_contract.py`

- [x] **Step 1: Failing test** — append to `tests/test_discovering_inflections_contract.py`:

```python
    def test_skill_registered_and_platform_complete(self) -> None:
        openai_yaml = SKILL.parent / "agents" / "openai.yaml"
        self.assertTrue(openai_yaml.exists(), "missing agents/openai.yaml for platform parity")
        validator = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("discovering-inflections", validator)
```

Run → FAIL.

- [x] **Step 2: Create `agents/openai.yaml`** by mirroring an existing sibling exactly (read `skills/analyzing-stocks/agents/openai.yaml` first and copy its shape — name, description, entry point — with this skill's values). Register the skill: add its SKILL.md (and openai.yaml if siblings are listed too — match how siblings appear) to `FULL_REQUIRED` in `scripts/validate_repo.py`.

- [x] **Step 3: Verify** — new test passes; `.venv/bin/python scripts/validate_repo.py --profile full` passes; `bash tests/test_install.sh` passes (the new skill installs via the glob).

- [x] **Step 4: Commit** — `git commit -am "Register discovering-inflections: openai.yaml parity and full-profile validation"`

---

### Task 12: Final verification + merge to main

- [x] **Step 1: Full gate**

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | tail -3
.venv-p3/bin/python -m pytest inflection_discovery/tests tests/test_contract.py -q
.venv/bin/python scripts/validate_repo.py --profile full
.venv/bin/python scripts/validate_records.py --home tests/fixtures/state-home
bash tests/test_install.sh
```

Expected: all pass. The first command is the CI-sim (PyYAML-only) — it is the merge gate.

- [x] **Step 2: Merge** (orchestrator, after final review): `git -C <main-root> merge p3-optimize`, rerun the gate on main, push per user's standing preference.

- [x] **Step 3: Update memory + report** — orchestrator closes out.

## Spec Coverage Map

| Audit finding | Task |
| --- | --- |
| ENG-Critical CI red (pandas imports) | 2, 3 |
| ENG artifacts/log in git | 4 |
| ENG `_yoy`, offline canaries, lazy imports, SEC UA | 5 |
| I2 dead-name/recycled ticker | 6 |
| I1 ADV haircut | 7 |
| C1 holdout fragility (median/sensitivity/ceiling) | 8 |
| C2 reproducibility (sampler + disclosure) | 8 |
| M1–M4 disclosures | 8 |
| ENG canonicalization gap (bare codes ↛ records) | 9 |
| ENG P3 wiring gap (debate gate, records) | 10 |
| ENG platform parity/registration | 11 |
