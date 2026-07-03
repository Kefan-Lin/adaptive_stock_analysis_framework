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


class IndexValidationTests(StateHomeTestCase):
    def test_missing_index_row_for_record_fails(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |\n",
            "",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no INDEX row", result.stdout)

    def test_index_row_without_record_fails(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review |",
            "| 2026-07-03 | position-review |",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no record file", result.stdout)

    def test_missing_index_file_fails(self) -> None:
        (self.home / "records" / "ACME" / "INDEX.md").unlink()
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INDEX.md missing", result.stdout)

    def test_dangling_historical_link_fails(self) -> None:
        self.mutate(
            "records/1234.HK/INDEX.md",
            "[report](../../equity_research_2026-05-01/1234-hk-note.md) |\n| 2026-07-02",
            "[report](../../equity_research_2026-05-01/gone.md) |\n| 2026-07-02",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("report link does not resolve", result.stdout)

    def test_unsorted_rows_fail(self) -> None:
        index = self.home / "records" / "ACME" / "INDEX.md"
        text = index.read_text(encoding="utf-8")
        row1 = "| 2026-06-01 | new-idea | 100.0 USD | Buy | 140 | Stage buy | [record](2026-06-01-new-idea.md) | — |"
        row2 = "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |"
        index.write_text(text.replace(row1 + "\n" + row2, row2 + "\n" + row1), encoding="utf-8")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("sorted", result.stdout)

    def test_missing_see_also_fails(self) -> None:
        self.mutate("records/ACME/INDEX.md", "See also: [1234.HK](../1234.HK/INDEX.md)\n", "")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("See also", result.stdout)

    def test_related_symbol_without_directory_needs_no_see_also(self) -> None:
        self.mutate(
            "records/1234.HK/2026-07-02-research.md",
            "related_symbols: [ACME]",
            "related_symbols: [ACME, 600001.SH]",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_malformed_row_reports_itself(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) |",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed row", result.stdout)

    def test_empty_date_cell_is_malformed_not_ignored(self) -> None:
        self.mutate(
            "records/1234.HK/INDEX.md",
            "| 2026-05-01 | historical |",
            "|  | historical |",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed row", result.stdout)

    def test_duplicate_identity_rows_fail(self) -> None:
        index = self.home / "records" / "ACME" / "INDEX.md"
        row = "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |"
        index.write_text(index.read_text(encoding="utf-8") + row + "\n", encoding="utf-8")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate row", result.stdout)

    def test_historical_link_escaping_home_fails(self) -> None:
        outside = self.home.parent / "outside-report.md"
        outside.write_text("outside\n", encoding="utf-8")
        self.mutate(
            "records/1234.HK/INDEX.md",
            "[report](../../equity_research_2026-05-01/1234-hk-note.md) |\n| 2026-07-02",
            "[report](../../../outside-report.md) |\n| 2026-07-02",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("report link does not resolve", result.stdout)


class PortfolioValidationTests(StateHomeTestCase):
    def test_bad_portfolio_schema_fails(self) -> None:
        self.mutate("portfolio.yaml", "schema: portfolio/v1", "schema: portfolio/v9")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("portfolio", result.stdout)

    def test_holding_missing_qty_fails(self) -> None:
        self.mutate("portfolio.yaml", "qty: 10, ", "")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("qty", result.stdout)

    def test_dangling_thesis_record_fails(self) -> None:
        self.mutate(
            "portfolio.yaml",
            "thesis_record: records/ACME/2026-06-01-new-idea.md",
            "thesis_record: records/ACME/2020-01-01-new-idea.md",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("thesis_record", result.stdout)

    def test_non_canonical_holding_symbol_fails(self) -> None:
        self.mutate("portfolio.yaml", "symbol: ACME", "symbol: acme")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_thesis_record_escaping_home_fails(self) -> None:
        outside = self.home.parent / "outside-thesis.md"
        outside.write_text("outside\n", encoding="utf-8")
        self.mutate(
            "portfolio.yaml",
            "thesis_record: records/ACME/2026-06-01-new-idea.md",
            "thesis_record: ../outside-thesis.md",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("thesis_record", result.stdout)

    def test_non_numeric_qty_fails(self) -> None:
        self.mutate("portfolio.yaml", "qty: 10, ", "qty: ten, ")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be numeric", result.stdout)

    def test_bad_base_currency_fails(self) -> None:
        self.mutate("portfolio.yaml", "base_currency: USD", "base_currency: dollars")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("base_currency", result.stdout)


class ReindexTests(StateHomeTestCase):
    def test_reindex_restores_deleted_record_row(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |\n",
            "",
        )
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        index = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("[record](2026-07-01-position-review.md)", index)

    def test_reindex_preserves_historical_rows(self) -> None:
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        index = (self.home / "records" / "1234.HK" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("| 2026-05-01 | historical |", index)
        self.assertIn("[report](../../equity_research_2026-05-01/1234-hk-note.md)", index)

    def test_reindex_writes_see_also_in_both_directions(self) -> None:
        self.mutate("records/ACME/INDEX.md", "See also: [1234.HK](../1234.HK/INDEX.md)\n", "")
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        acme = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("See also: [1234.HK](../1234.HK/INDEX.md)", acme)

    def test_reindex_notes_dropped_row_for_deleted_record(self) -> None:
        (self.home / "records" / "ACME" / "2026-07-01-position-review.md").unlink()
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("dropped row 2026-07-01-position-review", result.stderr)

    def test_reindex_refuses_to_drop_malformed_rows(self) -> None:
        self.mutate(
            "records/ACME/INDEX.md",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) | — |",
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) |",
        )
        result = run_validator(self.home, "--reindex")
        self.assertEqual(result.returncode, 1)
        self.assertIn("malformed row", result.stdout)
        index = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn(
            "| 2026-07-01 | position-review | 110.0 USD | Hold | 140 | No Action | [record](2026-07-01-position-review.md) |\n",
            index,
        )


if __name__ == "__main__":
    unittest.main()
