"""String-level contract tests for the discovering-inflections skill wiring (P3)."""
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "discovering-inflections" / "SKILL.md"


class DiscoveringInflectionsWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_stage3_routes_through_debating_stocks_trap_gate(self) -> None:
        self.assertIn("debating-stocks", self.text)
        self.assertIn("value-trap", self.text)

    def test_survivors_become_new_idea_records(self) -> None:
        self.assertIn("mode: new-idea", self.text)
        self.assertIn("decision-records", self.text)
        self.assertIn("INDEX.md", self.text)

    def test_candidates_use_canonical_symbols(self) -> None:
        self.assertIn("canonical", self.text)
        self.assertIn("600519.SH", self.text)

    def test_skill_registered_and_platform_complete(self) -> None:
        openai_yaml = SKILL.parent / "agents" / "openai.yaml"
        self.assertTrue(openai_yaml.exists(), "missing agents/openai.yaml for platform parity")
        validator = (REPO_ROOT / "scripts" / "validate_repo.py").read_text(encoding="utf-8")
        self.assertIn("discovering-inflections", validator)


if __name__ == "__main__":
    unittest.main()
