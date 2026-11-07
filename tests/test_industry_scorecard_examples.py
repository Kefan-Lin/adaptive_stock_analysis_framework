"""Fictional cross-industry cards at the published validation seam."""
import json
from pathlib import Path
import re
import unittest

from scorecard.card import validate_card


ROOT = Path(__file__).resolve().parents[1] / 'examples' / 'research-scorecard'


class IndustryExamplesTests(unittest.TestCase):
    def test_operating_bank_and_precommercial_cards_trace_to_ten_chapter_reports(self):
        for name in ('operating', 'bank', 'precommercial'):
            with self.subTest(name=name):
                card = json.loads((ROOT / f'{name}-card.json').read_text(encoding='utf-8'))
                report = (ROOT / f'{name}-report.md').read_text(encoding='utf-8')
                sources = (ROOT / f'{name}-sources.md').read_text(encoding='utf-8')
                self.assertIs(validate_card(card), card)
                self.assertEqual(re.findall(r'^## (\d+)\.', report, re.M),
                                 [str(i) for i in range(1, 11)])
                self.assertIn(f'{name}-report.md#1', card['report_reference'])
                self.assertIn(f'{name}-card.json', report)
                for dimension in card['company_quality']['dimensions']:
                    for evidence in dimension['supporting_evidence'] + dimension['counterevidence']:
                        self.assertIn(evidence['source'], sources)
                        self.assertIn(evidence['source_date'], sources)
                    self.assertIn(dimension['rationale'], report)
                for issue in card['decision_conditions']['material_issues']:
                    self.assertIn(issue['description'], report)
                    for evidence in issue['evidence']:
                        self.assertIn(evidence['source'], sources)
                valuation = card['price_attractiveness']['valuation']
                if valuation is not None:
                    self.assertIn(valuation['source_report'].split('#', 1)[1], sources)
                    self.assertIn(valuation['primary_method'], report)

    def test_family_specific_applicability_and_original_price_mode(self):
        cards = {name: json.loads((ROOT / f'{name}-card.json').read_text(encoding='utf-8'))
                 for name in ('operating', 'bank', 'precommercial')}
        dimensions = {name: {d['id']: d for d in card['company_quality']['dimensions']}
                      for name, card in cards.items()}
        self.assertEqual(dimensions['operating']['capital_allocation']['status'], 'assessed')
        self.assertEqual(dimensions['bank']['financial_resilience']['status'], 'assessed')
        self.assertEqual(dimensions['precommercial']['earnings_cash_quality']['status'],
                         'not_applicable')
        self.assertIsNone(dimensions['precommercial']['earnings_cash_quality']['score'])
        self.assertEqual(dimensions['precommercial']['financial_resilience']['status'], 'assessed')
        self.assertEqual(dimensions['bank']['management_governance']['status'],
                         'insufficient_information')
        self.assertEqual(cards['bank']['price_attractiveness']['valuation']['primary_method'], 'P/TBV')
        self.assertEqual(cards['operating']['price_attractiveness']['valuation']['primary_method'],
                         'FCFF DCF')
        self.assertEqual(cards['precommercial']['price_attractiveness']['status'], 'not_assessed')
        statuses = {issue['status'] for card in cards.values()
                    for issue in card['decision_conditions']['material_issues']}
        self.assertEqual(statuses, {'unverified', 'confirmed'})

    def test_precommercial_runway_inference_names_reported_inputs_and_assumptions(self):
        card = json.loads((ROOT / 'precommercial-card.json').read_text(encoding='utf-8'))
        finance = next(d for d in card['company_quality']['dimensions']
                       if d['id'] == 'financial_resilience')
        evidence = {item['id']: item for item in finance['supporting_evidence']}
        self.assertEqual(evidence['precommercial-7-fact']['kind'], 'fact')
        self.assertEqual(evidence['precommercial-7-readout']['kind'], 'management_claim')
        inferred = evidence['precommercial-7-runway']
        self.assertEqual(inferred['kind'], 'inference')
        self.assertEqual(set(inferred['depends_on']),
                         {'precommercial-7-fact', 'precommercial-7-readout'})
        self.assertIn('以后每季现金消耗 12m', inferred['assumptions'])
        self.assertIn('72/12=6', inferred['summary'])
        self.assertIn('分析推断', (ROOT / 'precommercial-report.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
