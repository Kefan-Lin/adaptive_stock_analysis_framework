"""Immutable private research snapshots, independent of decision records."""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from uuid import uuid4

from inflection_discovery.symbols import SYMBOL_PATTERNS
from .card import DIMENSION_IDS, RUBRIC_IDENTIFIER, validate_card


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
    optional = {'baseline_id', 'correction_of', 'correction_reason', 'selected_items',
                'change_reasons', 'item_sources'}
    if not isinstance(snapshot, dict) or not required <= snapshot.keys() or snapshot.keys() - required - optional:
        raise SnapshotValidationError('snapshot fields do not match the schema')
    if type(snapshot['schema_version']) is not int or snapshot['schema_version'] != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotValidationError('unsupported snapshot schema version')
    if not isinstance(snapshot['rubric_version'], str) or not RUBRIC_IDENTIFIER.fullmatch(snapshot['rubric_version']):
        raise SnapshotValidationError('invalid snapshot rubric identifier')
    _identity(snapshot['symbol'], snapshot['market'])
    _id(snapshot['snapshot_id'])
    created = _timestamp(snapshot['created_at'])
    cutoff = _date(snapshot['as_of'])
    if snapshot['snapshot_id'][:10] != created.date().isoformat() or cutoff > created.date():
        raise SnapshotValidationError('snapshot identity or cutoff conflicts with creation time')
    if snapshot['review_scope'] not in ('full', 'partial', 'correction'):
        raise SnapshotValidationError('unknown review scope')
    validate_card(snapshot['card'])
    if snapshot['rubric_version'] != snapshot['card']['rubric_version'] or snapshot['source_report'] != snapshot['card']['report_reference']:
        raise SnapshotValidationError('card rubric or report reference differs from snapshot')
    if snapshot['review_scope'] == 'full' and any(d['review_status'] != 'reviewed' for d in snapshot['card']['company_quality']['dimensions']):
        raise SnapshotValidationError('full research must review every dimension')
    if snapshot['review_scope'] != 'full':
        selected = snapshot.get('selected_items')
        if not isinstance(selected, list) or not selected or len(set(selected)) != len(selected) or any(
                item not in (*DIMENSION_IDS, 'price_attractiveness', 'decision_conditions') for item in selected):
            raise SnapshotValidationError('partial review requires selected items')
        baseline = snapshot.get('baseline_id')
        if baseline is not None:
            _id(baseline)
        if snapshot['review_scope'] == 'correction':
            _id(snapshot.get('correction_of'))
            if not isinstance(snapshot.get('correction_reason'), str) or not snapshot['correction_reason'].strip():
                raise SnapshotValidationError('correction requires explanation')
        reasons = snapshot.get('change_reasons')
        sources = snapshot.get('item_sources')
        if not isinstance(reasons, dict) or not isinstance(sources, dict) or set(reasons) != set(selected):
            raise SnapshotValidationError('change reasons and source tracking required')
        for item, entries in reasons.items():
            if not isinstance(entries, list):
                raise SnapshotValidationError('change reasons must be lists')
            for entry in entries:
                if not isinstance(entry, dict) or set(entry) != {'kind', 'explanation'} or entry['kind'] not in (
                        'new_fact', 'assumption_change', 'rubric_change', 'error_correction') or not isinstance(
                        entry['explanation'], str) or not entry['explanation'].strip() or entry['explanation'].strip() == '更新了':
                    raise SnapshotValidationError('specific substantive change reason required')
        if snapshot['review_scope'] == 'correction' and not any(
                entry['kind'] == 'error_correction' for entries in reasons.values() for entry in entries):
            raise SnapshotValidationError('correction requires error correction reason')
        for item, source in sources.items():
            if item not in (*DIMENSION_IDS, 'price_attractiveness', 'decision_conditions'):
                raise SnapshotValidationError('unknown item source')
            _id(source)
        for dimension in snapshot['card']['company_quality']['dimensions']:
            if dimension['id'] in selected and dimension['review_status'] != 'reviewed':
                raise SnapshotValidationError('selected dimension must be reviewed')
            if dimension['id'] not in selected and dimension['review_status'] != 'carried_forward' and baseline is not None:
                raise SnapshotValidationError('unselected dimension must be carried forward')
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


def create_snapshot(home, symbol, market, card, *, as_of, review_scope='full', snapshot_id=None,
                    baseline_id=None, correction_of=None, correction_reason=None,
                    selected_items=None, change_reasons=None, item_sources=None):
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
    if review_scope != 'full':
        snapshot.update(baseline_id=baseline_id, correction_of=correction_of,
                        correction_reason=correction_reason, selected_items=selected_items,
                        change_reasons=change_reasons, item_sources=item_sources)
    validate_snapshot(snapshot)
    state_home = _home_path(home)
    if review_scope != 'full':
        if baseline_id is not None:
            baseline = read_snapshot(home, symbol, baseline_id)
            if baseline['market'] != market:
                raise SnapshotValidationError('baseline belongs to another market')
        if correction_of is not None:
            target = read_snapshot(home, symbol, correction_of)
            if target['market'] != market or correction_of != baseline_id:
                raise SnapshotValidationError('correction target differs from baseline or market')
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


def _parts(card):
    return {d['id']: d for d in card['company_quality']['dimensions']} | {
        'price_attractiveness': card['price_attractiveness'],
        'decision_conditions': card['decision_conditions']}


def create_partial_snapshot(home, symbol, market, *, baseline_id=None, initial_card=None,
                            dimension_updates=None, price_update=None, decision_update=None,
                            as_of, report_reference, changes, rubric_version=None,
                            correction_of=None, correction_reason=None, snapshot_id=None):
    """Review explicit items against an exact baseline and save a new immutable version.

    With no baseline, initial_card supplies the three-card structure; all unselected
    quality judgments become undated unknowns, not historical assessments.
    """
    _identity(symbol, market)
    if baseline_id is None and initial_card is None:
        raise SnapshotValidationError('first partial review requires an initial card')
    previous = read_snapshot(home, symbol, baseline_id) if baseline_id else None
    if previous is not None and previous['market'] != market:
        raise SnapshotValidationError('baseline belongs to another market')
    if correction_of is not None:
        corrected = read_snapshot(home, symbol, correction_of)
        if corrected['market'] != market or previous is None or correction_of != baseline_id:
            raise SnapshotValidationError('correction and baseline must belong to this tradable line')
    original = previous['card'] if previous else initial_card
    validate_card(original)
    card = deepcopy(original)
    updates = dict(dimension_updates or {})
    if set(updates) - set(DIMENSION_IDS):
        raise SnapshotValidationError('unknown selected dimension')
    if price_update is not None:
        updates['price_attractiveness'] = price_update
    if decision_update is not None:
        updates['decision_conditions'] = decision_update
    if not updates or not isinstance(changes, dict) or set(changes) != set(updates):
        raise SnapshotValidationError('selected items and change reasons must match')
    if not isinstance(report_reference, str) or not report_reference.strip():
        raise SnapshotValidationError('report reference is required')
    old_parts = _parts(original)
    if previous is None:
        for dim in card['company_quality']['dimensions']:
            if dim['id'] not in updates:
                dim.update(status='insufficient_information', score=None, confidence=None,
                           rationale='Not yet assessed in this first partial research.',
                           supporting_evidence=[], counterevidence=[],
                           counterevidence_search='Not yet checked.', open_questions=[],
                           review_triggers=[], assessed_at=None, as_of=None,
                           review_status='not_reviewed')
                dim.pop('source_snapshot', None)
                dim.pop('adjacent_anchor_explanation', None)
        if 'price_attractiveness' not in updates:
            card['price_attractiveness'] = {'status': 'not_assessed', 'reason': 'Not yet reviewed.', 'valuation': None}
        if 'decision_conditions' not in updates:
            card['decision_conditions'] = {'material_issues': [], 'thesis': 'No investment conclusion yet.',
                'falsifiers': [], 'evidence_gaps': ['Decision conditions not yet reviewed.'],
                'portfolio_fit': {'status': 'not_assessed', 'reason': 'Not yet reviewed.'},
                'execution_conditions': {'status': 'not_assessed', 'reason': 'Not yet reviewed.'}}
    else:
        for dim in card['company_quality']['dimensions']:
            if dim['id'] not in updates:
                dim['review_status'] = 'carried_forward'
                dim.setdefault('source_snapshot', previous.get('item_sources', {}).get(dim['id'], baseline_id))
    for index, dim in enumerate(card['company_quality']['dimensions']):
        if dim['id'] in updates:
            entry = deepcopy(updates[dim['id']])
            if entry.get('id') != dim['id']:
                raise SnapshotValidationError('dimension update identity mismatch')
            entry['review_status'] = 'reviewed'
            entry.pop('source_snapshot', None)
            card['company_quality']['dimensions'][index] = entry
    for name in ('price_attractiveness', 'decision_conditions'):
        if name in updates:
            card[name] = deepcopy(updates[name])
    card['report_reference'] = report_reference
    card['rubric_version'] = rubric_version or original['rubric_version']
    if previous and card['rubric_version'] != original['rubric_version']:
        if not all(any(reason.get('kind') == 'rubric_change' for reason in changes.get(item, []))
                   for item in updates):
            raise SnapshotValidationError('rubric change requires a reason per selected item')
    validate_card(card)
    now_cutoff = _date(as_of)
    if previous and now_cutoff < _date(previous['as_of']):
        raise SnapshotValidationError('new cutoff cannot precede baseline')
    for item in updates:
        new = _parts(card)[item]
        old_content = {key: value for key, value in old_parts[item].items()
                       if key not in ('review_status', 'source_snapshot')}
        new_content = {key: value for key, value in new.items()
                       if key not in ('review_status', 'source_snapshot')}
        if previous and new_content != old_content and not changes[item]:
            raise SnapshotValidationError('substantive item change requires reasons')
        if item in DIMENSION_IDS and new.get('assessed_at') is not None and _date(new['assessed_at']) < _date(new['as_of']):
            raise SnapshotValidationError('assessment precedes information cutoff')
    if previous and 'price_attractiveness' in updates:
        old_price = original['price_attractiveness']
        new_price = card['price_attractiveness']
        if old_price['status'] == new_price['status'] == 'assessed':
            prior = old_price['valuation']; current = new_price['valuation']
            mode = ('currency', 'primary_method', 'earnings_basis', 'forecast_horizon', 'scenario_meanings')
            if any(prior[key] != current[key] for key in mode):
                raise SnapshotValidationError('valuation mode requires separately recorded permission')
            intrinsic = ('fair_value', 'scenarios', 'as_of')
            if any(prior[key] != current[key] for key in intrinsic):
                reason_kinds = {entry['kind'] for entry in changes['price_attractiveness']}
                correction = correction_of is not None and 'error_correction' in reason_kinds
                sourced_update = ('new_fact' in reason_kinds or 'assumption_change' in reason_kinds) and (
                    current['as_of'] > prior['as_of'] and current['source_report'] != prior['source_report'])
                if not (correction or sourced_update):
                    raise SnapshotValidationError('intrinsic update requires sourced non-price change or explicit correction')
    if previous and 'price_attractiveness' in updates and set(updates) & set(DIMENSION_IDS):
        for item in set(updates) & set(DIMENSION_IDS):
            if not any(reason['kind'] == 'new_fact' for reason in changes[item]) or not any(
                    evidence['source_date'] > previous['as_of']
                    for evidence in _parts(card)[item]['supporting_evidence']):
                raise SnapshotValidationError('operating transmission requires independent dated facts')
    sources = ({item: previous.get('item_sources', {}).get(item, baseline_id)
                for item in old_parts if item not in updates} if previous else {})
    return create_snapshot(home, symbol, market, card, as_of=as_of,
        review_scope='correction' if correction_of else 'partial', snapshot_id=snapshot_id,
        baseline_id=baseline_id, correction_of=correction_of, correction_reason=correction_reason,
        selected_items=list(updates), change_reasons=changes, item_sources=sources)


def compare_snapshots(home, symbol, before_id, after_id):
    """Read-only field-level difference for two exact versions of one tradable line."""
    before = read_snapshot(home, symbol, before_id)
    after = read_snapshot(home, symbol, after_id)
    if before['market'] != after['market']:
        raise SnapshotValidationError('versions belong to different markets')
    old, new = _parts(before['card']), _parts(after['card'])
    differences = {}
    for item in old:
        # Review bookkeeping is not a substantive change in a judgment.
        left = {k: v for k, v in old[item].items() if k not in ('review_status', 'source_snapshot')}
        right = {k: v for k, v in new[item].items() if k not in ('review_status', 'source_snapshot')}
        fields = sorted(k for k in left.keys() | right.keys() if left.get(k) != right.get(k))
        if fields or before['rubric_version'] != after['rubric_version']:
            differences[item] = {'before': left, 'after': right, 'changed_fields': fields,
                'comparable': before['rubric_version'] == after['rubric_version'],
                'reasons': after.get('change_reasons', {}).get(item, []),
                'note': 'Different scoring rubrics; scores are not comparable.'
                        if before['rubric_version'] != after['rubric_version'] else None}
    return {'before_id': before_id, 'after_id': after_id, 'changes': differences}
