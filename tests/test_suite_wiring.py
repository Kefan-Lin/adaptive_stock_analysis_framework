"""
Suite-wide wiring contract tests.

Two defects found in the whole-suite review:

1. The controller (`analyzing-stocks/SKILL.md`) mandates producing a report whose
   template requires a macro-regime line (§7.1), a Red-Team gate + 8-bucket risk
   table (§9-10), and a portfolio-adjusted size (§9.1) — but its "Load Shared
   References" (Step 4) and "Execute Shared Analysis Modules" (Step 6) lists never
   mention `macro-overlay.md`, `risk-register.md`, or `portfolio-construction.md`.
   An agent following the controller literally cannot fill those mandatory sections.

2. The `investment-decision-workflow` orchestrator runs the Structural Re-rating
   Gate in its Incremental Valuation Update but never the Earnings Base Re-basing
   Gate — even though Event Review (post-earnings) is exactly where a profit-center
   inflection (latest run-rate >> trailing base) gets processed, and is the place
   most at risk of mechanically holding a trailing-based Weighted Fair Value.
"""

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


class ControllerLoadsAllRequiredReferencesTests(unittest.TestCase):
    """The controller must load every reference its own report contract requires."""

    def test_controller_loads_macro_overlay(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("macro-overlay", controller)

    def test_controller_loads_risk_register(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("risk-register", controller)

    def test_controller_loads_portfolio_construction(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("portfolio-construction", controller)

    def test_every_report_required_reference_is_loaded_by_controller(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        # References whose output the report template makes mandatory.
        for ref in [
            "macro-overlay",
            "risk-register",
            "portfolio-construction",
            "valuation-scenarios",
            "value-investing-lens",
            "financial-diagnostics",
        ]:
            self.assertIn(ref, controller, f"controller never loads required reference {ref!r}")


class WorkflowPropagatesRebasingGateTests(unittest.TestCase):
    """The decision workflow must run the re-basing gate, not only the re-rating gate."""

    def test_workflow_references_rebasing_gate(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("Earnings Base Re-basing Gate", workflow)

    def test_workflow_triggers_rebasing_on_runrate_divergence(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("annualized run-rate", workflow)

    def test_workflow_output_contract_lists_rebasing_gate(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        # Both gates must appear so neither is silently dropped from §3 output.
        self.assertIn("Structural Re-rating Gate", workflow)
        self.assertIn("Earnings Base Re-basing Gate", workflow)


# ---------------------------------------------------------------------------
# Minor #1: accounting-quality checks must be symmetric (under- as well as over-)
# ---------------------------------------------------------------------------

class AccountingUnderstatementSymmetryTests(unittest.TestCase):
    def test_diagnostics_flag_understatement_and_hidden_value(self) -> None:
        diagnostics = read("skills/analyzing-stocks/references/financial-diagnostics.md")
        for expected in [
            "Understatement and hidden-value flags",
            "conservative accounting",
            "expensed",
            "hidden or under-marked assets",
        ]:
            self.assertIn(expected, diagnostics, f"financial-diagnostics.md missing {expected!r}")


# ---------------------------------------------------------------------------
# Minor #2: genuine conglomerates / holding companies need a sum-of-parts route
# ---------------------------------------------------------------------------

class ConglomerateSOTPRouteTests(unittest.TestCase):
    def test_controller_routes_conglomerates_to_sotp(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        for expected in [
            "Conglomerates and holding companies",
            "sum-of-parts",
            "holding-company discount",
        ]:
            self.assertIn(expected, controller, f"controller SKILL.md missing {expected!r}")

    def test_valuation_router_has_conglomerate_sotp_rule(self) -> None:
        router = read("skills/analyzing-stocks/references/valuation-router.md")
        self.assertIn("Conglomerate", router)
        self.assertIn("sum-of-parts", router)


# ---------------------------------------------------------------------------
# Minor #3: the 2+ High risk rule must be stated consistently across the file
# ---------------------------------------------------------------------------

class RiskRegisterConsistencyTests(unittest.TestCase):
    def test_two_high_rule_is_stated_consistently(self) -> None:
        register = read("skills/analyzing-stocks/references/risk-register.md")
        canonical = "documented mitigation or offsetting margin-of-safety"
        self.assertGreaterEqual(
            register.count(canonical),
            2,
            "the 2+ High rule must use the same wording in the prose and the aggregated table",
        )
        self.assertIn("reduce stance by at least one tier", register)


class ScheduledMonitoringWiringTests(unittest.TestCase):
    """P4: the skill must document the scheduled pipeline it claims to run."""

    def test_morning_check_documents_scheduled_and_weekly_modes(self) -> None:
        skill = read("skills/morning-check/SKILL.md")
        self.assertIn("## Scheduled Mode", skill)
        self.assertIn("## Weekly Mode", skill)
        self.assertNotIn("scheduling is out of scope", skill)

    def test_scheduled_mode_wires_all_three_scripts(self) -> None:
        skill = read("skills/morning-check/SKILL.md")
        for script in ("sync_portfolio.py", "morning_check.py", "notify_gate.py"):
            self.assertIn(script, skill)

    def test_skill_pins_read_only_guardrail(self) -> None:
        skill = read("skills/morning-check/SKILL.md")
        self.assertIn("read-only", skill.lower())
        self.assertIn("never place", skill.lower())

    def test_scheduled_prompts_reference_exists_and_covers_four_tasks(self) -> None:
        prompts = read("skills/morning-check/references/scheduled-prompts.md")
        for task_id in ("morning-check-am", "morning-check-pm",
                        "portfolio-weekly", "outcome-scoring-monthly"):
            self.assertIn(task_id, prompts)
        self.assertIn(".venv/bin/python", prompts)
        self.assertIn("--account", prompts)

    def test_openai_metadata_mentions_scheduled(self) -> None:
        meta = read("skills/morning-check/agents/openai.yaml")
        self.assertIn("scheduled", meta.lower())
        self.assertNotIn("Manual morning monitoring sweep", meta)


if __name__ == "__main__":
    unittest.main()
