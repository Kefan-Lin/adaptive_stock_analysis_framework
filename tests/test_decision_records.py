"""Contract tests for the decision-records & portfolio-state layer (P0).

Spec: docs/plans/2026-07-03-decision-records-design.md
Normative doc under test: skills/analyzing-stocks/references/decision-records.md
"""

import pathlib
import shutil
import subprocess
import sys
import tempfile
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


FIXTURE_HOME = REPO_ROOT / "tests" / "fixtures" / "state-home"
VALIDATOR = REPO_ROOT / "scripts" / "validate_records.py"


def run_validator(home: pathlib.Path, *extra: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--home", str(home), *extra],
        capture_output=True,
        text=True,
    )


class StateHomeTestCase(unittest.TestCase):
    """Copies the fixture home to a temp dir so mutations are isolated."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self._tmp.name) / "home"
        shutil.copytree(FIXTURE_HOME, self.home)
        self.addCleanup(self._tmp.cleanup)

    def mutate(self, relative_path: str, old: str, new: str) -> None:
        path = self.home / relative_path
        text = path.read_text(encoding="utf-8")
        assert old in text, f"mutation target not found in {relative_path}: {old!r}"
        path.write_text(text.replace(old, new), encoding="utf-8")


class RecordValidationTests(StateHomeTestCase):
    def test_good_fixture_home_passes(self) -> None:
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_bad_stance_fails(self) -> None:
        self.mutate("records/ACME/2026-06-01-new-idea.md", "stance: Buy", "stance: StrongBuy")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stance", result.stdout)

    def test_missing_review_by_fails(self) -> None:
        self.mutate("records/ACME/2026-06-01-new-idea.md", "review_by: 2026-09-01", "reviewed: 2026-09-01")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("review_by", result.stdout)

    def test_non_canonical_symbol_dir_fails(self) -> None:
        (self.home / "records" / "1234.HK").rename(self.home / "records" / "01234-HK")
        self.mutate("records/01234-HK/2026-07-02-research.md", "symbol: 1234.HK", "symbol: 01234-HK")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_filename_identity_mismatch_fails(self) -> None:
        (self.home / "records" / "ACME" / "2026-06-01-new-idea.md").rename(
            self.home / "records" / "ACME" / "2026-06-02-new-idea.md"
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("identity", result.stdout)

    def test_incomplete_workflow_group_fails(self) -> None:
        self.mutate(
            "records/ACME/2026-07-01-position-review.md",
            "candidate_tier: Core Candidate\n",
            "",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("candidate_tier", result.stdout)

    def test_dangling_source_report_fails(self) -> None:
        self.mutate(
            "records/1234.HK/2026-07-02-research.md",
            "source_report: equity_research_2026-05-01/1234-hk-note.md",
            "source_report: equity_research_2026-05-01/missing.md",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("source_report", result.stdout)

    def test_frontmatter_with_dashes_in_quoted_value_passes(self) -> None:
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            'text: "fictional KPI deteriorates two quarters running"',
            'text: "fictional KPI --- deteriorates --- two quarters running"',
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_bom_prefixed_record_passes(self) -> None:
        path = self.home / "records" / "ACME" / "2026-06-01-new-idea.md"
        path.write_text("\ufeff" + path.read_text(encoding="utf-8"), encoding="utf-8")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_source_report_escaping_home_fails(self) -> None:
        self.mutate(
            "records/1234.HK/2026-07-02-research.md",
            "source_report: equity_research_2026-05-01/1234-hk-note.md",
            "source_report: ../outside-note.md",
        )
        outside = self.home.parent / "outside-note.md"
        outside.write_text("outside\n", encoding="utf-8")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("source_report", result.stdout)

    def test_bad_price_trigger_fails(self) -> None:
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            "{type: price, level: 90, direction: below}",
            "{type: price, level: 90, direction: sideways}",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("price trigger", result.stdout)

    def test_bad_scenarios_fails(self) -> None:
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            "scenarios: {bear: 80, base: 135, bull: 190}",
            "scenarios: {bear: 80, base: 135}",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("scenarios", result.stdout)


if __name__ == "__main__":
    unittest.main()
