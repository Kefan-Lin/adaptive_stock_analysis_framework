"""Public snapshot boundary tested with fictional cards and temporary state homes."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scorecard import (SnapshotValidationError, create_snapshot,
                       read_snapshot, validate_snapshot, create_partial_snapshot,
                       compare_snapshots)
from scorecard.card import CardValidationError

REPO = Path(__file__).resolve().parents[1]
CARD = json.loads((REPO / 'examples/research-scorecard/fictional-card.json').read_text())


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name) / 'private'
        self.home.mkdir()

    def card(self):
        return copy.deepcopy(CARD)

    def test_full_research_round_trip_preserves_cards_evidence_and_dates(self):
        original = self.card()
        saved = create_snapshot(self.home, 'QHT', 'US', original, as_of='2026-04-01')
        self.assertTrue(saved.saved)
        snapshot = read_snapshot(self.home, 'QHT', saved.snapshot_id)
        self.assertEqual(validate_snapshot(snapshot), snapshot)
        self.assertEqual((snapshot['schema_version'], snapshot['rubric_version']), (1, '1.0'))
        self.assertEqual((snapshot['symbol'], snapshot['market'], snapshot['review_scope']), ('QHT', 'US', 'full'))
        self.assertEqual(snapshot['source_report'], original['report_reference'])
        self.assertEqual(snapshot['card'], original)
        self.assertEqual(snapshot['card']['company_quality']['dimensions'][0]['assessed_at'],
                         original['company_quality']['dimensions'][0]['assessed_at'])
        self.assertFalse((self.home / 'records').exists())

    def test_invalid_card_or_identity_creates_nothing(self):
        for bad in (0, 6, 2.5, True):
            changed = self.card()
            changed['company_quality']['dimensions'][0]['score'] = bad
            with self.subTest(score=bad), self.assertRaises(CardValidationError):
                create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01')
        for symbol, market in [('700', 'HK'), ('QHT', 'HK'), ('../QHT', 'US'), ('QHT\n', 'US')]:
            with self.subTest(symbol=symbol), self.assertRaises(SnapshotValidationError):
                create_snapshot(self.home, symbol, market, self.card(), as_of='2026-04-01')
        self.assertEqual(list(self.home.iterdir()), [])

    def test_same_day_versions_preserve_bytes_and_tradable_line_identity(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        path = self.home / 'research-scorecards' / 'QHT' / (first.snapshot_id + '.json')
        old = path.read_bytes()
        changed = self.card()
        changed['company_quality']['dimensions'][0]['score'] = 1
        second = create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01')
        hk = create_snapshot(self.home, '0700.HK', 'HK', self.card(), as_of='2026-04-01')
        self.assertNotEqual(first.snapshot_id, second.snapshot_id)
        self.assertEqual(path.read_bytes(), old)
        self.assertEqual(read_snapshot(self.home, 'QHT', second.snapshot_id)['card'], changed)
        self.assertEqual(read_snapshot(self.home, '0700.HK', hk.snapshot_id)['market'], 'HK')
        # A forged file in the requested directory must still fail envelope identity.
        wrong = self.home / 'research-scorecards' / 'QHT' / (hk.snapshot_id + '.json')
        wrong.write_bytes((self.home / 'research-scorecards' / '0700.HK' / (hk.snapshot_id + '.json')).read_bytes())
        for symbol, identifier in [('QHT', hk.snapshot_id), ('../QHT', first.snapshot_id), ('QHT', '../records')]:
            with self.subTest(symbol=symbol, identifier=identifier), self.assertRaises(SnapshotValidationError):
                read_snapshot(self.home, symbol, identifier)

    def test_conflict_and_link_failure_do_not_publish_or_overwrite(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        target = self.home / 'research-scorecards' / 'QHT' / (first.snapshot_id + '.json')
        old = target.read_bytes()
        changed = self.card()
        changed['company_quality']['dimensions'][0]['score'] = 1
        conflict = create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01', snapshot_id=first.snapshot_id)
        with patch('scorecard.snapshot.os.link', side_effect=OSError('controlled failure')):
            failed = create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01')
        for outcome in (conflict, failed):
            self.assertFalse(outcome.saved)
            self.assertIsNone(outcome.snapshot_id)
        self.assertEqual(target.read_bytes(), old)
        self.assertEqual(list(target.parent.iterdir()), [target])

    def test_unavailable_home_returns_honest_unsaved_state(self):
        for home in (None, self.home / 'missing'):
            outcome = create_snapshot(home, 'QHT', 'US', self.card(), as_of='2026-04-01')
            self.assertFalse(outcome.saved)
            self.assertIsNone(outcome.snapshot_id)
        file_home = self.home / 'file'
        file_home.write_text('x')
        self.assertFalse(create_snapshot(file_home, 'QHT', 'US', self.card(), as_of='2026-04-01').saved)
        self.assertFalse((self.home / 'missing').exists())

    def test_legacy_record_validation_and_reindex_leave_body_untouched(self):
        shutil.rmtree(self.home)
        shutil.copytree(REPO / 'tests/fixtures/state-home', self.home)
        record = self.home / 'records/ACME/2026-06-01-new-idea.md'
        original = record.read_bytes()
        saved = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        snapshot = read_snapshot(self.home, 'QHT', saved.snapshot_id)
        snapshot['source_report'] = 'wrong.md'
        with self.assertRaises(SnapshotValidationError):
            validate_snapshot(snapshot)
        for args in ([], ['--reindex']):
            result = subprocess.run([sys.executable, str(REPO / 'scripts/validate_records.py'),
                                     '--home', str(self.home), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(record.read_bytes(), original)

    def test_cutoff_and_symlink_boundaries(self):
        later = self.card()
        later['company_quality']['dimensions'][0]['as_of'] = '2026-04-02'
        later['company_quality']['dimensions'][0]['assessed_at'] = '2026-04-02'
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', later, as_of='2026-04-01')
        later = self.card()
        later['price_attractiveness']['valuation']['price_as_of'] = '2026-04-02'
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', later, as_of='2026-04-01')
        later = self.card()
        later['decision_conditions']['material_issues'][0]['evidence'].append({
            'id': 'late', 'source': 'Fictional disclosure', 'source_date': '2026-04-02',
            'summary': 'Later fact', 'kind': 'fact'})
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', later, as_of='2026-04-01')
        outside = Path(self.temporary.name) / 'outside'
        outside.mkdir()
        (self.home / 'research-scorecards').symlink_to(outside, target_is_directory=True)
        outcome = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        self.assertFalse(outcome.saved)
        self.assertIsNone(outcome.snapshot_id)
        self.assertEqual(list(outside.iterdir()), [])
        with self.assertRaises(SnapshotValidationError):
            read_snapshot(self.home, 'QHT', '2026-11-07-' + 'a' * 32)

    def test_fsync_failure_leaves_no_published_snapshot(self):
        with patch('scorecard.snapshot.os.fsync', side_effect=OSError('storage failure')):
            outcome = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        self.assertFalse(outcome.saved)
        self.assertIsNone(outcome.snapshot_id)
        self.assertEqual(list((self.home / 'research-scorecards' / 'QHT').iterdir()), [])

    def test_partial_review_carries_original_judgments_and_compares_evidence(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        old_path = self.home / 'research-scorecards' / 'QHT' / (first.snapshot_id + '.json')
        old_bytes = old_path.read_bytes()
        changed = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        changed['supporting_evidence'][0]['summary'] = 'A new fictional capacity survey confirms demand.'
        changed['supporting_evidence'][0]['source_date'] = '2026-04-02'
        changed.update(as_of='2026-04-02', assessed_at='2026-04-03')
        result = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=first.snapshot_id,
            dimension_updates={'industry_economics': changed}, as_of='2026-04-03',
            report_reference='fictional-incremental.md', changes={
                'industry_economics': [{'kind': 'new_fact', 'explanation': 'New capacity survey confirms demand.'}]})
        self.assertTrue(result.saved)
        new = read_snapshot(self.home, 'QHT', result.snapshot_id)
        old = read_snapshot(self.home, 'QHT', first.snapshot_id)
        self.assertEqual(old_path.read_bytes(), old_bytes)
        carried = new['card']['company_quality']['dimensions'][1]
        self.assertEqual(carried['supporting_evidence'], old['card']['company_quality']['dimensions'][1]['supporting_evidence'])
        self.assertEqual(carried['assessed_at'], '2026-04-01')
        self.assertEqual(carried['source_snapshot'], first.snapshot_id)
        self.assertEqual(carried['review_status'], 'carried_forward')
        comparison = compare_snapshots(self.home, 'QHT', first.snapshot_id, result.snapshot_id)
        self.assertEqual(comparison['changes']['industry_economics']['before']['score'], 4)
        self.assertIn('supporting_evidence', comparison['changes']['industry_economics']['changed_fields'])
        self.assertEqual(comparison['changes']['industry_economics']['after']['score'], 4)

    def test_first_partial_research_leaves_other_dimensions_unknown_and_undated(self):
        example = self.card()
        selected = example['company_quality']['dimensions'][0]
        saved = create_partial_snapshot(self.home, 'QHT', 'US', initial_card=example,
            dimension_updates={'industry_economics': selected}, as_of='2026-04-01',
            report_reference='fictional-incremental.md', changes={'industry_economics': []})
        self.assertTrue(saved.saved)
        snapshot = read_snapshot(self.home, 'QHT', saved.snapshot_id)
        for dimension in snapshot['card']['company_quality']['dimensions'][1:]:
            self.assertEqual((dimension['status'], dimension['score'], dimension['confidence'],
                              dimension['assessed_at'], dimension['as_of'], dimension['review_status']),
                             ('insufficient_information', None, None, None, None, 'not_reviewed'))
            self.assertNotIn('source_snapshot', dimension)

    def test_correction_links_target_without_changing_old_bytes_and_rejects_wrong_references(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        original_path = self.home / 'research-scorecards' / 'QHT' / (first.snapshot_id + '.json')
        original = original_path.read_bytes()
        wrong = create_snapshot(self.home, 'OTHER', 'US', self.card(), as_of='2026-04-01')
        changed = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        changed['score'] = 3
        changed.pop('adjacent_anchor_explanation')
        options = dict(baseline_id=first.snapshot_id, dimension_updates={'industry_economics': changed},
            as_of='2026-04-01', report_reference='fictional-incremental.md',
            changes={'industry_economics': [{'kind': 'error_correction',
                'explanation': 'Original rating transposed the survey columns.'}]},
            correction_of=first.snapshot_id, correction_reason='Survey columns were transposed.')
        result = create_partial_snapshot(self.home, 'QHT', 'US', **options)
        self.assertTrue(result.saved)
        self.assertEqual(read_snapshot(self.home, 'QHT', result.snapshot_id)['correction_of'], first.snapshot_id)
        self.assertEqual(original_path.read_bytes(), original)
        for bad in ('2026-11-07-' + 'f' * 32, wrong.snapshot_id):
            for key in ('baseline_id', 'correction_of'):
                with self.subTest(reference=bad, field=key), self.assertRaises(SnapshotValidationError):
                    create_partial_snapshot(self.home, 'QHT', 'US', **(options | {key: bad}))

    def test_rubric_change_marks_items_incomparable_without_rewriting_history(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        old_path = self.home / 'research-scorecards' / 'QHT' / (first.snapshot_id + '.json')
        old_bytes = old_path.read_bytes()
        updated = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        updated['rationale'] = 'Under revised anchor, capacity discipline remains mixed.'
        second = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=first.snapshot_id,
            dimension_updates={'industry_economics': updated}, rubric_version='1.1',
            as_of='2026-04-01', report_reference='fictional-incremental.md',
            changes={'industry_economics': [{'kind': 'rubric_change',
                'explanation': 'The revised capacity anchor interprets supply more strictly.'}]})
        self.assertTrue(second.saved)
        comparison = compare_snapshots(self.home, 'QHT', first.snapshot_id, second.snapshot_id)
        self.assertFalse(comparison['changes']['industry_economics']['comparable'])
        self.assertIn('not comparable', comparison['changes']['industry_economics']['note'])
        self.assertEqual(old_path.read_bytes(), old_bytes)

    def test_price_only_update_preserves_valuation_mode_and_quality(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        price = copy.deepcopy(self.card()['price_attractiveness'])
        price['valuation']['market_price'] = 24
        price['valuation']['price_as_of'] = '2026-04-02'
        price['valuation']['margin_of_safety'] = '31%'
        arguments = dict(baseline_id=first.snapshot_id, price_update=price,
            as_of='2026-04-02', report_reference='fictional-incremental.md',
            changes={'price_attractiveness': [{'kind': 'new_fact',
                'explanation': 'Exchange close changed to 24; original valuation is retained.'}]})
        saved = create_partial_snapshot(self.home, 'QHT', 'US', **arguments)
        self.assertTrue(saved.saved)
        before = read_snapshot(self.home, 'QHT', first.snapshot_id)['card']
        after = read_snapshot(self.home, 'QHT', saved.snapshot_id)['card']
        self.assertEqual(before['company_quality']['dimensions'][0]['score'], after['company_quality']['dimensions'][0]['score'])
        self.assertEqual(before['price_attractiveness']['valuation']['fair_value'], after['price_attractiveness']['valuation']['fair_value'])
        invalid = copy.deepcopy(price)
        invalid['valuation']['fair_value'] = 99
        with self.assertRaises(SnapshotValidationError):
            create_partial_snapshot(self.home, 'QHT', 'US', **(arguments | {'price_update': invalid}))

    def test_same_mode_arithmetic_correction_can_update_intrinsic_value(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        revised = copy.deepcopy(self.card()['price_attractiveness'])
        revised['valuation']['fair_value'] = 36
        revised['valuation']['scenarios']['Base'] = 36
        result = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=first.snapshot_id,
            correction_of=first.snapshot_id, correction_reason='Base scenario addition was off by one.',
            price_update=revised, as_of='2026-04-01', report_reference='fictional-correction.md',
            changes={'price_attractiveness': [{'kind': 'error_correction',
                'explanation': 'Corrected a one-unit arithmetic error in the Base scenario.'}]})
        self.assertTrue(result.saved)
        after = read_snapshot(self.home, 'QHT', result.snapshot_id)
        self.assertEqual(after['card']['price_attractiveness']['valuation']['fair_value'], 36)
        self.assertEqual(after['card']['price_attractiveness']['valuation']['primary_method'],
                         self.card()['price_attractiveness']['valuation']['primary_method'])
        changed_mode = copy.deepcopy(revised)
        changed_mode['valuation']['primary_method'] = 'new DCF'
        with self.assertRaises(SnapshotValidationError):
            create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=first.snapshot_id,
                correction_of=first.snapshot_id, correction_reason='Arithmetic error.',
                price_update=changed_mode, as_of='2026-04-01', report_reference='fictional-correction.md',
                changes={'price_attractiveness': [{'kind': 'error_correction',
                    'explanation': 'Corrected arithmetic.'}]})

    def test_substantive_changes_need_specific_reasons_and_fictional_report_discloses_scope(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        changed = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        changed['confidence'] = 'low'
        arguments = dict(baseline_id=first.snapshot_id,
            dimension_updates={'industry_economics': changed}, as_of='2026-04-01',
            report_reference='fictional-incremental-review.md', changes={'industry_economics': []})
        with self.assertRaises(SnapshotValidationError):
            create_partial_snapshot(self.home, 'QHT', 'US', **arguments)
        with self.assertRaises(SnapshotValidationError):
            create_partial_snapshot(self.home, 'QHT', 'US', **(arguments | {'changes': {
                'industry_economics': [{'kind': 'new_fact', 'explanation': '更新了'}]}}))
        report = (REPO / 'examples/research-scorecard/fictional-incremental-review.md').read_text()
        for detail in ('仅复核行业经济性', '原评估日期 2026-04-01',
                       '资料日期 2026-04-02', '本次未复核', '4→4', '未重做完整十章研究'):
            self.assertIn(detail, report)

    def test_consecutive_partial_reviews_retain_transitive_original_provenance(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        base = self.card()
        one = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=first.snapshot_id,
            dimension_updates={'industry_economics': base['company_quality']['dimensions'][0]},
            as_of='2026-04-01', report_reference='fictional-one.md',
            changes={'industry_economics': []})
        two = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=one.snapshot_id,
            dimension_updates={'business_model': base['company_quality']['dimensions'][1]},
            as_of='2026-04-01', report_reference='fictional-two.md',
            changes={'business_model': []})
        latest = read_snapshot(self.home, 'QHT', two.snapshot_id)
        dimensions = {entry['id']: entry for entry in latest['card']['company_quality']['dimensions']}
        self.assertEqual(dimensions['industry_economics']['source_snapshot'], one.snapshot_id)
        self.assertEqual(dimensions['product_competitiveness']['source_snapshot'], first.snapshot_id)
        self.assertEqual(dimensions['product_competitiveness']['assessed_at'], '2026-04-01')
        self.assertEqual(latest['item_sources']['product_competitiveness'], first.snapshot_id)

    def test_public_save_boundary_resolves_partial_baseline_before_publishing(self):
        card = self.card()
        selected = 'industry_economics'
        for dimension in card['company_quality']['dimensions'][1:]:
            dimension['review_status'] = 'carried_forward'
            dimension['source_snapshot'] = '2026-11-07-' + 'f' * 32
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', card, as_of='2026-04-01',
                review_scope='partial', baseline_id='2026-11-07-' + 'f' * 32,
                selected_items=[selected], change_reasons={selected: []}, item_sources={})
        self.assertEqual(list(self.home.iterdir()), [])

    def test_direct_partial_save_rejects_changed_carry_and_forged_provenance(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        card = self.card()
        for dimension in card['company_quality']['dimensions'][1:]:
            dimension.update(review_status='carried_forward', source_snapshot=first.snapshot_id)
        selected = 'industry_economics'
        args = dict(as_of='2026-04-01', review_scope='partial', baseline_id=first.snapshot_id,
                    selected_items=[selected], change_reasons={selected: []},
                    item_sources={d['id']: first.snapshot_id for d in card['company_quality']['dimensions'][1:]} |
                    {'price_attractiveness': first.snapshot_id, 'decision_conditions': first.snapshot_id})
        changed = copy.deepcopy(card)
        changed['company_quality']['dimensions'][1]['score'] = 1
        forged = copy.deepcopy(card)
        forged['company_quality']['dimensions'][1]['source_snapshot'] = '2026-11-07-' + 'f' * 32
        for candidate, kwargs in ((changed, args), (forged, args),
                                  (card, args | {'item_sources': {}})):
            with self.subTest(candidate=candidate['company_quality']['dimensions'][1]['score'],
                              sources=kwargs['item_sources']), self.assertRaises(SnapshotValidationError):
                create_snapshot(self.home, 'QHT', 'US', candidate, **kwargs)
        self.assertEqual(len(list((self.home / 'research-scorecards/QHT').glob('*.json'))), 1)

    def test_nonadjacent_comparison_preserves_intervening_reason(self):
        a = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        industry = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        industry['confidence'] = 'low'
        reason = {'kind': 'assumption_change', 'explanation': 'Fictional demand sensitivity revised.'}
        b = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=a.snapshot_id,
            dimension_updates={'industry_economics': industry}, as_of='2026-04-01',
            report_reference='fictional-b.md', changes={'industry_economics': [reason]})
        business = copy.deepcopy(self.card()['company_quality']['dimensions'][1])
        business['confidence'] = 'low'
        c = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=b.snapshot_id,
            dimension_updates={'business_model': business}, as_of='2026-04-01',
            report_reference='fictional-c.md', changes={'business_model': [reason]})
        comparison = compare_snapshots(self.home, 'QHT', a.snapshot_id, c.snapshot_id)
        self.assertEqual(comparison['changes']['industry_economics']['reasons'], [reason])

    def test_direct_partial_save_enforces_valuation_mode_and_first_partial_unknowns(self):
        a = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        card = self.card()
        for dimension in card['company_quality']['dimensions']:
            dimension.update(review_status='carried_forward', source_snapshot=a.snapshot_id)
        card['price_attractiveness']['valuation']['primary_method'] = 'Fictional replacement model'
        sources = {item: a.snapshot_id for item in (
            *[d['id'] for d in card['company_quality']['dimensions']], 'decision_conditions')}
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', card, as_of='2026-04-01',
                review_scope='partial', baseline_id=a.snapshot_id,
                selected_items=['price_attractiveness'], change_reasons={
                    'price_attractiveness': [{'kind': 'assumption_change',
                                              'explanation': 'Fictional alternate approach.'}]},
                item_sources=sources)
        first = self.card()
        for dimension in first['company_quality']['dimensions'][1:]:
            dimension.update(review_status='not_reviewed', status='insufficient_information',
                             score=None, confidence=None, assessed_at=None, as_of=None,
                             supporting_evidence=[], counterevidence=[])
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', first, as_of='2026-04-01',
                review_scope='partial', selected_items=['industry_economics'],
                change_reasons={'industry_economics': []}, item_sources={})

    def test_combined_arithmetic_correction_does_not_require_new_operating_fact(self):
        a = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        quality = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        quality['score'] = 3
        quality.pop('adjacent_anchor_explanation')
        price = copy.deepcopy(self.card()['price_attractiveness'])
        price['valuation']['fair_value'] = 36
        price['valuation']['scenarios']['Base'] = 36
        reason = [{'kind': 'error_correction', 'explanation': 'Corrected transposed worksheet cells.'}]
        result = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=a.snapshot_id,
            correction_of=a.snapshot_id, correction_reason='Transposed cells.',
            dimension_updates={'industry_economics': quality}, price_update=price,
            as_of='2026-04-01', report_reference='fictional-fix.md',
            changes={'industry_economics': reason, 'price_attractiveness': reason})
        self.assertTrue(result.saved)

    def test_quote_and_independent_quality_assumption_can_share_review(self):
        a = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        quality = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        quality['confidence'] = 'low'
        quality['rationale'] = 'Fictional independent demand sensitivity assumption.'
        quote = copy.deepcopy(self.card()['price_attractiveness'])
        quote['valuation'].update(market_price=24, price_as_of='2026-04-02')
        reasons = {'industry_economics': [{'kind': 'assumption_change',
            'explanation': 'Demand sensitivity changed based on prior operating facts.'}],
            'price_attractiveness': [{'kind': 'new_fact',
            'explanation': 'Fictional market close is now 24.'}]}
        args = dict(baseline_id=a.snapshot_id, dimension_updates={'industry_economics': quality},
            price_update=quote, as_of='2026-04-02', report_reference='fictional-combined.md', changes=reasons)
        self.assertTrue(create_partial_snapshot(self.home, 'QHT', 'US', **args).saved)
        quality['score'] = 3
        quality.pop('adjacent_anchor_explanation')
        with self.assertRaises(SnapshotValidationError):
            create_partial_snapshot(self.home, 'QHT', 'US', **(args | {'changes': reasons | {
                'industry_economics': [{'kind': 'new_fact',
                    'explanation': 'Market quote alone changed quality score.'}]}}))

    def test_carried_item_retains_original_rubric_for_comparison(self):
        a = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        industry = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        reason = [{'kind': 'rubric_change', 'explanation': 'Fictional revised anchor.'}]
        b = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=a.snapshot_id,
            dimension_updates={'industry_economics': industry}, rubric_version='1.1',
            as_of='2026-04-01', report_reference='fictional-b.md', changes={'industry_economics': reason})
        business = copy.deepcopy(self.card()['company_quality']['dimensions'][1])
        business['score'] = 5
        c = create_partial_snapshot(self.home, 'QHT', 'US', baseline_id=b.snapshot_id,
            dimension_updates={'business_model': business}, as_of='2026-04-01',
            report_reference='fictional-c.md', changes={'business_model': [
                {'kind': 'assumption_change', 'explanation': 'Fictional margin assumption revised.'}]})
        self.assertFalse(compare_snapshots(self.home, 'QHT', b.snapshot_id, c.snapshot_id)
                         ['changes']['business_model']['comparable'])

    def test_malformed_nested_card_and_other_public_checkout_are_rejected(self):
        saved = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        snapshot = read_snapshot(self.home, 'QHT', saved.snapshot_id)
        snapshot['card']['company_quality']['dimensions'][0]['id'] = []
        with self.assertRaises(SnapshotValidationError):
            validate_snapshot(snapshot)
        checkout = Path(self.temporary.name) / 'public-checkout'
        checkout.mkdir()
        (checkout / 'install').mkdir()
        (checkout / 'install/install.sh').write_text('# fictional earlier checkout')
        (checkout / 'skills/analyzing-stocks').mkdir(parents=True)
        (checkout / 'skills/analyzing-stocks/SKILL.md').write_text('Fictional public checkout')
        (checkout / 'inflection_discovery').mkdir()
        (checkout / 'inflection_discovery/symbols.py').write_text('Fictional canonical symbols')
        self.assertFalse(create_snapshot(checkout, 'QHT', 'US', self.card(), as_of='2026-04-01').saved)
        private_git = Path(self.temporary.name) / 'private-git-home'
        private_git.mkdir()
        (private_git / '.git').mkdir()
        self.assertTrue(create_snapshot(private_git, 'QHT', 'US', self.card(), as_of='2026-04-01').saved)

    def test_full_research_preserves_predecessor_and_reason_for_comparison(self):
        first = create_snapshot(self.home, 'QHT', 'US', self.card(), as_of='2026-04-01')
        changed = self.card()
        changed['company_quality']['dimensions'][0]['confidence'] = 'low'
        reason = {'kind': 'assumption_change', 'explanation': 'Fictional capacity assumption revised.'}
        with self.assertRaises(SnapshotValidationError):
            create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01',
                            baseline_id=first.snapshot_id, change_reasons={})
        second = create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01',
            baseline_id=first.snapshot_id, change_reasons={'industry_economics': [reason]})
        self.assertEqual(read_snapshot(self.home, 'QHT', second.snapshot_id)['baseline_id'], first.snapshot_id)
        comparison = compare_snapshots(self.home, 'QHT', first.snapshot_id, second.snapshot_id)
        self.assertEqual(comparison['changes']['industry_economics']['reasons'], [reason])
        independent = create_snapshot(self.home, 'QHT', 'US', changed, as_of='2026-04-01')
        unavailable = compare_snapshots(self.home, 'QHT', first.snapshot_id, independent.snapshot_id)
        self.assertIn('unavailable', unavailable['changes']['industry_economics']['note'])

    def test_copied_skill_runs_public_create_and_exact_read_outside_repository(self):
        destination = Path(self.temporary.name) / 'installed'
        unrelated = Path(self.temporary.name) / 'unrelated'
        unrelated.mkdir()
        subprocess.run(['bash', str(REPO / 'install/install.sh'), 'codex', '--copy',
                        '--dest', str(destination), 'analyzing-stocks'], check=True,
                       capture_output=True, text=True)
        command = [sys.executable, str(destination / 'analyzing-stocks/scripts/scorecard.py')]
        card = unrelated / 'card.json'
        card.write_text(json.dumps(self.card()))
        created = subprocess.run(command + ['create', '--home', str(self.home), '--symbol', 'QHT',
            '--market', 'US', '--card', str(card), '--as-of', '2026-04-01'], cwd=unrelated,
            capture_output=True, text=True, env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': ''})
        self.assertEqual(created.returncode, 0, created.stderr)
        identifier = json.loads(created.stdout)['snapshot_id']
        read = subprocess.run(command + ['read', '--home', str(self.home), '--symbol', 'QHT',
            '--snapshot-id', identifier], cwd=unrelated, capture_output=True, text=True,
            env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': ''})
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertEqual(json.loads(read.stdout)['card'], self.card())
        dimension = copy.deepcopy(self.card()['company_quality']['dimensions'][0])
        dimension['confidence'] = 'low'
        request = unrelated / 'partial.json'
        request.write_text(json.dumps({'home': str(self.home), 'symbol': 'QHT', 'market': 'US',
            'baseline_id': identifier, 'dimension_updates': {'industry_economics': dimension},
            'as_of': '2026-04-01', 'report_reference': 'fictional-partial.md',
            'changes': {'industry_economics': [{'kind': 'assumption_change',
                'explanation': 'Fictional demand assumption revised.'}]}}))
        partial = subprocess.run(command + ['partial', '--request', str(request)], cwd=unrelated,
            capture_output=True, text=True, env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': ''})
        self.assertEqual(partial.returncode, 0, partial.stderr)
        later_id = json.loads(partial.stdout)['snapshot_id']
        comparison = subprocess.run(command + ['compare', '--home', str(self.home),
            '--symbol', 'QHT', '--before-id', identifier, '--after-id', later_id], cwd=unrelated,
            capture_output=True, text=True, env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': ''})
        self.assertEqual(comparison.returncode, 0, comparison.stderr)
        self.assertEqual(json.loads(comparison.stdout)['changes']['industry_economics']['after']['confidence'], 'low')
        invalid = subprocess.run(command + ['read', '--home', str(self.home), '--symbol', 'QHT',
            '--snapshot-id', 'latest'], cwd=unrelated, capture_output=True, text=True,
            env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': ''})
        self.assertEqual(invalid.returncode, 1)


if __name__ == '__main__':
    unittest.main()
