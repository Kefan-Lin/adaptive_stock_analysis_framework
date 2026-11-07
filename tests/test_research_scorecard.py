"""The public card validator is the seam for future storage and report consumers."""
import json
from pathlib import Path
import unittest

from scorecard.card import validate_card, CardValidationError


DIMENSIONS = (
    'industry_economics', 'business_model', 'product_competitiveness',
    'moat_durability', 'management_governance', 'capital_allocation',
    'earnings_cash_quality', 'financial_resilience',
)


def fictional_card():
    return {
        'schema_version': 1, 'rubric_version': '1.0',
        'company_quality': {'dimensions': [
            {'id': dimension, 'status': 'assessed', 'score': 3, 'confidence': 'medium',
             'rationale': 'The observed strength is offset by a concrete limitation.',
             'supporting_evidence': [{'id': 'annual', 'source': 'Fictional annual report, p. 4',
                 'source_date': '2026-03-15', 'summary': 'Customer retention was 80%.',
                 'kind': 'fact'}],
             'counterevidence': [], 'counterevidence_search': 'Compared rival retention disclosures.',
             'open_questions': ['Will retention persist?'],
             'review_triggers': ['Retention drops below 70%.'],
             'assessed_at': '2026-04-01', 'as_of': '2026-03-15',
             'review_status': 'reviewed'} for dimension in DIMENSIONS]},
        'price_attractiveness': {'status': 'not_assessed', 'reason': 'No verified valuation.',
                                 'valuation': None},
        'decision_conditions': {'material_issues': [], 'thesis': 'Recurring demand may persist.',
                                'falsifiers': ['Retention falls.'], 'evidence_gaps': [],
                                'portfolio_fit': {'status': 'insufficient_information',
                                                  'reason': 'No portfolio provided.'},
                                'execution_conditions': {'status': 'not_assessed',
                                                         'reason': 'No decision yet.'}},
        'report_reference': 'fictional-report.md#1-执行摘要',
    }


class ScorecardContractTests(unittest.TestCase):
    def test_complete_three_card_research_is_valid_without_valuation_or_portfolio(self):
        self.assertEqual(validate_card(fictional_card()), fictional_card())

    def test_invalid_scores_and_statuses_fail_at_public_boundary(self):
        for score in (0, 6, 2.5, True):
            with self.subTest(score=score):
                card = fictional_card()
                card['company_quality']['dimensions'][0]['score'] = score
                with self.assertRaises(CardValidationError):
                    validate_card(card)
        for status in ('insufficient_information', 'not_applicable'):
            card = fictional_card()
            card['company_quality']['dimensions'][0].update(status=status, score=3, confidence=None)
            with self.assertRaises(CardValidationError):
                validate_card(card)

    def test_assessed_requires_evidence_and_confidence_but_unknown_preserves_known_material(self):
        for field, value in [('supporting_evidence', []), ('confidence', None),
                             ('counterevidence_search', '')]:
            card = fictional_card()
            card['company_quality']['dimensions'][0][field] = value
            with self.subTest(field=field), self.assertRaises(CardValidationError):
                validate_card(card)
        card = fictional_card()
        card['company_quality']['dimensions'][0].update(
            status='insufficient_information', score=None, confidence=None,
            supporting_evidence=[], counterevidence_search='Not yet checked.',
            rationale='Customer cohort disclosure is missing.')
        self.assertEqual(validate_card(card), card)

    def test_not_applicable_requires_reason_and_inference_dependencies(self):
        card = fictional_card()
        card['company_quality']['dimensions'][0].update(
            status='not_applicable', score=None, confidence=None, rationale='')
        with self.assertRaises(CardValidationError):
            validate_card(card)
        card = fictional_card()
        card['company_quality']['dimensions'][0]['supporting_evidence'].append({
            'id': 'estimate', 'source': 'Analyst calculation', 'source_date': '2026-03-16',
            'summary': 'Retention could stabilize.', 'kind': 'inference'})
        with self.assertRaises(CardValidationError):
            validate_card(card)
        card['company_quality']['dimensions'][0]['as_of'] = '2026-03-16'
        card['company_quality']['dimensions'][0]['supporting_evidence'][1].update(
            depends_on=['annual'], assumptions=['Cohort mix remains stable.'])
        self.assertEqual(validate_card(card), card)

    def test_material_issue_and_existing_valuation_require_traceable_context(self):
        card = fictional_card()
        card['decision_conditions']['material_issues'] = [{
            'status': 'unverified', 'description': 'Possible supplier concentration.',
            'impact': 'Could weaken the thesis.', 'verification': 'Inspect supplier disclosures.',
            'evidence': []}]
        self.assertEqual(validate_card(card), card)
        card['decision_conditions']['material_issues'][0]['impact'] = ''
        with self.assertRaises(CardValidationError):
            validate_card(card)
        card = fictional_card()
        card['price_attractiveness'] = {'status': 'assessed', 'reason': '', 'valuation': {
            'source_report': 'fictional-report.md#7-估值', 'as_of': '2026-04-01',
            'price_as_of': '2026-04-01', 'currency': 'USD', 'market_price': 30,
            'primary_method': 'FCFE', 'earnings_basis': 'normalized owner earnings',
            'forecast_horizon': '5 years', 'scenarios': {'Bear': 20, 'Base': 35, 'Bull': 50},
            'scenario_meanings': {'Bear': 'Demand contracts', 'Base': 'Stable demand',
                                  'Bull': 'Demand expands'},
            'fair_value': 35, 'margin_of_safety': '14%',
            'market_implied_expectations': 'Flat demand'}}
        self.assertEqual(validate_card(card), card)
        del card['price_attractiveness']['valuation']['primary_method']
        with self.assertRaises(CardValidationError):
            validate_card(card)

    def test_intermediate_scores_explain_adjacent_anchors_and_later_evidence_is_rejected(self):
        card = fictional_card()
        card['company_quality']['dimensions'][0]['score'] = 4
        with self.assertRaises(CardValidationError):
            validate_card(card)
        card['company_quality']['dimensions'][0]['adjacent_anchor_explanation'] = (
            'Retained demand exceeds the medium anchor; independent cycle evidence '
            'needed for the strongest anchor.')
        self.assertEqual(validate_card(card), card)
        card['company_quality']['dimensions'][0]['supporting_evidence'][0]['source_date'] = '2026-04-02'
        with self.assertRaises(CardValidationError):
            validate_card(card)

    def test_complete_fictional_report_card_is_valid_and_matches_display(self):
        root = Path(__file__).resolve().parents[1] / 'examples' / 'research-scorecard'
        card = json.loads((root / 'fictional-card.json').read_text(encoding='utf-8'))
        report = (root / 'fictional-report.md').read_text(encoding='utf-8')
        self.assertEqual(validate_card(card), card)
        self.assertEqual([line.split('.')[0] for line in report.splitlines()
                          if line.startswith('## ')], [f'## {i}' for i in range(1, 11)])
        self.assertIn('产品竞争力：5 分，低可信度', report)
        self.assertIn('盈利与现金质量：信息不足', report)
        self.assertIn('资本配置与再投资：不适用', report)
        self.assertIn('待核实：供应商集中', report)
        self.assertIn('已确认：存货跌价', report)
        self.assertIn('旧护城河评分 2/5', report)
        self.assertIn('新护城河持续性质量分 3/5', report)
        self.assertIn('fictional-card.json', report)
        source = (root / 'fictional-sources.md').read_text(encoding='utf-8')
        entries = {row['id']: row for row in card['company_quality']['dimensions']}
        self.assertEqual(entries['product_competitiveness']['confidence'], 'low')
        self.assertIn('60 choosing QHT over Rival A', source)
        self.assertIn('60 人偏好 QHT、25 人偏好竞品', report)
        self.assertIn('导入工具是直接反证', report)
        self.assertIn('三项交付承诺兑现两项', report)
        self.assertIn('债务到期表', entries['financial_resilience']['open_questions'][0])
        self.assertEqual(entries['earnings_cash_quality']['score'], None)
        self.assertEqual(entries['capital_allocation']['status'], 'not_applicable')
        self.assertIn('信托章程', entries['capital_allocation']['supporting_evidence'][0]['source'])
        self.assertIn('受托人', entries['capital_allocation']['rationale'])
        self.assertIn('运营管理层无并购、回购', report)
        self.assertEqual([issue['status'] for issue in card['decision_conditions']['material_issues']],
                         ['unverified', 'confirmed'])

    def test_existing_valuation_can_lack_outputs_not_in_its_original_framework(self):
        card = fictional_card()
        card['price_attractiveness'] = {'status': 'assessed', 'reason': '', 'valuation': {
            'source_report': 'old-report.md#7', 'as_of': '2026-04-01',
            'price_as_of': '2026-04-01', 'currency': 'USD', 'market_price': 30,
            'primary_method': 'NAV', 'earnings_basis': 'asset NAV',
            'forecast_horizon': '3 years', 'scenarios': {}, 'scenario_meanings': {},
            'fair_value': 35, 'margin_of_safety': None,
            'market_implied_expectations': None}}
        self.assertEqual(validate_card(card), card)

    def test_original_scenario_values_must_be_finite_numbers(self):
        card = fictional_card()
        card['price_attractiveness'] = {'status': 'assessed', 'reason': '', 'valuation': {
            'source_report': 'fictional-report.md#7', 'as_of': '2026-04-01',
            'price_as_of': '2026-04-01', 'currency': 'USD', 'market_price': 30,
            'primary_method': 'FCFE', 'earnings_basis': 'owner earnings',
            'forecast_horizon': '5 years', 'scenarios': {'Bear': 20, 'Base': 35},
            'scenario_meanings': {'Bear': 'Loss', 'Base': 'Stable'},
            'fair_value': 35, 'margin_of_safety': None,
            'market_implied_expectations': None}}
        self.assertEqual(validate_card(card), card)
        for bad in (True, '35', float('nan'), float('inf'), -float('inf')):
            for field in ('scenario', 'market_price', 'fair_value'):
                changed = json.loads(json.dumps(card))
                valuation = changed['price_attractiveness']['valuation']
                if field == 'scenario':
                    valuation['scenarios']['Base'] = bad
                else:
                    valuation[field] = bad
                with self.subTest(value=bad, field=field), self.assertRaises(CardValidationError):
                    validate_card(changed)

    def test_first_partial_unknown_does_not_invent_an_assessment_date(self):
        card = fictional_card()
        entry = card['company_quality']['dimensions'][0]
        entry.update(status='insufficient_information', score=None, confidence=None,
                     assessed_at=None, as_of=None, supporting_evidence=[],
                     rationale='The required disclosure is unavailable.')
        self.assertEqual(validate_card(card), card)

    def test_card_does_not_accept_rollup_or_automatic_trade_signal(self):
        for key in ('weighted_total', 'trade_signal'):
            card = fictional_card()
            card[key] = 4
            with self.subTest(key=key), self.assertRaises(CardValidationError):
                validate_card(card)


if __name__ == '__main__':
    unittest.main()
