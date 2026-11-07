"""Immutable private research snapshots, independent of decision records."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

from inflection_discovery.symbols import SYMBOL_PATTERNS
from .card import RUBRIC_VERSION, validate_card


SNAPSHOT_SCHEMA_VERSION = 1
SNAPSHOT_ID = re.compile(r'^\d{4}-\d{2}-\d{2}-[0-9a-f]{32}$')
STORAGE_DIR = 'research-scorecards'


class SnapshotValidationError(ValueError):
    """Snapshot identity or envelope is invalid, or a read target is unsafe."""


@dataclass(frozen=True)
class SaveResult:
    saved: bool
    snapshot_id: str | None = None
    reason: str | None = None


def _identity(symbol, market):
    if not isinstance(market, str) or market not in SYMBOL_PATTERNS or not isinstance(symbol, str) or not SYMBOL_PATTERNS[market].fullmatch(symbol):
        raise SnapshotValidationError('symbol must be canonical for market')


def _date(value):
    if not isinstance(value, str):
        raise SnapshotValidationError('as_of must be an ISO date')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SnapshotValidationError('as_of must be an ISO date') from exc


def _timestamp(value):
    if not isinstance(value, str):
        raise SnapshotValidationError('created_at must include a timezone')
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SnapshotValidationError('created_at must be ISO datetime') from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise SnapshotValidationError('created_at must include a timezone')
    return stamp


def _id(value):
    if not isinstance(value, str) or not SNAPSHOT_ID.fullmatch(value):
        raise SnapshotValidationError('invalid snapshot_id')
    _date(value[:10])


def validate_snapshot(snapshot):
    """Validate the independent envelope and embedded three-card contract."""
    required = {'schema_version', 'rubric_version', 'snapshot_id', 'symbol', 'market',
                'created_at', 'as_of', 'review_scope', 'source_report', 'card'}
    if not isinstance(snapshot, dict) or snapshot.keys() != required:
        raise SnapshotValidationError('snapshot fields do not match the schema')
    if type(snapshot['schema_version']) is not int or snapshot['schema_version'] != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotValidationError('unsupported snapshot schema version')
    if snapshot['rubric_version'] != RUBRIC_VERSION:
        raise SnapshotValidationError('unsupported snapshot rubric version')
    _identity(snapshot['symbol'], snapshot['market'])
    _id(snapshot['snapshot_id'])
    created = _timestamp(snapshot['created_at'])
    cutoff = _date(snapshot['as_of'])
    if snapshot['snapshot_id'][:10] != created.date().isoformat() or cutoff > created.date():
        raise SnapshotValidationError('snapshot identity or cutoff conflicts with creation time')
    if snapshot['review_scope'] != 'full':
        raise SnapshotValidationError('only completed full research is supported')
    validate_card(snapshot['card'])
    if snapshot['rubric_version'] != snapshot['card']['rubric_version'] or snapshot['source_report'] != snapshot['card']['report_reference']:
        raise SnapshotValidationError('card rubric or report reference differs from snapshot')
    if any(d['review_status'] != 'reviewed' for d in snapshot['card']['company_quality']['dimensions']):
        raise SnapshotValidationError('full research must review every dimension')
    for dimension in snapshot['card']['company_quality']['dimensions']:
        if dimension['as_of'] is not None and _date(dimension['as_of']) > cutoff:
            raise SnapshotValidationError('dimension information postdates snapshot cutoff')
        if dimension['assessed_at'] is not None and _date(dimension['assessed_at']) > created.date():
            raise SnapshotValidationError('dimension assessment postdates snapshot creation')
    price = snapshot['card']['price_attractiveness']
    if price['status'] == 'assessed' and any(_date(price['valuation'][field]) > cutoff for field in ('as_of', 'price_as_of')):
        raise SnapshotValidationError('valuation or market price postdates snapshot cutoff')
    for issue in snapshot['card']['decision_conditions']['material_issues']:
        if any(_date(evidence['source_date']) > cutoff for evidence in issue['evidence']):
            raise SnapshotValidationError('material issue evidence postdates snapshot cutoff')
    return snapshot


def _home_path(home):
    if home is None:
        return None
    try:
        path = Path(home)
        if not path.is_absolute() or not path.is_dir():
            return None
        path = path.resolve(strict=True)
        repository = Path(__file__).resolve().parents[1]
        if path == repository or repository in path.parents:
            return None
        return path
    except (OSError, TypeError, ValueError):
        return None


def _safe_dir(home, symbol):
    root = home / STORAGE_DIR
    target = root / symbol
    for item in (root, target):
        if item.is_symlink() or (item.exists() and not item.is_dir()):
            raise SnapshotValidationError('snapshot storage directory is unsafe')
    return target


def create_snapshot(home, symbol, market, card, *, as_of, review_scope='full', snapshot_id=None):
    """Save a completed full research card; return an honest unsaved result on I/O failure.

    ``home`` is an explicit private state-home path (or None for stateless work).
    A caller supplied snapshot_id supports deterministic imports and conflict checks.
    """
    _identity(symbol, market)
    cutoff = _date(as_of)
    validate_card(card)
    now = datetime.now(timezone.utc)
    identifier = snapshot_id if snapshot_id is not None else f'{now.date().isoformat()}-{uuid4().hex}'
    snapshot = {'schema_version': SNAPSHOT_SCHEMA_VERSION, 'rubric_version': card['rubric_version'],
                'snapshot_id': identifier, 'symbol': symbol, 'market': market,
                'created_at': now.isoformat(), 'as_of': cutoff.isoformat(),
                'review_scope': review_scope, 'source_report': card['report_reference'], 'card': card}
    validate_snapshot(snapshot)
    state_home = _home_path(home)
    if state_home is None:
        return SaveResult(False, reason='Private state home unavailable; research was not saved.')
    temporary = None
    try:
        directory = _safe_dir(state_home, symbol)
        directory.mkdir(parents=True, exist_ok=True)
        # Recheck after mkdir, including an existing directory substituted by a symlink.
        if directory.resolve() != state_home / STORAGE_DIR / symbol:
            raise SnapshotValidationError('snapshot storage directory escaped state home')
        target = directory / (identifier + '.json')
        payload = (json.dumps(snapshot, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + '\n').encode('utf-8')
        with tempfile.NamedTemporaryFile(mode='wb', dir=directory, prefix='.pending-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)  # atomic no-overwrite publication
        return SaveResult(True, snapshot_id=identifier)
    except (OSError, SnapshotValidationError) as exc:
        return SaveResult(False, reason=f'Research was not saved: {exc}')
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass  # publication is already complete; cleanup failure cannot undo it


def read_snapshot(home, symbol, snapshot_id):
    """Read an exact immutable version under a canonical tradable line."""
    _id(snapshot_id)
    if not isinstance(symbol, str) or not any(pattern.fullmatch(symbol) for pattern in SYMBOL_PATTERNS.values()):
        raise SnapshotValidationError('invalid canonical symbol')
    state_home = _home_path(home)
    if state_home is None:
        raise SnapshotValidationError('private state home unavailable')
    directory = _safe_dir(state_home, symbol)
    target = directory / (snapshot_id + '.json')
    if target.is_symlink() or not target.is_file() or target.resolve().parent != directory:
        raise SnapshotValidationError('snapshot does not exist or target is unsafe')
    try:
        snapshot = json.loads(target.read_text(encoding='utf-8'))
        validate_snapshot(snapshot)
    except (OSError, ValueError, UnicodeError) as exc:
        raise SnapshotValidationError('snapshot is unreadable or invalid') from exc
    if snapshot['symbol'] != symbol or snapshot['snapshot_id'] != snapshot_id:
        raise SnapshotValidationError('snapshot identity does not match requested target')
    return snapshot
