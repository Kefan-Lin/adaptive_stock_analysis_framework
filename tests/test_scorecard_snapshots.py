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
                       read_snapshot, validate_snapshot)
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


if __name__ == '__main__':
    unittest.main()
