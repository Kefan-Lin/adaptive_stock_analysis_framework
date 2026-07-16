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
