"""Public validation boundary for the independent three-card research scorecard v1."""
from datetime import date
from math import isfinite


class CardValidationError(ValueError):
    """Card data does not satisfy the published schema/rubric contract."""


DIMENSION_IDS = (
    'industry_economics', 'business_model', 'product_competitiveness',
    'moat_durability', 'management_governance', 'capital_allocation',
    'earnings_cash_quality', 'financial_resilience',
)
SCHEMA_VERSION = 1
RUBRIC_VERSION = '1.0'


def _fail(path, problem):
    raise CardValidationError(f'{path}: {problem}')


def _object(value, path, required, optional=()):
    if not isinstance(value, dict):
        _fail(path, 'expected object')
    missing = set(required) - value.keys()
    extras = value.keys() - set(required) - set(optional)
    if missing or extras:
        _fail(path, f'missing {sorted(missing)}, unexpected {sorted(extras)}')


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        _fail(path, 'expected nonempty text')


def _date(value, path):
    _text(value, path)
    try:
        date.fromisoformat(value)
    except ValueError:
        _fail(path, 'expected ISO date')


def _number(value, path):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        _fail(path, 'expected finite numeric value')


def _texts(value, path):
    if not isinstance(value, list):
        _fail(path, 'expected list')
    for index, item in enumerate(value):
        _text(item, f'{path}[{index}]')


def _evidence(items, path):
    if not isinstance(items, list):
        _fail(path, 'expected list')
    ids = set()
    for index, entry in enumerate(items):
        p = f'{path}[{index}]'
        _object(entry, p, ('id', 'source', 'source_date', 'summary', 'kind'),
                ('depends_on', 'assumptions'))
        for key in ('id', 'source', 'summary'):
            _text(entry[key], f'{p}.{key}')
        _date(entry['source_date'], f'{p}.source_date')
        if entry['kind'] not in ('fact', 'management_claim', 'inference'):
            _fail(p, 'unknown evidence kind')
        if entry['kind'] == 'inference':
            _texts(entry.get('depends_on'), f'{p}.depends_on')
            _texts(entry.get('assumptions'), f'{p}.assumptions')
            if not entry['depends_on'] or not entry['assumptions']:
                _fail(p, 'inference requires evidence dependencies and assumptions')
        if entry['id'] in ids:
            _fail(p, 'duplicate evidence id')
        ids.add(entry['id'])
    for index, entry in enumerate(items):
        for dependency in entry.get('depends_on', []):
            if dependency not in ids or dependency == entry['id']:
                _fail(f'{path}[{index}]', 'unresolved evidence dependency')


def _dimension(entry, path):
    _object(entry, path, ('id', 'status', 'score', 'confidence', 'rationale',
                          'supporting_evidence', 'counterevidence', 'counterevidence_search',
                          'open_questions', 'review_triggers', 'assessed_at', 'as_of',
                          'review_status'), ('adjacent_anchor_explanation', 'source_snapshot'))
    if entry['status'] not in ('assessed', 'insufficient_information', 'not_applicable'):
        _fail(path, 'unknown assessment status')
    if entry['status'] == 'assessed':
        if type(entry['score']) is not int or not 1 <= entry['score'] <= 5:
            _fail(path, 'assessed score must be an integer from 1 to 5')
        if entry['confidence'] not in ('high', 'medium', 'low'):
            _fail(path, 'assessed judgment requires independent confidence')
        if entry['score'] in (2, 4):
            _text(entry.get('adjacent_anchor_explanation'), f'{path}.adjacent_anchor_explanation')
    elif entry['score'] is not None or entry['confidence'] is not None:
        _fail(path, 'unscored status requires null score and confidence')
    _text(entry['rationale'], f'{path}.rationale')
    _evidence(entry['supporting_evidence'], f'{path}.supporting_evidence')
    _evidence(entry['counterevidence'], f'{path}.counterevidence')
    if entry['status'] == 'assessed' and not entry['supporting_evidence']:
        _fail(path, 'assessed judgment requires supporting evidence')
    if entry['status'] == 'assessed' and not entry['counterevidence']:
        _text(entry['counterevidence_search'], f'{path}.counterevidence_search')
    if entry['counterevidence_search'] is not None and entry['counterevidence_search'] != '':
        _text(entry['counterevidence_search'], f'{path}.counterevidence_search')
    _texts(entry['open_questions'], f'{path}.open_questions')
    _texts(entry['review_triggers'], f'{path}.review_triggers')
    if entry['status'] == 'assessed' or entry['assessed_at'] is not None:
        _date(entry['assessed_at'], f'{path}.assessed_at')
    if entry['status'] == 'assessed' or entry['as_of'] is not None:
        _date(entry['as_of'], f'{path}.as_of')
    if entry['as_of'] is None and (entry['supporting_evidence'] or entry['counterevidence']):
        _fail(path, 'evidence needs an information cut-off')
    for evidence in entry['supporting_evidence'] + entry['counterevidence']:
        if evidence['source_date'] > entry['as_of']:
            _fail(path, 'evidence postdates information cut-off')
    if entry['as_of'] is not None and entry['assessed_at'] is not None and entry['as_of'] > entry['assessed_at']:
        _fail(path, 'source cut-off exceeds original assessment date')
    if entry['review_status'] not in ('reviewed', 'carried_forward'):
        _fail(path, 'unknown review status')
    if entry['review_status'] == 'carried_forward':
        _text(entry.get('source_snapshot'), f'{path}.source_snapshot')


def _availability(value, path):
    _object(value, path, ('status', 'reason'))
    if value['status'] not in ('assessed', 'not_assessed', 'insufficient_information'):
        _fail(path, 'unknown availability status')
    if value['status'] != 'assessed':
        _text(value['reason'], f'{path}.reason')


def _price(value):
    path = 'price_attractiveness'
    _object(value, path, ('status', 'reason', 'valuation'))
    if value['status'] not in ('assessed', 'not_assessed', 'insufficient_information'):
        _fail(path, 'unknown status')
    if value['status'] != 'assessed':
        if value['valuation'] is not None:
            _fail(path, 'unassessed valuation must be null')
        _text(value['reason'], f'{path}.reason')
        return
    valuation = value['valuation']
    keys = ('source_report', 'as_of', 'price_as_of', 'currency', 'market_price',
            'primary_method', 'earnings_basis', 'forecast_horizon', 'scenarios',
            'scenario_meanings', 'fair_value', 'margin_of_safety',
            'market_implied_expectations')
    _object(valuation, f'{path}.valuation', keys)
    for key in keys:
        if key in ('as_of', 'price_as_of'):
            _date(valuation[key], f'{path}.{key}')
        elif key in ('scenarios', 'scenario_meanings'):
            if not isinstance(valuation[key], dict):
                _fail(path, f'{key} must preserve original labeled scenarios')
        elif key in ('market_price', 'fair_value'):
            if valuation[key] is not None:
                _number(valuation[key], f'{path}.{key}')
        elif valuation[key] is not None or key not in ('margin_of_safety', 'market_implied_expectations'):
            _text(valuation[key], f'{path}.{key}')
    for label, value in valuation['scenarios'].items():
        _text(label, path)
        _number(value, f'{path}.scenarios.{label}')
    if valuation['scenarios'].keys() != valuation['scenario_meanings'].keys():
        _fail(path, 'scenario values and meanings differ')
    for label, meaning in valuation['scenario_meanings'].items():
        _text(label, path)
        _text(meaning, path)


def _decision(value):
    path = 'decision_conditions'
    _object(value, path, ('material_issues', 'thesis', 'falsifiers', 'evidence_gaps',
                          'portfolio_fit', 'execution_conditions'))
    _text(value['thesis'], f'{path}.thesis')
    _texts(value['falsifiers'], f'{path}.falsifiers')
    _texts(value['evidence_gaps'], f'{path}.evidence_gaps')
    for key in ('portfolio_fit', 'execution_conditions'):
        _availability(value[key], f'{path}.{key}')
    if not isinstance(value['material_issues'], list):
        _fail(path, 'material issues must be a list')
    for index, issue in enumerate(value['material_issues']):
        p = f'{path}.material_issues[{index}]'
        _object(issue, p, ('status', 'description', 'impact', 'verification', 'evidence'))
        if issue['status'] not in ('unverified', 'confirmed'):
            _fail(p, 'issue status must distinguish unverified from confirmed')
        for key in ('description', 'impact', 'verification'):
            _text(issue[key], f'{p}.{key}')
        _evidence(issue['evidence'], f'{p}.evidence')
        if issue['status'] == 'confirmed' and not issue['evidence']:
            _fail(p, 'confirmed issue requires evidence')


def validate_card(card):
    """Validate a versioned card and return it unchanged; raises CardValidationError.

    This operation has no side effects and does not calculate scores or valuations.
    """
    _object(card, 'card', ('schema_version', 'rubric_version', 'company_quality',
                           'price_attractiveness', 'decision_conditions', 'report_reference'))
    if type(card['schema_version']) is not int or card['schema_version'] != SCHEMA_VERSION:
        _fail('schema_version', 'unsupported structure version')
    if card['rubric_version'] != RUBRIC_VERSION:
        _fail('rubric_version', 'unsupported scoring rubric version')
    _text(card['report_reference'], 'report_reference')
    _object(card['company_quality'], 'company_quality', ('dimensions',))
    dimensions = card['company_quality']['dimensions']
    if not isinstance(dimensions, list) or len(dimensions) != len(DIMENSION_IDS):
        _fail('company_quality', 'exactly eight dimensions required')
    ids = []
    for index, entry in enumerate(dimensions):
        _dimension(entry, f'company_quality.dimensions[{index}]')
        ids.append(entry['id'])
    if set(ids) != set(DIMENSION_IDS) or len(set(ids)) != len(ids):
        _fail('company_quality', 'dimension identifiers must match the rubric exactly')
    _price(card['price_attractiveness'])
    _decision(card['decision_conditions'])
    return card
