"""Contract tests for the decision-records & portfolio-state layer (P0).

Spec: docs/plans/2026-07-03-decision-records-design.md
Normative doc under test: skills/analyzing-stocks/references/decision-records.md
"""

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

DECISION_RECORDS = "skills/analyzing-stocks/references/decision-records.md"
CONTROLLER = "skills/analyzing-stocks/SKILL.md"
TEMPLATE = "skills/analyzing-stocks/references/report-template.md"
WORKFLOW = "skills/investment-decision-workflow/SKILL.md"


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class VocabularySyncTests(unittest.TestCase):
    """Every enum in decision-records.md must literally match its source skill."""

    def test_reference_exists(self) -> None:
        self.assertTrue((REPO_ROOT / DECISION_RECORDS).exists())

    def test_stance_vocabulary_matches_controller_template_and_workflow(self) -> None:
        expected = "`Buy / Add / Hold / Reduce / Avoid`"
        for path in (DECISION_RECORDS, CONTROLLER, TEMPLATE, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing stance vocabulary")

    def test_position_size_vocabulary_matches(self) -> None:
        expected = "`Core / Starter / Speculative / Watch-Avoid`"
        for path in (DECISION_RECORDS, TEMPLATE, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing position-size vocabulary")

    def test_confidence_vocabulary_matches_template(self) -> None:
        expected = "`High / Medium / Low`"
        for path in (DECISION_RECORDS, TEMPLATE):
            self.assertIn(expected, read(path), f"{path} missing confidence vocabulary")

    def test_candidate_tier_vocabulary_matches_workflow(self) -> None:
        expected = "`Core Candidate / Tactical Candidate / Reject`"
        for path in (DECISION_RECORDS, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing candidate-tier vocabulary")

    def test_valuation_zone_vocabulary_matches_workflow(self) -> None:
        expected = "`Accumulation / Hold / Exhaustion / Invalidation`"
        for path in (DECISION_RECORDS, WORKFLOW):
            self.assertIn(expected, read(path), f"{path} missing valuation-zone vocabulary")

    def test_execution_method_vocabulary_pinned_to_workflow_execution_sheet(self) -> None:
        expected = "`Buy now / Stage buy / Sell cash-secured put / Wait / Reduce / Exit / No Action`"
        workflow = read(WORKFLOW)
        self.assertIn("### 5. Execution Sheet", workflow)
        self.assertIn(expected, workflow)
        self.assertIn(expected, read(DECISION_RECORDS))

    def test_mode_slug_table_maps_workflow_mode_names(self) -> None:
        doc = read(DECISION_RECORDS)
        for slug, display in [
            ("new-idea", "New Idea Decision"),
            ("existing-report", "Existing Report to Action"),
            ("position-review", "Position Review"),
            ("event-review", "Event Review"),
        ]:
            self.assertIn(slug, doc, f"mode slug {slug!r} missing")
            self.assertIn(display, doc, f"mode display {display!r} missing")
            self.assertIn(display, read(WORKFLOW))
        # research is record-only; historical is index-only.
        self.assertIn("research", doc)
        self.assertIn("historical", doc)

    def test_record_identity_and_tiebreak_are_stated(self) -> None:
        doc = read(DECISION_RECORDS)
        self.assertIn("(symbol, date, mode)", doc)
        self.assertIn("position-review > event-review > existing-report > new-idea > research", doc)

    def test_canonical_symbol_rules_are_stated(self) -> None:
        doc = read(DECISION_RECORDS)
        for expected in ("`NVDA`", "`0700.HK`", "`600519.SH`", "related_symbols"):
            self.assertIn(expected, doc)


class RepoWiringTests(unittest.TestCase):
    def test_full_profile_requires_decision_records_reference(self) -> None:
        validator = read("scripts/validate_repo.py")
        self.assertIn(
            "skills/analyzing-stocks/references/decision-records.md", validator
        )


if __name__ == "__main__":
    unittest.main()
