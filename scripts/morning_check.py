#!/usr/bin/env python3
"""P1 morning-check: sweep the state home and emit an action brief.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-09-morning-check-monitoring-design.md

The deterministic core (this script) checks price triggers, drawdown vs
scenarios, review_by expiry, next_earnings proximity, and cash-secured-put
assignment risk. The morning-check skill layers LLM KPI/event judgment on top.
Live price fetching (yfinance/akshare) is lazily imported so the pyyaml-only
test job stays dependency-free.

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
    print("morning_check.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse the decision-records loaders and symbol vocabulary so the two never drift.
from validate_records import (  # noqa: E402
    FRONTMATTER,
    MODE_PRIORITY,
    SYMBOL_PATTERNS,
    as_date,
    is_number,
    resolve_home,
)


# ----------------------------- price sources -----------------------------

def provider_for(symbol: str) -> "tuple[str, str]":
    """Map a canonical symbol to (provider, provider_symbol).

    CN A-shares (`600519.SH`) go to akshare as the bare 6-digit code; every
    other market passes through to yfinance unchanged.
    """
    if SYMBOL_PATTERNS["CN"].match(symbol):
        return "akshare", symbol.split(".")[0]
    return "yfinance", symbol


class FilePriceSource:
    """Spot prices from an in-memory {canonical_symbol: price} mapping.

    Backs both the owner-provided-quote fallback and offline tests.
    """

    def __init__(self, prices: dict) -> None:
        self._prices = {str(k): v for k, v in (prices or {}).items()}

    def spot(self, symbol: str) -> "float | None":
        value = self._prices.get(symbol)
        return float(value) if is_number(value) else None


class ChainSource:
    """Try `first`, then `second`; the first non-None spot wins."""

    def __init__(self, first, second) -> None:
        self._first = first
        self._second = second

    def spot(self, symbol: str) -> "float | None":
        value = self._first.spot(symbol)
        return value if value is not None else self._second.spot(symbol)


class LivePriceSource:
    """Live quotes via yfinance (US/HK/KR/AU) and akshare (CN A-shares).

    Heavy providers are imported lazily inside the fetch so merely importing
    this module never requires them. Any per-name failure returns None (the
    caller records a data gap) rather than raising.
    """

    def spot(self, symbol: str) -> "float | None":
        provider, provider_symbol = provider_for(symbol)
        try:
            if provider == "akshare":
                return self._akshare_spot(provider_symbol)
            return self._yfinance_spot(provider_symbol)
        except Exception:
            return None

    @staticmethod
    def _yfinance_spot(provider_symbol: str) -> "float | None":
        import yfinance as yf

        ticker = yf.Ticker(provider_symbol)
        try:
            last = ticker.fast_info.get("last_price")
            if is_number(last) and last > 0:
                return float(last)
        except Exception:
            pass
        hist = ticker.history(period="5d")
        if hist is not None and not hist.empty and "Close" in hist:
            closes = hist["Close"].dropna()
            if len(closes):
                return float(closes.iloc[-1])
        return None

    @staticmethod
    def _akshare_spot(provider_symbol: str) -> "float | None":
        import akshare as ak

        df = ak.stock_zh_a_hist(symbol=provider_symbol, period="daily", adjust="")
        if df is not None and len(df) and "收盘" in df:
            return float(df.iloc[-1]["收盘"])
        return None


# ----------------------------- state loading -----------------------------

def load_frontmatter(path: Path) -> "dict | None":
    """Parse a record's YAML frontmatter (tolerant; None if unparseable)."""
    text = path.read_text(encoding="utf-8-sig")
    match = FRONTMATTER.match(text)
    if not match:
        return None
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return meta if isinstance(meta, dict) else None


def load_portfolio(home: Path) -> dict:
    """Return the parsed portfolio.yaml, or {} when absent/unreadable."""
    path = home / "portfolio.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _latest_key(meta: dict) -> "tuple[datetime.date, int]":
    """Sort key for 'most current' record: newest date, then P0 mode priority."""
    try:
        date = as_date(meta.get("date"))
    except (ValueError, TypeError):
        date = datetime.date.min
    priority = MODE_PRIORITY.get(meta.get("mode"), 99)
    return (date, -priority)  # max() picks newest date, then lowest priority number


def load_latest_records(home: Path) -> "dict[str, dict]":
    """The latest decision record per symbol (P0 (date, mode) tie-break)."""
    latest: "dict[str, dict]" = {}
    records_root = home / "records"
    if not records_root.exists():
        return latest
    for symbol_dir in sorted(p for p in records_root.iterdir() if p.is_dir()):
        best: "dict | None" = None
        for record_path in sorted(symbol_dir.glob("*.md")):
            if record_path.name == "INDEX.md":
                continue
            meta = load_frontmatter(record_path)
            if meta is None:
                continue
            if best is None or _latest_key(meta) > _latest_key(best):
                best = meta
        if best is not None:
            latest[symbol_dir.name] = best
    return latest


def build_universe(portfolio: dict, latest: "dict[str, dict]") -> "set[str]":
    """Holdings union option underlyings union symbols with a current record."""
    universe: "set[str]" = set(latest)
    for holding in portfolio.get("holdings") or []:
        symbol = holding.get("symbol")
        if symbol:
            universe.add(str(symbol))
    for leg in portfolio.get("option_legs") or []:
        underlying = leg.get("underlying")
        if underlying:
            universe.add(str(underlying))
    return universe


# ----------------------------- checks -----------------------------

def _finding(symbol, kind, urgency, detail, evidence):
    return {"symbol": symbol, "kind": kind, "urgency": urgency,
            "detail": detail, "evidence": evidence}


def _price_trigger_findings(symbol, meta, spot):
    out = []
    triggers = meta.get("triggers") or {}
    for group in ("add_on", "trim_exit"):
        for item in triggers.get(group) or []:
            if not isinstance(item, dict) or item.get("type") != "price":
                continue
            level, direction = item.get("level"), item.get("direction")
            if not is_number(level) or direction not in ("above", "below"):
                continue
            fired = (direction == "above" and spot >= level) or \
                    (direction == "below" and spot <= level)
            if fired:
                out.append(_finding(
                    symbol, "price_trigger", "act",
                    f"{group} level {level} crossed (spot {spot} {direction})",
                    {"group": group, "level": level, "direction": direction, "spot": spot},
                ))
    return out


def _drawdown_findings(symbol, meta, spot):
    # Deterministic layer flags only the actionable bear-scenario breach; richer
    # base/bull/WFV positioning is left to the LLM layer (design §Drawdown). The
    # guard also skips research-mode records, which carry no scenarios.
    scenarios = meta.get("scenarios")
    if not isinstance(scenarios, dict) or not is_number(scenarios.get("bear")):
        return []
    if spot < scenarios["bear"]:
        return [_finding(
            symbol, "drawdown", "review",
            f"spot {spot} below bear scenario {scenarios['bear']}",
            {"spot": spot, "bear": scenarios["bear"]},
        )]
    return []


def _review_findings(symbol, meta, as_of, review_window):
    value = meta.get("review_by")
    if value is None:
        return []
    try:
        review_by = as_date(value)
    except (ValueError, TypeError):
        return []
    if review_by < as_of:
        return [_finding(
            symbol, "review_expiry", "review",
            f"review_by {review_by.isoformat()} passed ({(as_of - review_by).days}d ago)",
            {"review_by": review_by.isoformat()},
        )]
    if (review_by - as_of).days <= review_window:
        return [_finding(
            symbol, "review_expiry", "watch",
            f"review_by {review_by.isoformat()} in {(review_by - as_of).days}d",
            {"review_by": review_by.isoformat()},
        )]
    return []


def _earnings_findings(symbol, meta, as_of, earnings_window):
    value = meta.get("next_earnings")
    if value is None:
        return [], [{"symbol": symbol, "reason": "earnings date unknown — verify"}]
    try:
        earnings = as_date(value)
    except (ValueError, TypeError):
        return [], [{"symbol": symbol, "reason": f"next_earnings not a date: {value!r}"}]
    if earnings < as_of:
        return [], []  # a stale earnings date is a review_by concern, not an alert
    if (earnings - as_of).days <= earnings_window:
        return [_finding(
            symbol, "earnings_proximity", "watch",
            f"earnings in {(earnings - as_of).days}d ({earnings.isoformat()})",
            {"next_earnings": earnings.isoformat()},
        )], []
    return [], []


def _llm_todo(symbol, meta):
    out = []
    triggers = meta.get("triggers") or {}
    for group in ("add_on", "trim_exit"):
        for item in triggers.get(group) or []:
            if isinstance(item, dict) and item.get("type") in ("kpi", "event"):
                out.append({"symbol": symbol, "type": item["type"],
                            "text": item.get("text"), "trigger_group": group})
    for item in meta.get("monitor") or []:
        if isinstance(item, dict):
            out.append({"symbol": symbol, "type": "monitor", "kpi": item.get("kpi"),
                        "threshold": item.get("threshold"), "action": item.get("action")})
    return out


def _option_findings(portfolio, latest, price_source, as_of,
                     assignment_watch_pct, dte_window, data_gaps):
    out = []
    seen_gap = {g["symbol"] for g in data_gaps}
    for leg in portfolio.get("option_legs") or []:
        if not isinstance(leg, dict) or leg.get("kind") != "cash-secured-put":
            continue
        qty = leg.get("qty")
        if not is_number(qty) or qty >= 0:
            continue  # only short puts carry assignment risk
        underlying = leg.get("underlying")
        strike = leg.get("strike")
        if not underlying or not is_number(strike):
            continue
        try:
            expiry = as_date(leg.get("expiry"))
        except (ValueError, TypeError):
            continue
        dte = (expiry - as_of).days
        if dte < 0:
            continue  # expired leg; stale portfolio, not a live alert
        spot = price_source.spot(underlying)
        if spot is None:
            if underlying not in seen_gap:
                data_gaps.append({"symbol": underlying,
                                  "reason": "option underlying price unavailable"})
                seen_gap.add(underlying)
            continue
        multiplier = leg.get("multiplier") if is_number(leg.get("multiplier")) else 100
        reserve = float(strike) * float(multiplier) * abs(qty)
        in_the_money = spot <= strike
        near_strike = spot <= strike * (1 + assignment_watch_pct)
        near_expiry = dte <= dte_window
        earnings_before_expiry = False
        under_meta = latest.get(underlying)
        if under_meta and under_meta.get("next_earnings") is not None:
            try:
                earnings_before_expiry = as_date(under_meta["next_earnings"]) <= expiry
            except (ValueError, TypeError):
                earnings_before_expiry = False
        if not (in_the_money or near_strike or near_expiry or earnings_before_expiry):
            continue
        urgency = "act" if (in_the_money and near_expiry) else "watch"
        out.append(_finding(
            underlying, "options_assignment", urgency,
            f"cash-secured put {strike} (exp {expiry.isoformat()}): "
            f"spot {spot}, {dte} DTE, reserve {reserve:g}",
            {"strike": strike, "expiry": expiry.isoformat(), "dte": dte, "spot": spot,
             "reserve": reserve, "in_the_money": in_the_money, "near_strike": near_strike,
             "near_expiry": near_expiry, "earnings_before_expiry": earnings_before_expiry},
        ))
    return out


def evaluate_state(home, price_source, as_of, *, earnings_window=7, review_window=14,
                   assignment_watch_pct=0.03, dte_window=7) -> dict:
    portfolio = load_portfolio(home)
    latest = load_latest_records(home)
    findings: list = []
    data_gaps: list = []
    llm_todo: list = []

    for symbol in sorted(latest):
        meta = latest[symbol]
        llm_todo.extend(_llm_todo(symbol, meta))
        spot = price_source.spot(symbol)
        if spot is None:
            data_gaps.append({"symbol": symbol, "reason": "price fetch failed / unavailable"})
        else:
            findings.extend(_price_trigger_findings(symbol, meta, spot))
            findings.extend(_drawdown_findings(symbol, meta, spot))
        findings.extend(_review_findings(symbol, meta, as_of, review_window))
        earn_findings, earn_gaps = _earnings_findings(symbol, meta, as_of, earnings_window)
        findings.extend(earn_findings)
        data_gaps.extend(earn_gaps)

    findings.extend(_option_findings(portfolio, latest, price_source, as_of,
                                     assignment_watch_pct, dte_window, data_gaps))

    # Held names / option underlyings with no decision record cannot be monitored
    # (no thesis, no triggers) — surface them as a data gap rather than silently
    # dropping them from the sweep.
    universe = build_universe(portfolio, latest)
    already_flagged = {g["symbol"] for g in data_gaps}
    for symbol in sorted(universe - set(latest) - already_flagged):
        data_gaps.append({"symbol": symbol,
                          "reason": "held/underlying but no decision record on file"})

    order = {"act": 0, "review": 1, "watch": 2}
    findings.sort(key=lambda f: (order.get(f["urgency"], 9), f["symbol"], f["kind"]))
    return {"as_of": as_of.isoformat(), "findings": findings,
            "data_gaps": data_gaps, "llm_todo": llm_todo}


# ----------------------------- rendering + CLI -----------------------------

_URGENCY_HEADERS = [("act", "Act now"), ("review", "Review"), ("watch", "Watch")]


def render_markdown(result: dict) -> str:
    lines = [f"# Morning Check — {result['as_of']}", ""]
    for key, header in _URGENCY_HEADERS:
        hits = [f for f in result["findings"] if f["urgency"] == key]
        if hits:
            lines.append(f"## {header}")
            for f in hits:
                lines.append(f"- **{f['symbol']}** — {f['detail']}")
            lines.append("")
    if result["llm_todo"]:
        lines.append("## KPI / event checks (LLM)")
        for todo in result["llm_todo"]:
            if todo["type"] == "monitor":
                lines.append(f"- **{todo['symbol']}** — monitor {todo.get('kpi')} "
                             f"({todo.get('threshold')}): {todo.get('action')}")
            else:
                lines.append(f"- **{todo['symbol']}** — {todo['trigger_group']} "
                             f"{todo['type']}: {todo.get('text')}")
        lines.append("")
    if result["data_gaps"]:
        lines.append("## Data gaps")
        for gap in result["data_gaps"]:
            lines.append(f"- **{gap['symbol']}** — {gap['reason']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_prices_file(path_str: str) -> dict:
    data = yaml.safe_load(Path(path_str).expanduser().read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _build_source(args):
    prices = _load_prices_file(args.prices) if args.prices else {}
    if args.offline:
        return FilePriceSource(prices)
    if prices:
        return ChainSource(FilePriceSource(prices), LivePriceSource())
    return LivePriceSource()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Morning-check sweep of an investing state home.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--as-of", help="evaluation date YYYY-MM-DD (default: today)")
    parser.add_argument("--earnings-window", type=int, default=7)
    parser.add_argument("--review-window", type=int, default=14)
    parser.add_argument("--prices", help="YAML/JSON {symbol: price} for offline / fallback quotes")
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
        source = _build_source(args)
    except OSError as exc:
        print(f"could not read --prices file: {exc}", file=sys.stderr)
        return 2
    except yaml.YAMLError as exc:
        print(f"--prices file is not valid YAML: {exc}", file=sys.stderr)
        return 2

    result = evaluate_state(
        home, source, as_of,
        earnings_window=args.earnings_window, review_window=args.review_window,
    )
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
