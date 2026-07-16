#!/usr/bin/env python3
"""P4 sync: merge an IBKR positions payload into the state home's portfolio.yaml.

Contract: skills/analyzing-stocks/references/decision-records.md
Design:   docs/plans/2026-07-13-scheduled-monitoring-design.md

Deterministic core of the P4 scheduled-monitoring layer. The scheduled session
dumps the connector's get_account_positions JSON to a file; this script owns
every mapping and write decision (the LLM never edits portfolio.yaml by hand).
Merging is pinned to one account (--account); rows in other accounts are never
matched, updated, or closed. Absent rows are quarantined to suspected_closed:,
never deleted. Pure stdlib + PyYAML.

Exit codes: 0 clean run (with or without changes), 2 environment error.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("sync_portfolio.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Reuse the decision-records vocabulary so the two never drift.
from validate_records import (  # noqa: E402
    SYMBOL_PATTERNS,
    as_date,
    is_canonical,
    is_number,
    resolve_home,
)


# ----------------------------- payload parsing -----------------------------

_MONTHS = {m: i + 1 for i, m in enumerate(
    ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}

_STOCK_RE = re.compile(r"^(?P<ticker>[A-Z0-9][A-Z0-9.\-]{0,9})(?: @(?P<exch>[A-Z]+))?$")
_OPTION_RE = re.compile(
    r"^(?P<u>[A-Z0-9][A-Z0-9.\-]{0,9}) "
    r"(?P<mon>[A-Z][a-z]{2})(?P<day>\d{1,2})'(?P<yy>\d{2}) "
    r"(?P<strike>\d+(?:\.\d+)?) "
    r"(?P<right>CALL|PUT)(?: @(?P<exch>[A-Z]+))?$")


def parse_description(desc: object) -> "dict | None":
    """Structure an IBKR contract_description, or None when unparseable."""
    if not isinstance(desc, str):
        return None
    match = _OPTION_RE.match(desc)
    if match:
        month = _MONTHS.get(match.group("mon"))
        if month is None:
            return None
        try:
            expiry = datetime.date(2000 + int(match.group("yy")), month,
                                   int(match.group("day")))
        except ValueError:
            return None
        return {"asset": "option", "underlying": match.group("u"),
                "expiry": expiry, "strike": float(match.group("strike")),
                "right": match.group("right"), "exchange": match.group("exch")}
    match = _STOCK_RE.match(desc)
    if match:
        return {"asset": "stock", "ticker": match.group("ticker"),
                "exchange": match.group("exch")}
    return None


def canonical_for(parsed: "dict | None", existing_symbols: "set[str]") -> "str | None":
    """Deterministic canonical symbol for a parsed stock description.

    Bare ticker -> US; @ASX -> .AX; @KRX -> adopt .KS/.KQ when an existing
    row already holds this code with that suffix (KOSPI/KOSDAQ is not
    inferable from the payload); @SEHK -> zero-padded .HK (assumed form —
    unverified until an HK row is observed live; see design §mapping).
    Anything else, or a result that is not canonical, -> None (caller emits
    needs_mapping).
    """
    if not parsed or parsed.get("asset") != "stock":
        return None
    ticker, exch = parsed["ticker"], parsed.get("exchange")
    candidate: "str | None" = None
    if exch is None:
        candidate = ticker
    elif exch == "ASX":
        candidate = f"{ticker}.AX"
    elif exch == "KRX":
        for suffix in (".KS", ".KQ"):
            if f"{ticker}{suffix}" in existing_symbols:
                candidate = f"{ticker}{suffix}"
                break
    elif exch == "SEHK":
        if ticker.isdigit():
            candidate = f"{ticker.zfill(4)}.HK"
    if candidate is not None and is_canonical(candidate):
        return candidate
    return None


def default_kind(right: str, qty: float) -> str:
    side = "long" if qty > 0 else "short"
    return f"{side}-{right.lower()}"


# ----------------------------- merge engine -----------------------------

def _change(kind, urgency, detail, evidence, symbol=None, account=None):
    # `symbol` is always present so changes share the P1 findings shape (P1
    # findings are symbol-keyed); account-scoped findings (sync_staleness)
    # carry symbol=None and route on `account`. See DONE_WITH_CONCERNS note.
    out = {"kind": kind, "urgency": urgency, "detail": detail, "evidence": evidence,
           "symbol": symbol}
    if account is not None:
        out["account"] = account
    return out


def _needs(cid, desc, reason):
    return {"contract_id": cid, "contract_description": desc, "reason": reason}


def _pct_delta(old: float, new: float) -> float:
    if old == 0:
        return float("inf") if new != 0 else 0.0
    return abs(new - old) / abs(old) * 100.0


def _leg_key(underlying: str, expiry: object, strike: float, right: str) -> tuple:
    try:
        expiry_iso = as_date(expiry).isoformat()
    except (ValueError, TypeError):
        expiry_iso = str(expiry)
    return (underlying, expiry_iso, float(strike), right)


def _right_of(leg: dict) -> "str | None":
    kind = str(leg.get("kind", ""))
    if "put" in kind:
        return "PUT"
    if "call" in kind:
        return "CALL"
    return None


def merge(portfolio: dict, payload: dict, *, account: str,
          as_of: datetime.date, resolve_map: "dict | None" = None,
          epsilon_pct: float = 0.5, staleness_days: int = 3) -> "tuple[dict, dict]":
    """Merge a positions payload into a deep copy of `portfolio` (pinned account).

    Returns (new_portfolio, report). Never mutates the input. The report's
    `changes` mirror the P1 findings shape so notify_gate/skill consume one
    vocabulary. Matched-row numerics (qty/avg_cost/leg qty) are assumed valid
    per validate_records; malformed state homes are not this function's
    contract.
    """
    import copy as _copy

    new = _copy.deepcopy(portfolio)
    resolve_map = {int(k): v for k, v in (resolve_map or {}).items()}
    changes: list = []
    needs_mapping: list = []
    positions = [p for p in (payload.get("positions") or []) if isinstance(p, dict)]
    # Asset-class coverage: a class absent from the whole snapshot is ambiguous
    # (sold-all vs connector didn't return it), so its close pass is skipped —
    # the same "never mass-close on ambiguous evidence" rule the empty-snapshot
    # guard applies globally, at per-asset-class granularity. See CONCERNS note.
    snap_has_stk = any(p.get("asset_class") == "STK" for p in positions)
    snap_has_opt = any(p.get("asset_class") == "OPT" for p in positions)

    holdings = [h for h in (new.get("holdings") or []) if isinstance(h, dict)]
    legs = [l for l in (new.get("option_legs") or []) if isinstance(l, dict)]
    pinned_holdings = [h for h in holdings if h.get("account") == account]
    pinned_legs = [l for l in legs if l.get("account") == account]

    report_base = {"as_of": as_of.isoformat(), "account": account,
                   "guard_triggered": False}

    # Empty/implausible snapshot guard (design §account scoping).
    if not positions and (pinned_holdings or pinned_legs):
        report = dict(report_base, guard_triggered=True, changes=[],
                      needs_mapping=[], uncovered_accounts=[])
        _staleness(new, account, as_of, staleness_days, report, bump=False)
        return portfolio, report

    existing_symbols = {str(h.get("symbol")) for h in holdings if h.get("symbol")}

    by_cid_h = {h["broker_contract_id"]: h for h in pinned_holdings
                if is_number(h.get("broker_contract_id"))}
    by_sym_h = {str(h.get("symbol")): h for h in pinned_holdings}
    by_cid_l = {l["broker_contract_id"]: l for l in pinned_legs
                if is_number(l.get("broker_contract_id"))}
    by_key_l: "dict[tuple, list]" = {}
    indexable_l: "set[int]" = {id(l) for l in by_cid_l.values()}
    unkeyed_loose: "set[tuple]" = set()
    for leg in pinned_legs:
        right = _right_of(leg)
        keyable = bool(leg.get("underlying")) and is_number(leg.get("strike")) and bool(right)
        if keyable:
            try:
                as_date(leg.get("expiry"))
            except (ValueError, TypeError):
                keyable = False
        if keyable:
            by_key_l.setdefault(
                _leg_key(str(leg["underlying"]), leg.get("expiry"),
                         leg["strike"], right), []).append(leg)
            indexable_l.add(id(leg))
        elif id(leg) not in indexable_l:
            # Never-indexable: no broker_contract_id and no derivable
            # (underlying, expiry, strike, right) key. Such a leg can never
            # match a payload row, so quarantining it as "absent" would be a
            # false close; it is exempted from the close pass, left in place,
            # and surfaced for one-time owner resolution instead.
            needs_mapping.append(_needs(
                leg.get("broker_contract_id"),
                "option_leg " + " ".join(str(leg.get(k)) for k in
                                         ("underlying", "strike", "expiry", "kind")),
                "leg not indexable (kind/strike/expiry unmappable); left in place"))
            if leg.get("underlying") and is_number(leg.get("strike")):
                try:
                    unkeyed_loose.add((str(leg["underlying"]),
                                       as_date(leg.get("expiry")).isoformat(),
                                       float(leg["strike"])))
                except (ValueError, TypeError):
                    pass

    matched_h: "set[int]" = set()   # id() of matched holding rows
    matched_l: "set[int]" = set()

    for pos in positions:
        cid = pos.get("contract_id")
        desc = pos.get("contract_description")
        asset = pos.get("asset_class")
        qty = pos.get("position")
        avg = pos.get("average_price")
        cur = pos.get("currency")
        if not is_number(qty) or not is_number(avg):
            needs_mapping.append(_needs(cid, desc, "non-numeric position/average_price"))
            continue

        if asset == "STK":
            parsed = parse_description(desc)
            symbol = resolve_map.get(cid) if is_number(cid) else None
            row = by_cid_h.get(cid)
            if row is None and symbol is None:
                symbol = canonical_for(parsed, existing_symbols)
            if row is None and symbol is not None:
                row = by_sym_h.get(symbol)
            if row is None and symbol is None:
                needs_mapping.append(_needs(cid, desc, "canonical symbol unresolvable"))
                continue
            if row is not None:
                # Mark seen BEFORE the currency-mismatch bail-out (mirrors the
                # OPT branch) so an unreconcilable-but-present row is never
                # quarantined as closed. See DONE_WITH_CONCERNS note.
                matched_h.add(id(row))
                if row.get("currency") != cur:
                    needs_mapping.append(_needs(
                        cid, desc,
                        f"currency mismatch (row {row.get('currency')}, payload {cur})"))
                    continue
                if not is_number(row.get("broker_contract_id")) and is_number(cid):
                    row["broker_contract_id"] = cid
                old_qty, old_avg = row.get("qty"), row.get("avg_cost")
                delta = max(_pct_delta(float(old_qty), float(qty)),
                            _pct_delta(float(old_avg), float(avg)))
                if delta > 0:
                    below = delta <= epsilon_pct
                    row["qty"], row["avg_cost"] = qty, round(float(avg), 4)
                    changes.append(_change(
                        "position_resized", "watch",
                        f"qty {old_qty} -> {qty} (avg_cost {old_avg} -> {row['avg_cost']})",
                        {"qty_before": old_qty, "qty_after": qty,
                         "below_epsilon": below}, symbol=str(row["symbol"])))
            else:
                new_row = {"symbol": symbol, "qty": qty,
                           "avg_cost": round(float(avg), 4), "currency": cur,
                           "account": account}
                if is_number(cid):
                    new_row["broker_contract_id"] = cid
                holdings.append(new_row)
                matched_h.add(id(new_row))
                existing_symbols.add(symbol)
                changes.append(_change(
                    "position_new", "review",
                    f"new position {qty} @ {round(float(avg), 4)} {cur}",
                    {"qty": qty, "avg_cost": round(float(avg), 4)}, symbol=symbol))

        elif asset == "OPT":
            parsed = parse_description(desc)
            if not parsed or parsed.get("asset") != "option":
                needs_mapping.append(_needs(cid, desc, "option description unparseable"))
                continue
            underlying = resolve_map.get(cid) if is_number(cid) else None
            if underlying is None:
                underlying = canonical_for(
                    {"asset": "stock", "ticker": parsed["underlying"],
                     "exchange": None if parsed.get("exchange") in
                     (None, "AMEX", "CBOE", "SMART") else parsed.get("exchange")},
                    existing_symbols)
            if underlying is None:
                needs_mapping.append(_needs(cid, desc, "underlying unresolvable"))
                continue
            row = by_cid_l.get(cid)
            rows = [row] if row is not None else by_key_l.get(
                _leg_key(underlying, parsed["expiry"], parsed["strike"],
                         parsed["right"]), [])
            if len(rows) > 1:
                total = sum(float(l.get("qty") or 0) for l in rows)
                for l in rows:
                    matched_l.add(id(l))
                if total != float(qty):
                    needs_mapping.append(_needs(
                        cid, desc,
                        f"contract nets {qty} but {len(rows)} rows sum to {total:g};"
                        " allocation is the owner's call"))
                continue
            if rows:
                leg = rows[0]
                matched_l.add(id(leg))
                if leg.get("currency") != cur:
                    needs_mapping.append(_needs(
                        cid, desc,
                        f"currency mismatch (row {leg.get('currency')}, payload {cur})"))
                    continue
                if not is_number(leg.get("broker_contract_id")) and is_number(cid):
                    leg["broker_contract_id"] = cid
                old_qty = leg.get("qty")
                if float(old_qty) != float(qty):
                    leg["qty"] = qty
                    changes.append(_change(
                        "option_leg_resized", "watch",
                        f"{underlying} {parsed['strike']:g} {parsed['right']} "
                        f"{parsed['expiry'].isoformat()}: qty {old_qty} -> {qty}",
                        {"qty_before": old_qty, "qty_after": qty,
                         "below_epsilon": False}, symbol=underlying))
                if "premium" in leg:
                    leg["premium"] = round(float(avg), 4)
            else:
                if (underlying, parsed["expiry"].isoformat(),
                        float(parsed["strike"])) in unkeyed_loose:
                    # This contract lines up with a never-indexable pinned leg
                    # on underlying/expiry/strike; creating a default-kind row
                    # would duplicate it. Owner resolves the leg first.
                    needs_mapping.append(_needs(
                        cid, desc,
                        "matches an unindexable portfolio leg on underlying/"
                        "expiry/strike; resolve that leg before merging"))
                    continue
                new_leg = {"kind": default_kind(parsed["right"], float(qty)),
                           "underlying": underlying, "strike": parsed["strike"],
                           "expiry": parsed["expiry"], "qty": qty,
                           "premium": round(float(avg), 4), "currency": cur,
                           "multiplier": 100, "account": account}
                if is_number(cid):
                    new_leg["broker_contract_id"] = cid
                legs.append(new_leg)
                matched_l.add(id(new_leg))
                changes.append(_change(
                    "option_leg_new", "review",
                    f"new leg {new_leg['kind']} {underlying} {parsed['strike']:g} "
                    f"exp {parsed['expiry'].isoformat()} qty {qty}",
                    {"qty": qty, "premium": new_leg["premium"]}, symbol=underlying))

        else:
            needs_mapping.append(_needs(cid, desc, f"unsupported asset_class {asset!r}"))

    # Close pass: pinned rows the snapshot no longer contains -> quarantine.
    # Removal is identity-based (id()) — matching is by identity throughout,
    # and value-equal duplicate rows must not shadow each other. Legs that
    # never entered an index are exempt: "absent" is unprovable for them
    # (routed to needs_mapping above and left in place).
    suspected = [s for s in (new.get("suspected_closed") or []) if isinstance(s, dict)]
    closed_ids: "set[int]" = set()
    for row in pinned_holdings:
        if snap_has_stk and id(row) not in matched_h:
            closed_ids.add(id(row))
            suspected.append(dict(row, suspected_closed_on=as_of.isoformat()))
            changes.append(_change(
                "position_closed", "review",
                f"absent from {account} snapshot; quarantined pending confirmation",
                {"qty": row.get("qty")}, symbol=str(row.get("symbol"))))
    for leg in pinned_legs:
        if (snap_has_opt and id(leg) in indexable_l
                and id(leg) not in matched_l):
            closed_ids.add(id(leg))
            suspected.append(dict(leg, suspected_closed_on=as_of.isoformat()))
            changes.append(_change(
                "option_leg_closed", "review",
                f"leg absent from {account} snapshot; quarantined pending confirmation",
                {"strike": leg.get("strike"), "qty": leg.get("qty")},
                symbol=str(leg.get("underlying"))))
    holdings = [h for h in holdings if id(h) not in closed_ids]
    legs = [l for l in legs if id(l) not in closed_ids]

    new["holdings"] = holdings
    new["option_legs"] = legs
    if suspected:
        new["suspected_closed"] = suspected

    report = dict(report_base, changes=changes, needs_mapping=needs_mapping,
                  uncovered_accounts=[])
    _staleness(new, account, as_of, staleness_days, report, bump=True)
    return new, report


def _staleness(portfolio: dict, account: "str | None", as_of: datetime.date,
               staleness_days: int, report: dict, *, bump: bool) -> None:
    """Update pinned last_synced (bump=True) and emit uncovered/staleness info."""
    accounts = portfolio.setdefault("accounts", {})
    row_accounts = {str(h.get("account")) for h in portfolio.get("holdings") or []
                    if isinstance(h, dict) and h.get("account")}
    row_accounts |= {str(l.get("account")) for l in portfolio.get("option_legs") or []
                     if isinstance(l, dict) and l.get("account")}
    pinned = {account} if account else set()
    for name in sorted(row_accounts | set(accounts) | pinned):
        accounts.setdefault(name, {})
    if bump and account:
        accounts[account]["last_synced"] = as_of.isoformat()
    for name in sorted(accounts):
        last = accounts[name].get("last_synced")
        if name != account:
            report["uncovered_accounts"].append(
                {"account": name, "last_synced": str(last) if last else None})
        try:
            age = (as_of - as_date(last)).days if last is not None else None
        except (ValueError, TypeError):
            age = None
        if age is None or age > staleness_days:
            detail = (f"account {name} never synced" if age is None
                      else f"account {name} last synced {last} ({age}d ago)")
            report["changes"].append(_change(
                "sync_staleness", "review", detail,
                {"last_synced": str(last) if last else None, "age_days": age},
                account=name))


# ----------------------------- inference fallback -----------------------------

def infer_account(portfolio: dict, payload: dict) -> "str | None":
    """Majority-quorum account inference for manual runs without --account.

    Report-only by contract: callers must never write on an inferred account.
    """
    positions = [p for p in (payload.get("positions") or []) if isinstance(p, dict)]
    holdings = [h for h in (portfolio.get("holdings") or []) if isinstance(h, dict)]
    legs = [l for l in (portfolio.get("option_legs") or []) if isinstance(l, dict)]
    votes: "dict[str, int]" = {}
    by_cid = {}
    for row in holdings + legs:
        if is_number(row.get("broker_contract_id")) and row.get("account"):
            by_cid[row["broker_contract_id"]] = str(row["account"])
    sym_accounts: "dict[str, set]" = {}
    for row in holdings:
        if row.get("symbol") and row.get("account"):
            sym_accounts.setdefault(str(row["symbol"]), set()).add(str(row["account"]))
    existing_symbols = set(sym_accounts)
    for pos in positions:
        acct = by_cid.get(pos.get("contract_id"))
        if acct is None and pos.get("asset_class") == "STK":
            symbol = canonical_for(parse_description(pos.get("contract_description")),
                                   existing_symbols)
            owners = sym_accounts.get(symbol or "", set())
            acct = next(iter(owners)) if len(owners) == 1 else None
        if acct:
            votes[acct] = votes.get(acct, 0) + 1
    if not votes or not positions:
        return None
    best = max(sorted(votes), key=lambda a: votes[a])
    return best if votes[best] * 2 > len(positions) else None


# ----------------------------- write discipline -----------------------------

_SECTION_ORDER = ("schema", "as_of", "base_currency", "note", "cash", "accounts",
                  "holdings", "option_legs", "suspected_closed", "constraints")


def has_comment_lines(text: str) -> bool:
    # Leading-# lines only: an inline trailing comment (qty: 5  # note) is not
    # caught — a ` #` scan would false-positive on quoted values containing '#'
    # (note: 'filed #2'). The vault's git auto-commit is the backstop for any
    # lossy round-trip.
    return any(line.lstrip().startswith("#") for line in text.splitlines())


def dump_portfolio(portfolio: dict) -> str:
    ordered = {k: portfolio[k] for k in _SECTION_ORDER if k in portfolio}
    for key in portfolio:
        if key not in ordered:
            ordered[key] = portfolio[key]
    return yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True,
                          default_flow_style=False, width=88)


def write_portfolio(path: Path, portfolio: dict) -> None:
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent),
        prefix=".portfolio-", suffix=".tmp", delete=False)
    try:
        with handle:
            handle.write(dump_portfolio(portfolio))
        os.replace(handle.name, str(path))
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def emit_prices(payload: dict, resolve_map: dict, existing_symbols: "set[str]",
                out_path: Path) -> int:
    prices: "dict[str, float]" = {}
    for pos in payload.get("positions") or []:
        if not isinstance(pos, dict) or pos.get("asset_class") != "STK":
            continue
        if not is_number(pos.get("market_price")) or pos["market_price"] <= 0:
            continue
        cid = pos.get("contract_id")
        symbol = resolve_map.get(int(cid)) if is_number(cid) else None
        if symbol is None:
            symbol = canonical_for(parse_description(pos.get("contract_description")),
                                   existing_symbols)
        if symbol is not None:
            prices[symbol] = float(pos["market_price"])
    out_path.write_text(yaml.safe_dump(prices, sort_keys=True), encoding="utf-8")
    return len(prices)


# ----------------------------- rendering + CLI -----------------------------

def render_markdown(report: dict) -> str:
    lines = [f"# Portfolio Sync — {report['as_of']}", ""]
    if report.get("blocked"):
        lines += [f"**BLOCKED:** {report['blocked']}", ""]
    for change in report["changes"]:
        who = change.get("symbol") or change.get("account")
        lines.append(f"- **{who}** — {change['kind']}: {change['detail']}")
    for item in report["needs_mapping"]:
        lines.append(f"- needs mapping: {item['contract_description']!r} "
                     f"(contract {item['contract_id']}) — {item['reason']}")
    for item in report["uncovered_accounts"]:
        lines.append(f"- uncovered account {item['account']} "
                     f"(last synced {item['last_synced']})")
    return "\n".join(lines).rstrip() + "\n"


def _load_yaml_or_json(path_str: str) -> object:
    text = Path(path_str).expanduser().read_text(encoding="utf-8")
    return yaml.safe_load(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge an IBKR positions payload into portfolio.yaml.")
    parser.add_argument("--positions", help="JSON payload from get_account_positions")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--as-of", help="sync date YYYY-MM-DD (default: today)")
    parser.add_argument("--account", help="pinned broker account id (required to write)")
    parser.add_argument("--resolve", help="YAML/JSON {contract_id: canonical_symbol}")
    parser.add_argument("--emit-prices", help="write {symbol: market_price} YAML (STK only)")
    parser.add_argument("--resize-epsilon-pct", type=float, default=0.5)
    parser.add_argument("--staleness-days", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2
    path = home / "portfolio.yaml"
    if not path.exists():
        print(f"portfolio.yaml not found in {home}", file=sys.stderr)
        return 2

    if args.as_of:
        try:
            as_of = as_date(args.as_of)
        except (ValueError, TypeError):
            print(f"--as-of is not an ISO date: {args.as_of!r}", file=sys.stderr)
            return 2
    else:
        as_of = datetime.date.today()

    raw_text = path.read_text(encoding="utf-8-sig")
    try:
        portfolio = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        print(f"portfolio.yaml is not valid YAML: {exc}", file=sys.stderr)
        return 2
    if not isinstance(portfolio, dict):
        print("portfolio.yaml is not a mapping", file=sys.stderr)
        return 2

    resolve_map: dict = {}
    if args.resolve and Path(args.resolve).expanduser().exists():
        try:
            loaded = _load_yaml_or_json(args.resolve)
        except (yaml.YAMLError, OSError) as exc:
            print(f"--resolve file unreadable, ignoring: {exc}", file=sys.stderr)
            loaded = None
        if isinstance(loaded, dict):
            for k, v in loaded.items():
                try:
                    resolve_map[int(k)] = str(v)
                except (ValueError, TypeError):
                    print(f"--resolve: ignoring un-coercible key {k!r}", file=sys.stderr)

    payload: "dict | None" = None
    if args.positions:
        try:
            loaded = json.loads(Path(args.positions).expanduser()
                                .read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"--positions unreadable: {exc}", file=sys.stderr)
            return 2
        if not isinstance(loaded, dict) or not isinstance(
                loaded.get("positions"), list):
            print("--positions must be a JSON object with a positions[] list",
                  file=sys.stderr)
            return 2
        payload = loaded

    account = args.account
    inferred = None
    write_allowed = bool(account) and not args.dry_run
    if payload is not None and not account:
        inferred = infer_account(portfolio, payload)
        account = inferred  # report-only below

    if payload is None:
        # Degraded mode: freshness accounting only.
        report = {"as_of": as_of.isoformat(), "account": account,
                  "guard_triggered": False, "changes": [], "needs_mapping": [],
                  "uncovered_accounts": [], "mode": "degraded"}
        shadow = copy.deepcopy(portfolio)
        _staleness(shadow, account or "", as_of, args.staleness_days, report,
                   bump=False)
        report["uncovered_accounts"] = [
            u for u in report["uncovered_accounts"] if u["account"]]
        merged = portfolio
        wrote = False
        blocked = None
    elif account is None:
        print("no --account and inference found no majority; report-only, "
              "nothing written", file=sys.stderr)
        report = {"as_of": as_of.isoformat(), "account": None, "mode": "unpinned",
                  "guard_triggered": False, "changes": [], "needs_mapping": [],
                  "uncovered_accounts": []}
        merged, wrote, blocked = portfolio, False, None
    else:
        merged, report = merge(
            portfolio, payload, account=account, as_of=as_of,
            resolve_map=resolve_map, epsilon_pct=args.resize_epsilon_pct,
            staleness_days=args.staleness_days)
        report["mode"] = "synced" if write_allowed else "report-only"
        blocked = None
        wrote = False
        if has_comment_lines(raw_text):
            blocked = ("portfolio.yaml contains comment lines; move them into "
                       "note: fields before sync can write (design §write discipline)")
        elif write_allowed and not report["guard_triggered"] and merged != portfolio:
            merged["as_of"] = as_of.isoformat()
            write_portfolio(path, merged)
            wrote = True

    report["blocked"] = blocked
    report["wrote"] = wrote
    if inferred is not None:
        report["inferred_account"] = inferred

    if args.emit_prices and payload is not None:
        existing = {str(h.get("symbol")) for h in merged.get("holdings") or []
                    if isinstance(h, dict) and h.get("symbol")}
        report["prices_emitted"] = emit_prices(
            payload, resolve_map, existing, Path(args.emit_prices).expanduser())

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
