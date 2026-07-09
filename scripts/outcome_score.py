#!/usr/bin/env python3
"""P2 outcome-scoring: score past decision records against realized prices.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-09-outcome-scoring-design.md

Forward-only measurement harness. The deterministic core (this script) loads
every real decision record, fetches historical closes through an injectable
PriceHistory, scores each matured 90/180/365-day window (absolute
native-currency return, direction-hit vs stance, WFV/scenario convergence,
price-trigger touch), and aggregates a calibration report grouped by fields the
records already carry. The outcome-scoring skill narrates on top. Live history
(yfinance/akshare) is lazily imported so the pyyaml-only test job stays
dependency-free.

Exit codes: 0 clean run, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("outcome_score.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse P0 loaders/vocabulary and the P1 provider mapping so nothing drifts.
from validate_records import (  # noqa: E402
    SYMBOL_PATTERNS,
    as_date,
    is_number,
    resolve_home,
)
from morning_check import load_frontmatter, provider_for  # noqa: E402

WINDOWS_DEFAULT = (90, 180, 365)
CLOSE_LOOKBACK_DAYS = 7   # nearest prior trading day tolerance for close_on
HOLD_BAND = 0.10          # |return| band for a Hold with no scenarios
LOW_N = 3                 # calibration buckets below this are flagged low_n


# ----------------------------- price history -----------------------------
# A per-symbol series is {date: (close, low, high)}. FileHistory sets
# low == high == close; LiveHistory carries the true daily range.

def _pick_close(series: dict, target: datetime.date) -> "float | None":
    candidates = [d for d in series
                  if d <= target and (target - d).days <= CLOSE_LOOKBACK_DAYS]
    return series[max(candidates)][0] if candidates else None


def _pick_low_high(series: dict, start: datetime.date, end: datetime.date):
    rows = [v for d, v in series.items() if start <= d <= end]
    if not rows:
        return (None, None)
    return (min(r[1] for r in rows), max(r[2] for r in rows))


class FileHistory:
    """Historical closes from a {symbol: {YYYY-MM-DD: close}} mapping.

    Backs offline tests and the owner-provided-close fallback. Window low/high
    are approximated by the min/max of the supplied closes in range.
    """

    def __init__(self, closes: dict) -> None:
        self._series: "dict[str, dict]" = {}
        for symbol, points in (closes or {}).items():
            series: dict = {}
            for day, price in (points or {}).items():
                if not is_number(price):
                    continue
                try:
                    d = as_date(day)
                except (ValueError, TypeError):
                    continue
                series[d] = (float(price), float(price), float(price))
            self._series[str(symbol)] = series

    def prefetch(self, symbol: str, start: datetime.date, end: datetime.date) -> None:
        return None  # nothing to fetch; data is already in memory

    def close_on(self, symbol: str, target: datetime.date) -> "float | None":
        return _pick_close(self._series.get(symbol) or {}, target)

    def low_high(self, symbol: str, start: datetime.date, end: datetime.date):
        return _pick_low_high(self._series.get(symbol) or {}, start, end)


# ----------------------------- record loading -----------------------------

def load_all_records(home: Path) -> "list[dict]":
    """Every real, scorable decision record in the state home.

    Skips INDEX.md, unparseable frontmatter, and records lacking a positive
    price_at_decision or a valid date. `historical` rows live only in INDEX.md,
    so forward-only falls out for free.
    """
    out: "list[dict]" = []
    root = home / "records"
    if not root.exists():
        return out
    for symbol_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(symbol_dir.glob("*.md")):
            if path.name == "INDEX.md":
                continue
            meta = load_frontmatter(path)
            if not isinstance(meta, dict):
                continue
            price = meta.get("price_at_decision")
            if not is_number(price) or price <= 0:
                continue
            try:
                as_date(meta.get("date"))
            except (ValueError, TypeError):
                continue
            meta["symbol"] = meta.get("symbol") or symbol_dir.name
            out.append(meta)
    return out


# ----------------------------- scoring primitives -----------------------------

def _direction_hit(stance, ret, exit_price, scenarios) -> "bool | None":
    """Did the realized move vindicate the stance? None when unscoreable."""
    if stance in ("Buy", "Add"):
        return ret > 0
    if stance in ("Reduce", "Avoid"):
        return ret < 0
    if stance == "Hold":
        if isinstance(scenarios, dict) and is_number(scenarios.get("bear")) \
                and is_number(scenarios.get("bull")):
            return scenarios["bear"] <= exit_price <= scenarios["bull"]
        return abs(ret) <= HOLD_BAND
    return None


def _wfv(p0, exit_price, wfv):
    """(gap_closed, converged) toward weighted_fair_value, or None.

    gap_closed is the fraction of the initial |price - WFV| gap that closed
    (1.0 = reached WFV, negative = moved away). converged requires closing the
    gap *and* moving in the WFV direction (not overshooting the wrong way).
    None when WFV is absent or the price already sits at fair value.
    """
    if not is_number(wfv) or p0 == wfv:
        return None
    before = abs(p0 - wfv)
    after = abs(exit_price - wfv)
    gap_closed = (before - after) / before
    moved_right_way = ((exit_price - p0) > 0) == ((wfv - p0) > 0)
    return (round(gap_closed, 4), bool(gap_closed > 0 and moved_right_way))


def _scenario_landing(exit_price, scenarios) -> "str | None":
    bear = scenarios.get("bear")
    base = scenarios.get("base")
    bull = scenarios.get("bull")
    if not all(is_number(x) for x in (bear, base, bull)):
        return None
    if exit_price < bear:
        return "below_bear"
    if exit_price <= base:
        return "bear_base"
    if exit_price <= bull:
        return "base_bull"
    return "above_bull"


def _trigger_touches(triggers, low, high) -> "list[dict]":
    """Per price trigger, whether its level was touched in the window.

    `below` triggers are touched when the window low reached the level; `above`
    triggers when the window high reached it. `touched` is None when the range
    is unavailable (a data gap on the range, not a false negative).
    """
    out: "list[dict]" = []
    for group in ("add_on", "trim_exit"):
        for item in (triggers or {}).get(group) or []:
            if not isinstance(item, dict) or item.get("type") != "price":
                continue
            level = item.get("level")
            direction = item.get("direction")
            if not is_number(level) or direction not in ("above", "below"):
                continue
            if direction == "below":
                touched = None if low is None else bool(low <= level)
            else:
                touched = None if high is None else bool(high >= level)
            out.append({"group": group, "level": level,
                        "direction": direction, "touched": touched})
    return out


# ----------------------------- per-record scoring -----------------------------

def score_record(meta: dict, history, as_of: datetime.date, windows):
    """Score one record. Returns (record | None, pending[], data_gaps[])."""
    symbol = meta["symbol"]
    p0 = float(meta["price_at_decision"])
    d = as_date(meta["date"])
    stance = meta.get("stance")
    scenarios = meta.get("scenarios")
    wfv = meta.get("weighted_fair_value")
    triggers = meta.get("triggers") or {}

    win_results: "dict[str, dict]" = {}
    pending: "list[dict]" = []
    gaps: "list[dict]" = []
    for w in windows:
        target = d + datetime.timedelta(days=w)
        if as_of < target:
            pending.append({"symbol": symbol, "date": d.isoformat(),
                            "window": w, "matures_on": target.isoformat()})
            continue
        exit_price = history.close_on(symbol, target)
        if exit_price is None:
            gaps.append({"symbol": symbol, "date": d.isoformat(), "window": w,
                         "reason": f"no close near {target.isoformat()}"})
            continue
        ret = (exit_price - p0) / p0
        res: dict = {"exit_price": exit_price, "return": round(ret, 4),
                     "direction_hit": _direction_hit(stance, ret, exit_price, scenarios)}
        wfv_res = _wfv(p0, exit_price, wfv)
        if wfv_res is not None:
            res["gap_closed"], res["converged"] = wfv_res
        if isinstance(scenarios, dict):
            landing = _scenario_landing(exit_price, scenarios)
            if landing is not None:
                res["scenario_landing"] = landing
        low, high = history.low_high(symbol, d, target)
        touches = _trigger_touches(triggers, low, high)
        if touches:
            res["trigger_touches"] = touches
        win_results[str(w)] = res

    record = None
    if win_results:
        record = {
            "symbol": symbol, "date": d.isoformat(), "mode": meta.get("mode"),
            "stance": stance, "confidence": meta.get("confidence"),
            "valuation_zone": meta.get("valuation_zone"), "market": meta.get("market"),
            "price_at_decision": p0, "windows": win_results,
        }
    return record, pending, gaps


def evaluate_home(home: Path, history, as_of: datetime.date,
                  windows=WINDOWS_DEFAULT) -> dict:
    records = load_all_records(home)
    by_symbol: "dict[str, list[dict]]" = {}
    for meta in records:
        by_symbol.setdefault(meta["symbol"], []).append(meta)

    scored: "list[dict]" = []
    pending: "list[dict]" = []
    gaps: "list[dict]" = []
    max_window = max(windows)
    for symbol in sorted(by_symbol):
        metas = by_symbol[symbol]
        dates = [as_date(m["date"]) for m in metas]
        span_lo = min(dates)
        span_hi = min(as_of, max(d + datetime.timedelta(days=max_window) for d in dates))
        history.prefetch(symbol, span_lo, span_hi)
        for meta in sorted(metas, key=lambda m: m["date"]):
            record, p, g = score_record(meta, history, as_of, windows)
            if record is not None:
                scored.append(record)
            pending.extend(p)
            gaps.extend(g)

    return {
        "as_of": as_of.isoformat(), "windows": list(windows),
        "scored": scored, "pending": pending, "data_gaps": gaps,
        "calibration": calibrate(scored, windows),
    }


# ----------------------------- calibration -----------------------------

_DIMENSIONS = (
    ("by_stance", "stance"),
    ("by_confidence", "confidence"),
    ("by_valuation_zone", "valuation_zone"),
    ("by_market", "market"),
)


def _median(xs: "list[float]") -> "float | None":
    values = sorted(xs)
    n = len(values)
    if n == 0:
        return None
    mid = n // 2
    return values[mid] if n % 2 else (values[mid - 1] + values[mid]) / 2


def _summarize(results: "list[dict]") -> dict:
    returns = [r["return"] for r in results]
    hits = [r["direction_hit"] for r in results if r.get("direction_hit") is not None]
    convs = [r["converged"] for r in results if r.get("converged") is not None]
    return {
        "n": len(results),
        "hit_rate": round(sum(1 for h in hits if h) / len(hits), 4) if hits else None,
        "mean_return": round(sum(returns) / len(returns), 4) if returns else None,
        "median_return": round(_median(returns), 4) if returns else None,
        "wfv_convergence": round(sum(1 for c in convs if c) / len(convs), 4) if convs else None,
        "low_n": len(results) < LOW_N,
    }


def calibrate(scored: "list[dict]", windows) -> dict:
    # Flatten to (record, window, window-result) for every scored window.
    flat = [(rec, int(w), res)
            for rec in scored for w, res in rec["windows"].items()]
    out: dict = {}
    for key, field in _DIMENSIONS:
        out[key] = {}
        for w in windows:
            buckets: "dict[str, list[dict]]" = {}
            for rec, ww, res in flat:
                if ww != w:
                    continue
                bucket = rec.get(field) or "—"
                buckets.setdefault(bucket, []).append(res)
            out[key][str(w)] = {b: _summarize(v) for b, v in sorted(buckets.items())}
    out["overall"] = {}
    for w in windows:
        out["overall"][str(w)] = _summarize([res for _, ww, res in flat if ww == w])
    return out


# ----------------------------- live + chain history -----------------------------

class LiveHistory:
    """Historical closes via yfinance (US/HK/KR/AU) and akshare (CN A-shares).

    Heavy providers are imported lazily inside prefetch so importing this module
    never requires them. One fetch per symbol is cached as {date: (close, low,
    high)}; any per-name failure yields an empty series (→ data gaps).
    """

    def __init__(self) -> None:
        self._cache: "dict[str, dict]" = {}

    def prefetch(self, symbol: str, start: datetime.date, end: datetime.date) -> None:
        if symbol in self._cache:
            return
        provider, provider_symbol = provider_for(symbol)
        try:
            if provider == "akshare":
                self._cache[symbol] = self._akshare(provider_symbol, start, end)
            else:
                self._cache[symbol] = self._yfinance(provider_symbol, start, end)
        except Exception:
            self._cache[symbol] = {}

    def close_on(self, symbol: str, target: datetime.date) -> "float | None":
        return _pick_close(self._cache.get(symbol) or {}, target)

    def low_high(self, symbol: str, start: datetime.date, end: datetime.date):
        return _pick_low_high(self._cache.get(symbol) or {}, start, end)

    @staticmethod
    def _yfinance(provider_symbol: str, start: datetime.date, end: datetime.date) -> dict:
        import yfinance as yf

        # end is inclusive for our purposes; yfinance end is exclusive.
        hist = yf.Ticker(provider_symbol).history(
            start=start.isoformat(),
            end=(end + datetime.timedelta(days=1)).isoformat(),
        )
        series: dict = {}
        if hist is not None and not hist.empty:
            for ts, row in hist.iterrows():
                day = ts.date() if hasattr(ts, "date") else as_date(str(ts)[:10])
                series[day] = (float(row["Close"]), float(row["Low"]), float(row["High"]))
        return series

    @staticmethod
    def _akshare(provider_symbol: str, start: datetime.date, end: datetime.date) -> dict:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol=provider_symbol, period="daily",
            start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"),
            adjust="",
        )
        series: dict = {}
        if df is not None and len(df):
            for _, row in df.iterrows():
                day = as_date(str(row["日期"])[:10])
                series[day] = (float(row["收盘"]), float(row["最低"]), float(row["最高"]))
        return series


class ChainHistory:
    """Try `first` (e.g. owner-provided closes), then `second` (live)."""

    def __init__(self, first, second) -> None:
        self._first = first
        self._second = second

    def prefetch(self, symbol, start, end) -> None:
        self._first.prefetch(symbol, start, end)
        self._second.prefetch(symbol, start, end)

    def close_on(self, symbol, target) -> "float | None":
        value = self._first.close_on(symbol, target)
        return value if value is not None else self._second.close_on(symbol, target)

    def low_high(self, symbol, start, end):
        low, high = self._first.low_high(symbol, start, end)
        if low is not None and high is not None:
            return (low, high)
        return self._second.low_high(symbol, start, end)


# ----------------------------- rendering -----------------------------

def _fmt(value, pct=False) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%" if pct else f"{value}"


def _dimension_table(title: str, buckets: dict) -> "list[str]":
    lines = [f"**{title}**", "",
             "| bucket | N | hit-rate | mean ret | median ret | WFV conv | |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, s in buckets.items():
        flag = "low-N" if s["low_n"] else ""
        lines.append(
            f"| {name} | {s['n']} | {_fmt(s['hit_rate'], True)} | "
            f"{_fmt(s['mean_return'], True)} | {_fmt(s['median_return'], True)} | "
            f"{_fmt(s['wfv_convergence'], True)} | {flag} |")
    lines.append("")
    return lines


def render_markdown(result: dict) -> str:
    lines = [f"# Outcome Scoring — {result['as_of']}", ""]
    cal = result["calibration"]
    for w in result["windows"]:
        wk = str(w)
        overall = cal["overall"][wk]
        lines.append(f"## Window {w}d")
        lines.append(
            f"Overall: N={overall['n']}, hit-rate {_fmt(overall['hit_rate'], True)}, "
            f"mean {_fmt(overall['mean_return'], True)}, "
            f"median {_fmt(overall['median_return'], True)}, "
            f"WFV-conv {_fmt(overall['wfv_convergence'], True)}.")
        lines.append("")
        lines.extend(_dimension_table("By stance", cal["by_stance"][wk]))
        lines.extend(_dimension_table("By confidence", cal["by_confidence"][wk]))
        lines.extend(_dimension_table("By valuation zone", cal["by_valuation_zone"][wk]))
        lines.extend(_dimension_table("By market", cal["by_market"][wk]))
    if result["pending"]:
        lines.append("## Pending (not yet matured)")
        for p in result["pending"]:
            lines.append(f"- **{p['symbol']}** {p['date']} — {p['window']}d "
                         f"matures {p['matures_on']}")
        lines.append("")
    if result["data_gaps"]:
        lines.append("## Data gaps")
        for g in result["data_gaps"]:
            lines.append(f"- **{g['symbol']}** {g['date']} — {g['window']}d: {g['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ----------------------------- CLI -----------------------------

def _load_closes_file(path_str: str) -> dict:
    data = yaml.safe_load(Path(path_str).expanduser().read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _build_history(args):
    closes = _load_closes_file(args.prices) if args.prices else {}
    if args.offline:
        return FileHistory(closes)
    if closes:
        return ChainHistory(FileHistory(closes), LiveHistory())
    return LiveHistory()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Outcome-score a private investing state home's decision records.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--as-of", help="evaluation date YYYY-MM-DD (default: today)")
    parser.add_argument("--windows", default="90,180,365",
                        help="comma-separated horizon days (default: 90,180,365)")
    parser.add_argument("--prices", help="YAML/JSON {symbol: {date: close}} for offline / fallback")
    parser.add_argument("--offline", action="store_true", help="use only --prices, never the network")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2

    if args.as_of:
        try:
            as_of = as_date(args.as_of)
        except (ValueError, TypeError):
            print(f"--as-of is not an ISO date (YYYY-MM-DD): {args.as_of!r}", file=sys.stderr)
            return 2
    else:
        as_of = datetime.date.today()

    try:
        windows = tuple(int(x) for x in str(args.windows).split(",") if x.strip())
    except ValueError:
        print(f"--windows must be comma-separated integers: {args.windows!r}", file=sys.stderr)
        return 2
    if not windows:
        print("--windows produced no horizons", file=sys.stderr)
        return 2

    try:
        history = _build_history(args)
    except OSError as exc:
        print(f"could not read --prices file: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"--prices file is not valid YAML: {exc}", file=sys.stderr)
        return 2

    result = evaluate_home(home, history, as_of, windows=windows)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
