#!/usr/bin/env python3
"""Installed scorecard command; accepts fictional or private card JSON paths."""
import argparse
import json
from pathlib import Path
import sys


skill = Path(__file__).resolve().parents[1]
runtime = skill / '.scorecard-runtime'
sys.path.insert(0, str(runtime if runtime.is_dir() else skill.parents[1]))

from scorecard import (compare_snapshots, create_partial_snapshot, create_snapshot,
                       read_snapshot, validate_card)  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='Validate, save or read an exact research scorecard')
    actions = parser.add_subparsers(dest='action', required=True)
    validate = actions.add_parser('validate')
    validate.add_argument('--card', required=True, type=Path)
    create = actions.add_parser('create')
    create.add_argument('--home', required=True, type=Path)
    create.add_argument('--symbol', required=True)
    create.add_argument('--market', required=True)
    create.add_argument('--card', required=True, type=Path)
    create.add_argument('--as-of', required=True)
    create.add_argument('--baseline-id')
    create.add_argument('--change-reasons', type=Path,
                        help='JSON mapping of item IDs to reason lists for a linked full research')
    partial = actions.add_parser('partial', help='JSON request with create_partial_snapshot keyword arguments')
    partial.add_argument('--request', required=True, type=Path)
    read = actions.add_parser('read')
    read.add_argument('--home', required=True, type=Path)
    read.add_argument('--symbol', required=True)
    read.add_argument('--snapshot-id', required=True)
    compare = actions.add_parser('compare')
    compare.add_argument('--home', required=True, type=Path)
    compare.add_argument('--symbol', required=True)
    compare.add_argument('--before-id', required=True)
    compare.add_argument('--after-id', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'read':
            output = read_snapshot(args.home, args.symbol, args.snapshot_id)
        elif args.action == 'compare':
            output = compare_snapshots(args.home, args.symbol, args.before_id, args.after_id)
        elif args.action == 'partial':
            request = json.loads(args.request.read_text(encoding='utf-8'))
            result = create_partial_snapshot(**request)
            output = {'saved': result.saved, 'snapshot_id': result.snapshot_id,
                      'reason': result.reason}
        else:
            card = json.loads(args.card.read_text(encoding='utf-8'))
            if args.action == 'validate':
                output = validate_card(card)
            else:
                reasons = (json.loads(args.change_reasons.read_text(encoding='utf-8'))
                           if args.change_reasons is not None else None)
                result = create_snapshot(args.home, args.symbol, args.market, card,
                                         as_of=args.as_of, baseline_id=args.baseline_id,
                                         change_reasons=reasons)
                output = {'saved': result.saved, 'snapshot_id': result.snapshot_id,
                          'reason': result.reason}
        print(json.dumps(output, ensure_ascii=False))
        return 0 if args.action not in ('create', 'partial') or output['saved'] else 1
    except (ValueError, OSError, TypeError) as exc:
        print(f'Scorecard unavailable: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
