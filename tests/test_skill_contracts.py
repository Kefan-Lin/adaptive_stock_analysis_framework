import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def read_frontmatter(relative_path: str) -> str:
    content = read(relative_path)
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise AssertionError(f"{relative_path} is missing YAML frontmatter")
    return parts[1]


def skill_paths() -> list[pathlib.Path]:
    return sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))


class SectorSafeControllerContractTests(unittest.TestCase):
    def test_controller_declares_analysis_and_merge_contract(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("analysis family", controller)
        self.assertIn("valuation family", controller)
        self.assertIn("Merge schema", controller)

    def test_controller_and_template_share_stance_vocabulary(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        template = read("skills/analyzing-stocks/references/report-template.md")
        expected = "`Buy / Add / Hold / Reduce / Avoid`"
        self.assertIn(expected, controller)
        self.assertIn(expected, template)

    def test_financial_diagnostics_are_route_aware(self) -> None:
        diagnostics = read("skills/analyzing-stocks/references/financial-diagnostics.md")
        self.assertIn("Operating companies", diagnostics)
        self.assertIn("Banks and insurers", diagnostics)
        self.assertIn("Real estate and asset-backed property businesses", diagnostics)
        self.assertIn("Pre-commercial biotech and binary healthcare", diagnostics)

    def test_valuation_scenarios_support_multiple_valuation_families(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        self.assertIn("P/TBV", scenarios)
        self.assertIn("P/B", scenarios)
        self.assertIn("NAV", scenarios)
        self.assertIn("rNPV", scenarios)
        self.assertIn("Reverse DCF is required only for steady-state operating companies", scenarios)

    def test_reassessment_valuation_changes_are_not_price_anchored(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        template = read("skills/analyzing-stocks/references/report-template.md")

        self.assertIn("Scenario Change Control", scenarios)
        self.assertIn("Do not change Bear/Base/Bull fair values solely because the current share price changed", scenarios)
        self.assertIn("Valuation change bridge vs prior report", template)
        self.assertIn("Prior", template)
        self.assertIn("Reason", template)


class StructuralReratingGateContractTests(unittest.TestCase):
    def test_shared_valuation_contract_requires_structural_rerating_gate(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        template = read("skills/analyzing-stocks/references/report-template.md")

        for expected in [
            "Structural Re-rating Gate",
            "contracted revenue visibility",
            "earnings volatility",
            "discount rate or valuation multiple",
        ]:
            self.assertIn(expected, scenarios)

        for expected in [
            "Structural re-rating sensitivity",
            "Old regime",
            "New regime",
        ]:
            self.assertIn(expected, template)

    def test_sector_skills_cover_industry_specific_rerating_drivers(self) -> None:
        expectations = {
            "skills/analyzing-semiconductors-hardware/SKILL.md": [
                "SCA",
                "take-or-pay",
                "volatility compression",
                "re-rating",
            ],
            "skills/analyzing-resource-energy-materials/SKILL.md": [
                "offtake",
                "tolling",
                "floor-price hedge",
                "contracted cash flow",
            ],
            "skills/analyzing-industrials-transport/SKILL.md": [
                "cancellable",
                "price escalator",
                "advance payment",
                "service attach",
            ],
            "skills/analyzing-software-platforms/SKILL.md": [
                "pricing model migration",
                "usage-based",
                "AI monetization",
                "multiple re-rating",
            ],
            "skills/analyzing-consumer-retail/SKILL.md": [
                "membership",
                "advertising monetization",
                "franchise mix",
                "platform re-rating",
            ],
            "skills/analyzing-banks/SKILL.md": [
                "deposit franchise re-rating",
                "funding beta",
                "fee mix",
                "duration of ROTCE",
            ],
            "skills/analyzing-insurers/SKILL.md": [
                "hard market",
                "float duration",
                "reserve confidence",
                "P/B re-rating",
            ],
            "skills/analyzing-real-estate/SKILL.md": [
                "WALT",
                "CPI escalator",
                "tenant credit",
                "cap-rate re-rating",
            ],
            "skills/analyzing-utilities-telecom/SKILL.md": [
                "PPA",
                "capacity contract",
                "interconnection",
                "contracted cash flow",
            ],
            "skills/analyzing-healthcare-biotech/SKILL.md": [
                "value-based care",
                "recurring consumables",
                "reimbursement contract",
                "installed base",
            ],
        }

        for relative_path, expected_terms in expectations.items():
            content = read(relative_path)
            for expected in expected_terms:
                self.assertIn(expected, content, f"{relative_path} missing {expected!r}")


class RoutingBoundaryContractTests(unittest.TestCase):
    def test_controller_calls_out_the_problem_boundaries(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("healthcare services", controller)
        self.assertIn("asset-light managers may still keep operating-company valuation family", controller)
        self.assertIn("processor-heavy businesses may route to industrials", controller)
        self.assertIn("tower/fiber names may use infrastructure overlay", controller)

    def test_healthcare_skill_separates_services_from_pipeline_logic(self) -> None:
        healthcare = read("skills/analyzing-healthcare-biotech/SKILL.md")
        self.assertIn("Healthcare services, tools, CRO, or HCIT", healthcare)
        self.assertIn("operating-company diagnostics", healthcare)

    def test_real_estate_skill_distinguishes_property_services(self) -> None:
        real_estate = read("skills/analyzing-real-estate/SKILL.md").lower()
        self.assertIn("asset-light property manager, broker, or real-estate services platform", real_estate)
        self.assertIn("operating-company valuation family", real_estate)

    def test_resource_skill_warns_on_specialty_chemicals(self) -> None:
        resources = read("skills/analyzing-resource-energy-materials/SKILL.md").lower()
        self.assertIn("commodity chemicals or spread-driven materials", resources)
        self.assertIn("reroute to `analyzing-industrials-transport`", resources)

    def test_utilities_skill_calls_out_tower_and_fiber_frameworks(self) -> None:
        utilities = read("skills/analyzing-utilities-telecom/SKILL.md").lower()
        self.assertIn("tower or fiber infrastructure operator", utilities)
        self.assertIn("tower or fiber names may lean on infrastructure-style dcf", utilities)

    def test_routing_examples_cover_new_boundary_cases(self) -> None:
        routing_examples = read("examples/routing-examples.md")
        self.assertIn("Healthcare services", routing_examples)
        self.assertIn("Property services", routing_examples)
        self.assertIn("Tower infrastructure", routing_examples)


class RiskRegisterAndRedTeamContractTests(unittest.TestCase):
    def test_risk_register_covers_eight_required_categories(self) -> None:
        register = read("skills/analyzing-stocks/references/risk-register.md")
        for category in [
            "Regulatory",
            "Customer",
            "Supply Chain",
            "Leverage",
            "Accounting",
            "Litigation",
            "Competitive",
            "Geopolitical",
        ]:
            self.assertIn(category, register, f"risk-register.md missing category: {category}")

    def test_risk_register_defines_stance_constraint_table(self) -> None:
        register = read("skills/analyzing-stocks/references/risk-register.md")
        self.assertIn("2+ High entries", register)
        self.assertIn("Stance cannot exceed", register)

    def test_report_template_has_red_team_gate_before_conclusion(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        red_team_pos = template.find("Red-Team Gate")
        # Use the subsection header "9.1 投资结论" so the section title "→ 投资结论" doesn't confuse ordering
        conclusion_pos = template.find("9.1 投资结论")
        self.assertGreater(red_team_pos, 0, "Red-Team Gate section missing from report-template.md")
        self.assertGreater(conclusion_pos, 0, "Section 9.1 投资结论 missing from report-template.md")
        self.assertGreater(conclusion_pos, red_team_pos, "Red-Team Gate must appear before 9.1 投资结论")

    def test_report_template_risk_section_uses_eight_bucket_table(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        for bucket in [
            "监管与政策",
            "客户与收入集中度",
            "供应链与投入成本",
            "杠杆与债务契约",
            "会计与盈利质量",
            "诉讼、ESG",
            "竞争与颠覆",
            "地缘政治与汇率",
        ]:
            self.assertIn(bucket, template, f"report-template.md risk table missing bucket: {bucket}")

    def test_value_investing_lens_references_red_team_gate(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("Red-Team", lens)
        self.assertIn("risk-register.md", lens)


class MacroOverlayROICAndFXContractTests(unittest.TestCase):
    def test_macro_overlay_covers_four_regime_dimensions(self) -> None:
        macro = read("skills/analyzing-stocks/references/macro-overlay.md")
        for dimension in ["Rate Regime", "Inflation Regime", "FX Regime", "Commodity Cycle"]:
            self.assertIn(dimension, macro, f"macro-overlay.md missing section: {dimension}")

    def test_macro_overlay_per_family_adjustments_cover_all_families(self) -> None:
        macro = read("skills/analyzing-stocks/references/macro-overlay.md")
        for family in ["Operating companies", "Banks", "Real estate", "Biotech", "Regulated utilities"]:
            self.assertIn(family, macro, f"macro-overlay.md missing per-family adjustment for: {family}")

    def test_macro_overlay_defines_combined_stress_scenario(self) -> None:
        macro = read("skills/analyzing-stocks/references/macro-overlay.md")
        self.assertIn("Combined Stress Scenario", macro)
        self.assertIn("Bear (macro stress)", macro)

    def test_financial_diagnostics_roic_wacc_required_for_operating_company(self) -> None:
        diagnostics = read("skills/analyzing-stocks/references/financial-diagnostics.md")
        self.assertIn("required", diagnostics)
        self.assertIn("insufficient disclosure", diagnostics)
        # Ensure the old "only when" language is gone
        self.assertNotIn("only when invested-capital math is meaningful", diagnostics)

    def test_source_policy_has_fx_normalization_section(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Currency and FX Normalization", source)
        self.assertIn("period-average", source)
        self.assertIn("period-end", source)


class CatalystAndPortfolioConstructionContractTests(unittest.TestCase):
    def test_report_template_catalyst_section_requires_timing_and_probability(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("预期时间区间", template)
        self.assertIn("触发概率", template)
        self.assertIn("估值影响", template)

    def test_report_template_catalyst_section_covers_biotech_calendar(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("catalyst calendar", template)

    def test_report_template_section9_references_portfolio_construction(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("portfolio-construction.md", template)

    def test_portfolio_construction_defines_sector_caps(self) -> None:
        construction = read("skills/analyzing-stocks/references/portfolio-construction.md")
        self.assertIn("soft cap", construction)
        self.assertIn("hard cap", construction)

    def test_portfolio_construction_defines_correlation_check(self) -> None:
        construction = read("skills/analyzing-stocks/references/portfolio-construction.md")
        self.assertIn("KPI-Driver Correlation", construction)
        self.assertIn("high-correlation", construction)

    def test_portfolio_construction_defines_factor_tilt(self) -> None:
        construction = read("skills/analyzing-stocks/references/portfolio-construction.md")
        for factor in ["Value", "Quality", "Growth", "Momentum", "Defensive"]:
            self.assertIn(factor, construction, f"portfolio-construction.md missing factor: {factor}")

    def test_portfolio_construction_references_upstream_sizing(self) -> None:
        construction = read("skills/analyzing-stocks/references/portfolio-construction.md")
        self.assertIn("portfolio-sizing.md", construction)


class HKEXAndAShareDisclosureContractTests(unittest.TestCase):
    def test_source_policy_has_market_specific_disclosure_checklist(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Market-Specific Disclosure Checklist", source)

    def test_source_policy_hkex_calendar_warns_no_quarterly_reports(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("No quarterly reports", source)

    def test_source_policy_ashare_calendar_explains_yejiyugao_threshold(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("业绩预告", source)
        self.assertIn("mandatory", source)

    def test_source_policy_has_disclosure_absence_rules(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Disclosure Absence Rules by Market", source)

    def test_source_policy_warns_against_sec_intuition_on_other_markets(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("absence = red flag", source)


class GlobalSourceAndSizingContractTests(unittest.TestCase):
    def test_source_policy_covers_us_hk_and_a_share_inputs(self) -> None:
        source_policy = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("HKEX", source_policy)
        self.assertIn("A-share annual / interim / quarterly reports", source_policy)
        self.assertIn("业绩预告", source_policy)
        self.assertIn("IFRS", source_policy)
        self.assertIn("PRC GAAP", source_policy)

    def test_portfolio_sizing_has_liquidity_and_spread_rules(self) -> None:
        sizing = read("skills/analyzing-stocks/references/portfolio-sizing.md")
        self.assertIn("Average daily traded value", sizing)
        self.assertIn("bid-ask spread", sizing)
        self.assertIn("ADR", sizing)
        self.assertIn("micro-cap", sizing)
        self.assertIn("low-turnover", sizing)

    def test_controller_mentions_tradable_line_and_liquidity_downgrade(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("tradable line", controller)
        self.assertIn("bid-ask spread", controller)


class InvestmentDecisionWorkflowContractTests(unittest.TestCase):
    def test_workflow_declares_mode_routing_priority(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("Position Review", workflow)
        self.assertIn("Event Review", workflow)
        self.assertIn("Existing Report to Action", workflow)
        self.assertIn("New Idea Decision", workflow)
        self.assertIn("Mode", workflow)
        self.assertIn("Reason", workflow)

    def test_workflow_reuses_analyzing_stocks_as_research_engine(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("$analyzing-stocks", workflow)
        self.assertIn("Research & Valuation Engine", workflow)
        self.assertIn("Do not change Bear/Base/Bull fair values solely because current price changed", workflow)

    def test_workflow_requires_stale_check_and_incremental_update(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("Stale Check", workflow)
        self.assertIn("Incremental Valuation Update", workflow)
        self.assertIn("Structural Re-rating Gate", workflow)
        self.assertIn("Red-Team Gate", workflow)

    def test_workflow_blocks_material_actions_until_research_is_refreshed(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        for expected in [
            "Action-Blocking Refresh Gate",
            "Refresh required before action",
            "material portfolio exposure",
            ">= 2% - 3%",
            "top portfolio drivers",
            "run `$analyzing-stocks` first",
            "Do not leave `needs future refresh` as a current recommendation for material positions",
        ]:
            self.assertIn(expected, workflow)

    def test_workflow_has_execution_and_option_risk_contract(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        for expected in [
            "Equivalent Exposure",
            "Technical Execution Filter",
            "Momentum Risk Filter",
            "Premium Hurdle",
            "Earnings Risk Block",
            "Earnings Risk Exit",
            "Do-Not-Initiate Rule",
            "No Action",
        ]:
            self.assertIn(expected, workflow)

    def test_workflow_requires_evidence_based_valuation_updates(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        for expected in [
            "Valuation Evidence Gate",
            "Do not raise Weighted Fair Value because the share price rose",
            "sell-side target-price upgrade",
            "backlog",
            "take-or-pay",
            "PPA",
            "WFV can be refreshed only after",
        ]:
            self.assertIn(expected, workflow)

    def test_workflow_includes_portfolio_risk_budget_contract(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        for expected in [
            "Portfolio Risk Budget",
            "stock-equivalent exposure",
            "cash-secured put assigned reserve",
            "cash reserve floor",
            "Capital Allocation Waterfall",
            "Rebalance Rule",
            "single-name cap",
        ]:
            self.assertIn(expected, workflow)


class SkillMetadataContractTests(unittest.TestCase):
    def test_skill_frontmatter_scalars_with_colons_are_quoted(self) -> None:
        for path in skill_paths():
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            frontmatter = read_frontmatter(relative_path)
            for line in frontmatter.strip().splitlines():
                if not line.strip() or line.startswith("  "):
                    continue
                key, separator, value = line.partition(":")
                self.assertTrue(separator, f"{relative_path} frontmatter line lacks key/value separator: {line}")
                value = value.strip()
                if value.startswith(("\"", "'", "|", ">")):
                    continue
                self.assertNotIn(
                    ": ",
                    value,
                    f"{relative_path} frontmatter field {key!r} contains an unquoted colon sequence",
                )


class InputVerificationContractTests(unittest.TestCase):
    def test_controller_has_input_verification_step_before_report(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("Step 6.5", controller)
        self.assertIn("Input Verification Pass", controller)
        for critical_input in ["diluted share count", "net debt", "valuation earnings base"]:
            self.assertIn(critical_input, controller)
        # Verification precedes report production
        self.assertGreater(controller.find("Step 7"), controller.find("Step 6.5"))

    def test_source_policy_requires_dual_source_on_critical_inputs(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Critical-Input Verification", source)
        self.assertIn("two independent sources", source)
        self.assertIn("one filing-direct citation", source)
        self.assertIn("lower confidence one band", source)

    def test_report_template_shows_weighted_fair_value_math(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("sum(probability × scenario value)", template)

    def test_report_template_has_input_verification_block(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("输入验证块", template)
        for column in ["项目", "来源", "通过/存疑"]:
            self.assertIn(column, template)
        self.assertIn("币种与交易线核对", template)


class ValuationInputDisciplineContractTests(unittest.TestCase):
    def test_lens_has_discount_rate_construction_rule_with_floor(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("Discount Rate Construction", lens)
        self.assertIn("risk-free", lens)
        self.assertIn("equity risk premium", lens)
        self.assertIn("floor", lens)
        self.assertIn("300 bps", lens)

    def test_lens_has_terminal_value_numeric_guardrail(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("terminal value exceeds 75%", lens)
        self.assertIn("terminal sensitivity is mandatory", lens)
        self.assertIn("confidence caps at `Medium`", lens)

    def test_scenarios_have_probability_prior_rule(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        self.assertIn("default prior of 25 / 50 / 25", scenarios)
        self.assertIn("±15 pp", scenarios)
        self.assertIn("Bull scenario may not silently carry the thesis", scenarios)

    def test_scenarios_have_bear_plausibility_benchmark(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        self.assertIn("worst historical drawdown", scenarios)
        self.assertIn("a milder Bear must be justified", scenarios)

    def test_macro_overlay_adjustments_respect_wacc_floor(self) -> None:
        macro = read("skills/analyzing-stocks/references/macro-overlay.md")
        self.assertIn("may not breach the discount-rate floor", macro)

    def test_report_template_71_has_discipline_rows(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("折现率构建", template)
        self.assertIn("终值占 PV 比例", template)
        self.assertIn("概率分配理由", template)


if __name__ == "__main__":
    unittest.main()
