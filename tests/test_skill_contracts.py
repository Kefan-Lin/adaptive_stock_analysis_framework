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


if __name__ == "__main__":
    unittest.main()
