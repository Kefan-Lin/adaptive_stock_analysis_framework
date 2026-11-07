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


if __name__ == '__main__':
    unittest.main()
