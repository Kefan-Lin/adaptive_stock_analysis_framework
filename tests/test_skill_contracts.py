import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


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


if __name__ == "__main__":
    unittest.main()
