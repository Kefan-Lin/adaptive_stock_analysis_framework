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
        for expected in (
            "`NVDA`", "`0700.HK`", "`600519.SH`",
            "`000660.KS`", "`BC8.AX`", "related_symbols",
        ):
            self.assertIn(expected, doc)

    def test_index_row_cell_format_is_stated_for_writers(self) -> None:
        doc = read(DECISION_RECORDS)
        self.assertIn("<price_at_decision> <currency>", doc)
        self.assertIn("no thousands separators", doc)


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

    def add_research_record(self, symbol: str, market: str, *, date: str = "2026-07-04") -> None:
        """Create a minimal `research` record dir (record + INDEX) in the temp home.

        Mirrors the fixture's standalone research record so the record ↔ INDEX-row
        bijection holds; `symbol` is used verbatim so callers can exercise
        non-canonical values.
        """
        symbol_dir = self.home / "records" / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        # Quote the symbol so a bare leading-zero code (e.g. 000660) reaches the
        # validator as a string, not a YAML-parsed octal int.
        (symbol_dir / f"{date}-research.md").write_text(
            "---\n"
            "schema: decision-record/v1\n"
            f'symbol: "{symbol}"\n'
            f"market: {market}\n"
            f"date: {date}\n"
            "mode: research\n"
            "price_at_decision: 25.0\n"
            "currency: USD\n"
            "stance: Hold\n"
            f"review_by: {date}\n"
            "---\n\n"
            f"# {symbol} — research (fixture)\n\n"
            "Fictional standalone research record.\n",
            encoding="utf-8",
        )
        (symbol_dir / "INDEX.md").write_text(
            f"# {symbol} — Decision Timeline\n\n"
            "| date | mode | price | stance | WFV | execution | record | report |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
            f"| {date} | research | 25.0 USD | Hold | — | — | "
            f"[record]({date}-research.md) | — |\n",
            encoding="utf-8",
        )


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

    def test_bad_scenario_probabilities_fails(self) -> None:
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            "scenarios: {bear: 80, base: 135, bull: 190}",
            "scenarios: {bear: 80, base: 135, bull: 190}\n"
            "scenario_probabilities: {bear: 20, base: 55, bull: 60}",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("scenario_probabilities", result.stdout)

    def test_valid_scenario_probabilities_passes(self) -> None:
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            "scenarios: {bear: 80, base: 135, bull: 190}",
            "scenarios: {bear: 80, base: 135, bull: 190}\n"
            "scenario_probabilities: {bear: 20, base: 55, bull: 25}",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


class KoreaAustraliaSymbolTests(StateHomeTestCase):
    """Canonical symbol forms extended to Korea (KRX) and Australia (ASX)."""

    def test_korea_ks_record_passes(self) -> None:
        self.add_research_record("000660.KS", "KR")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_australia_ax_record_passes(self) -> None:
        self.add_research_record("BC8.AX", "AU")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_korea_bare_code_is_not_canonical(self) -> None:
        self.add_research_record("000660", "KR")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_australia_bare_code_is_not_canonical(self) -> None:
        self.add_research_record("BC8", "AU")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_portfolio_holding_korea_ks_passes(self) -> None:
        self.mutate(
            "portfolio.yaml",
            "  - {symbol: ACME, qty: 10,",
            "  - {symbol: 000660.KS, qty: 5, avg_cost: 100.0, currency: KRW}\n"
            "  - {symbol: ACME, qty: 10,",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_portfolio_holding_australia_bare_is_flagged(self) -> None:
        self.mutate(
            "portfolio.yaml",
            "  - {symbol: ACME, qty: 10,",
            "  - {symbol: BC8, qty: 5, avg_cost: 1.0, currency: AUD}\n"
            "  - {symbol: ACME, qty: 10,",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("canonical", result.stdout)

    def test_market_enum_error_lists_new_markets(self) -> None:
        self.add_research_record("000660.KS", "XX")
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1)
        self.assertIn("KR", result.stdout)
        self.assertIn("AU", result.stdout)


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


class SeeAlsoSymmetryTests(StateHomeTestCase):
    """See-also links are derived data: an INDEX link not backed by any record's
    related_symbols is flagged, mirroring what --reindex would remove."""

    def _blank_all_related_symbols(self) -> None:
        # Both ACME records and the sole 1234.HK record declare related_symbols;
        # blanking all three leaves the See-also lines in both INDEX files
        # underived, so each becomes an unexpected (stale) link.
        for rel, old in (
            ("records/ACME/2026-06-01-new-idea.md", "related_symbols: [1234.HK]"),
            ("records/ACME/2026-07-01-position-review.md", "related_symbols: [1234.HK]"),
            ("records/1234.HK/2026-07-02-research.md", "related_symbols: [ACME]"),
        ):
            self.mutate(rel, old, "related_symbols: []")

    def test_stale_see_also_without_related_symbols_fails(self) -> None:
        self._blank_all_related_symbols()
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("unexpected See also link [1234.HK](../1234.HK/INDEX.md)", result.stdout)

    def test_dangling_see_also_target_fails(self) -> None:
        # ZZZZ has no directory and no record declares it as related.
        self.mutate(
            "records/ACME/INDEX.md",
            "See also: [1234.HK](../1234.HK/INDEX.md)\n",
            "See also: [1234.HK](../1234.HK/INDEX.md)\nSee also: [ZZZZ](../ZZZZ/INDEX.md)\n",
        )
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("unexpected See also link [ZZZZ](../ZZZZ/INDEX.md)", result.stdout)

    def test_legit_see_also_pair_is_not_flagged(self) -> None:
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertNotIn("unexpected See also link", result.stdout)

    def test_reindex_clears_stale_see_also(self) -> None:
        self._blank_all_related_symbols()
        reindexed = run_validator(self.home, "--reindex")
        self.assertEqual(reindexed.returncode, 0, msg=reindexed.stdout + reindexed.stderr)
        # The gap is closed end to end: plain validate is clean afterwards too.
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_one_sided_relation_reindex_and_validate_agree(self) -> None:
        # Only 1234.HK declares the relation. --reindex derives See-also
        # bidirectionally, so it still writes the [1234.HK] link into ACME's
        # INDEX; validate must accept exactly the state reindex produces.
        self.mutate(
            "records/ACME/2026-06-01-new-idea.md",
            "related_symbols: [1234.HK]", "related_symbols: []",
        )
        self.mutate(
            "records/ACME/2026-07-01-position-review.md",
            "related_symbols: [1234.HK]", "related_symbols: []",
        )
        reindexed = run_validator(self.home, "--reindex")
        self.assertEqual(reindexed.returncode, 0, msg=reindexed.stdout + reindexed.stderr)
        acme = (self.home / "records" / "ACME" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("See also: [1234.HK](../1234.HK/INDEX.md)", acme)
        result = run_validator(self.home)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


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


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_resolves_state_home(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("### State Home", workflow)
        self.assertIn(".investing-home", workflow)
        self.assertIn("Never invent state", workflow)

    def test_stale_check_auto_anchors_from_records(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("latest decision record", workflow)

    def test_output_contract_has_decision_record_section(self) -> None:
        workflow = read(WORKFLOW)
        self.assertIn("### 6. Decision Record", workflow)
        self.assertIn("action_taken", workflow)
        self.assertIn("INDEX.md", workflow)


class ControllerContractTests(unittest.TestCase):
    def test_controller_loads_decision_records_reference(self) -> None:
        self.assertIn("decision-records", read(CONTROLLER))

    def test_controller_step7_emits_archive_ready_record(self) -> None:
        controller = read(CONTROLLER)
        self.assertIn("mode: research", controller)
        self.assertIn("archive-ready", controller)


class PortfolioP4SectionTests(unittest.TestCase):
    """P4 sync sections: accounts, suspected_closed, broker_contract_id, account."""

    def _run(self, portfolio_yaml: str) -> "subprocess.CompletedProcess[str]":
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        home = pathlib.Path(tmp.name) / "home"
        (home / "records").mkdir(parents=True)
        (home / "portfolio.yaml").write_text(portfolio_yaml, encoding="utf-8")
        return run_validator(home)

    BASE = (
        "schema: portfolio/v1\nas_of: 2026-07-13\nbase_currency: USD\n"
        "holdings:\n- {symbol: ACME, qty: 10, avg_cost: 100.0, currency: USD,\n"
        "   account: U200, broker_contract_id: 42}\n")

    def test_valid_p4_sections_pass(self):
        result = self._run(self.BASE + (
            "accounts:\n  U200: {last_synced: 2026-07-13}\n"
            "suspected_closed:\n"
            "- {symbol: OLD, qty: 5, avg_cost: 9.0, currency: USD, account: U200,\n"
            "   suspected_closed_on: 2026-07-13}\n"))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_accounts_bad_date_fails(self):
        result = self._run(self.BASE + "accounts:\n  U200: {last_synced: soon}\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("last_synced", result.stdout)

    def test_suspected_closed_requires_date(self):
        result = self._run(self.BASE + (
            "suspected_closed:\n- {symbol: OLD, qty: 5, account: U200}\n"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("suspected_closed_on", result.stdout)

    def test_broker_contract_id_must_be_numeric(self):
        result = self._run(
            self.BASE.replace("broker_contract_id: 42", "broker_contract_id: abc"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("broker_contract_id", result.stdout)


if __name__ == "__main__":
    unittest.main()
