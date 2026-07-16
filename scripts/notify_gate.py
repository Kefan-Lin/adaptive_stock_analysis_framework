#!/usr/bin/env python3
"""P4 notify gate: edge-trigger dedup between sweeps and notifications.

Design: docs/plans/2026-07-13-scheduled-monitoring-design.md §notify_gate.py

P1 findings are level-triggered (a crossed trigger fires every run while spot
stays crossed). This script owns the run-over-run notify-state so a standing
condition notifies once, then stays silent until it clears and recurs, or
escalates. Sync diff changes are edge-triggered by construction and always
pass. A `blocked` sync (comment guard) always notifies. The state also keeps
run timestamps: a gap wider than --max-gap-hours means scheduled runs went
missing, which always notifies.

Exit codes: 0 clean run, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

_URGENCY_ORDER = {"act": 0, "review": 1, "watch": 2}
_MAX_RUNS_KEPT = 40


def finding_key(item: dict) -> str:
    """Stable identity for dedup (design §notify_gate: stable finding keys)."""
    if "reason" in item and "contract_id" in item:  # needs_mapping entry
        cid = item.get("contract_id")
        # Unkeyable option legs arrive with contract_id=None (Task 2 merge
        # engine). Falling back to their description keeps two such legs
        # distinct so they notify and clear independently.
        if cid is None:
            return f"{item.get('contract_description')}|needs_mapping"
        return f"{cid}|needs_mapping"
    who = item.get("symbol") or item.get("account")
    kind = item.get("kind")
    ev = item.get("evidence") or {}
    if kind == "price_trigger":
        return f"{who}|{kind}|{ev.get('group')}|{ev.get('level')}"
    if kind == "review_expiry":
        return f"{who}|{kind}|{ev.get('review_by')}"
    if kind == "earnings_proximity":
        return f"{who}|{kind}|{ev.get('next_earnings')}"
    if kind == "options_assignment":
        return f"{who}|{kind}|{ev.get('strike')}|{ev.get('expiry')}"
    return f"{who}|{kind}"


_EDGE_KINDS = ("position_new", "position_closed", "position_resized",
               "option_leg_new", "option_leg_closed", "option_leg_resized")


def decide(sweep: dict, sync: dict, state: dict, *, now: datetime.datetime,
           max_gap_hours: float) -> "tuple[dict, dict]":
    """Return (decision, new_state). Pure; callers own file I/O."""
    old = (state or {}).get("findings") or {}
    runs = list((state or {}).get("runs") or [])

    new_items, escalated, standing = [], [], []
    always = []
    current: "dict[str, dict]" = {}

    level_items = list(sweep.get("findings") or [])
    level_items += [c for c in (sync.get("changes") or [])
                    if c.get("kind") == "sync_staleness"]
    level_items += list(sync.get("needs_mapping") or [])

    for item in level_items:
        key = finding_key(item)
        urgency = item.get("urgency", "review")
        entry = {"key": key, "item": item}
        prev = old.get(key)
        first = (prev or {}).get("first_notified") or now.isoformat()
        current[key] = {"urgency": urgency, "first_notified": first,
                        "last_seen": now.isoformat()}
        if prev is None:
            new_items.append(entry)
        elif _URGENCY_ORDER.get(urgency, 9) < _URGENCY_ORDER.get(
                prev.get("urgency"), 9):
            escalated.append(entry)
        else:
            current[key]["urgency"] = prev.get("urgency")
            if _URGENCY_ORDER.get(urgency, 9) > _URGENCY_ORDER.get(
                    prev.get("urgency"), 9):
                current[key]["urgency"] = urgency  # de-escalation tracked, silent
            standing.append(entry)

    for change in sync.get("changes") or []:
        if change.get("kind") in _EDGE_KINDS and not (
                change.get("evidence") or {}).get("below_epsilon"):
            always.append({"key": finding_key(change), "item": change})

    cleared = [{"key": key, "item": old[key]} for key in sorted(old)
               if key not in current]

    missed_gap = None
    if runs:
        try:
            last = datetime.datetime.fromisoformat(runs[-1])
            gap = (now - last).total_seconds() / 3600.0
            if gap > max_gap_hours:
                missed_gap = round(gap, 2)
        except ValueError:
            pass
    runs = (runs + [now.isoformat()])[-_MAX_RUNS_KEPT:]

    blocked = sync.get("blocked")
    notify = bool(new_items or escalated or always or blocked or
                  missed_gap is not None)
    decision = {"notify": notify, "new": new_items + always,
                "escalated": escalated, "standing": standing,
                "cleared": cleared, "blocked": blocked,
                "missed_gap_hours": missed_gap}
    return decision, {"findings": current, "runs": runs}


def _load(path_str: "str | None", fallback: dict) -> dict:
    if not path_str:
        return fallback
    path = Path(path_str).expanduser()
    if not path.exists():
        return fallback
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else fallback


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Edge-trigger notify gate.")
    parser.add_argument("--findings", help="morning_check --format json output")
    parser.add_argument("--changes", help="sync_portfolio --format json output")
    parser.add_argument("--state", required=True, help="monitoring/state.json path")
    parser.add_argument("--run-id", default="", help='e.g. "2026-07-13 am"')
    parser.add_argument("--now", help="ISO datetime (default: system now)")
    parser.add_argument("--max-gap-hours", type=float, default=36.0)
    args = parser.parse_args(argv)

    try:
        sweep = _load(args.findings, {"findings": []})
        sync = _load(args.changes, {"changes": [], "needs_mapping": [],
                                    "blocked": None})
        state = _load(args.state, {})
    except (OSError, json.JSONDecodeError) as exc:
        print(f"input unreadable: {exc}", file=sys.stderr)
        return 2

    if args.now:
        try:
            now = datetime.datetime.fromisoformat(args.now)
        except ValueError:
            print(f"--now is not ISO: {args.now!r}", file=sys.stderr)
            return 2
    else:
        now = datetime.datetime.now()

    decision, new_state = decide(sweep, sync, state, now=now,
                                 max_gap_hours=args.max_gap_hours)
    if args.run_id:
        new_state["last_run_id"] = args.run_id
    state_path = Path(args.state).expanduser()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(new_state, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    print(json.dumps(decision, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
