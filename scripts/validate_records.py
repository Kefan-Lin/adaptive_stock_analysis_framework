#!/usr/bin/env python3
"""Validate a private investing state home against the decision-records contract.

Contract: skills/analyzing-stocks/references/decision-records.md
Spec:     docs/plans/2026-07-03-decision-records-design.md

Exit codes: 0 clean, 1 violations, 2 environment error.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("validate_records.py requires PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

POINTER_FILE = Path.home() / ".investing-home"

STANCES = ("Buy", "Add", "Hold", "Reduce", "Avoid")
POSITION_SIZES = ("Core", "Starter", "Speculative", "Watch-Avoid")
CONFIDENCE_LEVELS = ("High", "Medium", "Low")
CANDIDATE_TIERS = ("Core Candidate", "Tactical Candidate", "Reject")
EXECUTION_METHODS = (
    "Buy now", "Stage buy", "Sell cash-secured put", "Wait",
    "Reduce", "Exit", "No Action",
)
VALUATION_ZONES = ("Accumulation", "Hold", "Exhaustion", "Invalidation")
MODES = ("new-idea", "existing-report", "position-review", "event-review", "research")
MODE_PRIORITY = {
    "position-review": 0, "event-review": 1, "existing-report": 2,
    "new-idea": 3, "research": 4,
}
ACTIONS = ("bought", "added", "reduced", "exited", "sold-put", "put-assigned", "put-closed")
TRIGGER_TYPES = ("price", "kpi", "event")
DIRECTIONS = ("above", "below")

SYMBOL_PATTERNS = {
    "US": re.compile(r"^[A-Z]{1,6}([.\-][A-Z]{1,2})?$"),
    "HK": re.compile(r"^\d{4,5}\.HK$"),
    "CN": re.compile(r"^\d{6}\.(SH|SZ|BJ)$"),
}

REQUIRED_ALWAYS = (
    "schema", "symbol", "market", "date", "mode",
    "price_at_decision", "currency", "stance", "review_by",
)
VALUATION_GROUP = ("weighted_fair_value", "scenarios", "position_size", "confidence")
WORKFLOW_GROUP = ("candidate_tier", "valuation_zone", "execution_method", "triggers")

RECORD_FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z-]+)\.md$")
CURRENCY = re.compile(r"^[A-Z]{3}$")
# Anchored fences: the body stops at the first line that is exactly `---`,
# so `---` inside a quoted YAML value on one line cannot truncate parsing.
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.S)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_date(value: object) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        return datetime.date.fromisoformat(value)
    raise ValueError(f"not a date: {value!r}")


def is_canonical(symbol: object) -> bool:
    return isinstance(symbol, str) and any(p.match(symbol) for p in SYMBOL_PATTERNS.values())


class Checker:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.errors: list[str] = []

    def err(self, path: Path, message: str) -> None:
        try:
            rel = path.relative_to(self.home)
        except ValueError:
            rel = path
        self.errors.append(f"{rel}: {message}")

    # ---------------- records ----------------

    def load_frontmatter(self, path: Path) -> "dict | None":
        # utf-8-sig strips a leading BOM if present; identical to utf-8 otherwise.
        text = path.read_text(encoding="utf-8-sig")
        match = FRONTMATTER.match(text)
        if not match:
            self.err(path, "missing YAML frontmatter fences")
            return None
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            self.err(path, f"frontmatter is not valid YAML: {exc}")
            return None
        if not isinstance(meta, dict):
            self.err(path, "frontmatter is not a mapping")
            return None
        return meta

    def check_record(self, path: Path, symbol_dir: str) -> "dict | None":
        meta = self.load_frontmatter(path)
        if meta is None:
            return None

        missing = [key for key in REQUIRED_ALWAYS if key not in meta]
        if missing:
            self.err(path, f"missing required fields: {', '.join(missing)}")
        if meta.get("schema") != "decision-record/v1":
            self.err(path, f"schema must be decision-record/v1, got {meta.get('schema')!r}")

        symbol = meta.get("symbol")
        if symbol != symbol_dir:
            self.err(path, f"symbol {symbol!r} does not match directory {symbol_dir!r}")
        market = meta.get("market")
        if market not in SYMBOL_PATTERNS:
            self.err(path, f"market must be one of US/CN/HK, got {market!r}")
        elif not (isinstance(symbol, str) and SYMBOL_PATTERNS[market].match(symbol)):
            self.err(path, f"symbol {symbol!r} is not canonical for market {market}")

        mode = meta.get("mode")
        if mode not in MODES:
            self.err(path, f"mode must be one of {MODES}, got {mode!r}")

        match = RECORD_FILENAME.match(path.name)
        if not match:
            self.err(path, "filename must be YYYY-MM-DD-<mode>.md")
        else:
            try:
                meta_date = as_date(meta.get("date"))
                if (match.group(1), match.group(2)) != (meta_date.isoformat(), mode):
                    self.err(path, "filename does not match record identity (date, mode)")
            except (ValueError, TypeError):
                self.err(path, f"date is not ISO: {meta.get('date')!r}")

        for field, vocab in (
            ("stance", STANCES),
            ("position_size", POSITION_SIZES),
            ("confidence", CONFIDENCE_LEVELS),
            ("candidate_tier", CANDIDATE_TIERS),
            ("valuation_zone", VALUATION_ZONES),
            ("execution_method", EXECUTION_METHODS),
        ):
            value = meta.get(field)
            if value is not None and value not in vocab:
                self.err(path, f"{field} {value!r} not in vocabulary {vocab}")

        if not is_number(meta.get("price_at_decision")) or meta.get("price_at_decision", 0) <= 0:
            self.err(path, f"price_at_decision must be a positive number, got {meta.get('price_at_decision')!r}")
        if not (isinstance(meta.get("currency"), str) and CURRENCY.match(meta["currency"])):
            self.err(path, f"currency must be a 3-letter code, got {meta.get('currency')!r}")
        for field in ("review_by", "next_earnings"):
            value = meta.get(field)
            if value is not None:
                try:
                    as_date(value)
                except (ValueError, TypeError):
                    self.err(path, f"{field} is not ISO: {value!r}")

        self._check_group(path, meta, VALUATION_GROUP)
        self._check_group(path, meta, WORKFLOW_GROUP)
        self._check_scenarios(path, meta)
        self._check_triggers(path, meta)
        self._check_action_taken(path, meta)

        related = meta.get("related_symbols") or []
        if not isinstance(related, list) or any(not is_canonical(s) for s in related):
            self.err(path, f"related_symbols must be a list of canonical symbols, got {related!r}")

        source = meta.get("source_report")
        if source is not None:
            target = (self.home / str(source)).resolve()
            try:
                target.relative_to(self.home.resolve())
                resolves = target.exists()
            except ValueError:
                resolves = False
            if not resolves:
                self.err(path, f"source_report does not resolve inside the state home: {source!r}")

        return meta

    def _check_group(self, path: Path, meta: dict, group: "tuple[str, ...]") -> None:
        present = [key for key in group if meta.get(key) is not None]
        if present and len(present) != len(group):
            absent = [key for key in group if meta.get(key) is None]
            self.err(path, f"group incomplete: has {', '.join(present)} but missing {', '.join(absent)}")

    def _check_scenarios(self, path: Path, meta: dict) -> None:
        scenarios = meta.get("scenarios")
        if scenarios is None:
            return
        if not isinstance(scenarios, dict) or set(scenarios) != {"bear", "base", "bull"}:
            self.err(path, f"scenarios must have exactly bear/base/bull, got {scenarios!r}")
            return
        if any(not is_number(v) for v in scenarios.values()):
            self.err(path, f"scenarios values must be numbers, got {scenarios!r}")

    def _check_triggers(self, path: Path, meta: dict) -> None:
        triggers = meta.get("triggers")
        if triggers is None:
            return
        if not isinstance(triggers, dict) or not set(triggers) <= {"add_on", "trim_exit"}:
            self.err(path, "triggers must be a mapping with add_on/trim_exit lists")
            return
        for side, items in triggers.items():
            if not isinstance(items, list):
                self.err(path, f"triggers.{side} must be a list")
                continue
            for item in items:
                if not isinstance(item, dict) or item.get("type") not in TRIGGER_TYPES:
                    self.err(path, f"triggers.{side} item needs type in {TRIGGER_TYPES}: {item!r}")
                    continue
                if item["type"] == "price":
                    if not is_number(item.get("level")) or item.get("direction") not in DIRECTIONS:
                        self.err(path, f"price trigger needs numeric level and direction above/below: {item!r}")
                elif not isinstance(item.get("text"), str):
                    self.err(path, f"{item['type']} trigger needs text: {item!r}")

    def _check_action_taken(self, path: Path, meta: dict) -> None:
        action = meta.get("action_taken")
        if action is None:
            return
        if not isinstance(action, dict) or action.get("action") not in ACTIONS:
            self.err(path, f"action_taken.action must be in {ACTIONS}: {action!r}")
            return
        try:
            as_date(action.get("date"))
        except (ValueError, TypeError):
            self.err(path, f"action_taken.date is not ISO: {action!r}")

    # ---------------- walk ----------------

    def run(self) -> "list[str]":
        records_root = self.home / "records"
        if records_root.exists():
            for symbol_dir in sorted(p for p in records_root.iterdir() if p.is_dir()):
                if not is_canonical(symbol_dir.name):
                    self.err(symbol_dir, f"directory name {symbol_dir.name!r} is not a canonical symbol")
                for record_path in sorted(symbol_dir.glob("*.md")):
                    if record_path.name == "INDEX.md":
                        continue
                    self.check_record(record_path, symbol_dir.name)
        return self.errors


def resolve_home(arg: "str | None") -> Path:
    if arg:
        return Path(arg).expanduser()
    if POINTER_FILE.exists():
        return Path(POINTER_FILE.read_text(encoding="utf-8").strip()).expanduser()
    print(f"no --home given and {POINTER_FILE} does not exist", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an investing state home.")
    parser.add_argument("--home", help="state-home path (default: ~/.investing-home pointer)")
    parser.add_argument("--reindex", action="store_true", help="rebuild INDEX.md files, then validate")
    args = parser.parse_args()

    home = resolve_home(args.home)
    if not home.is_dir():
        print(f"state home is not a directory: {home}", file=sys.stderr)
        return 2

    errors = Checker(home).run()
    if errors:
        print("State-home validation failed:")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"State-home validation passed: {home}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
