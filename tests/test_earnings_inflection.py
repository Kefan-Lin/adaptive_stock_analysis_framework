"""
Earnings-inflection / profit-center re-basing contract + e2e tests.

Motivating case: an A-share name (e.g. 宏景科技) reports FY2025 归母净利润 ~26.4M
but a single quarter Q1 2026 归母净利润 ~30.3M — the latest run-rate already
exceeds the entire prior fiscal year.  Mechanically valuing on trailing/FY
earnings would massively understate intrinsic value.

The framework already has machinery to normalize earnings *down* (cyclical
peaks, one-off boosts) and to *re-rate the multiple* (Structural Re-rating
Gate).  These tests pin the missing symmetric capability: detecting and
re-basing earnings *up* to a forward run-rate when a structural inflection
makes trailing earnings unrepresentative — while still guarding against naive
single-quarter annualization.

Re-rating changes the multiple; re-basing changes the earnings base level.
Both must exist.
"""

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contract tests: the re-basing gate must exist and be wired into the flow
# ---------------------------------------------------------------------------

class EarningsBaseRebasingGateContractTests(unittest.TestCase):
    def test_valuation_scenarios_define_earnings_base_rebasing_gate(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        for expected in [
            "Earnings Base Re-basing Gate",
            "run-rate",
            "trailing earnings",
            "structural step-change",
            "re-base",
        ]:
            self.assertIn(expected, scenarios, f"valuation-scenarios.md missing {expected!r}")

    def test_rebasing_gate_separates_rebasing_from_rerating(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        # The two concepts are distinct and must be called out explicitly.
        self.assertIn("Re-rating changes the multiple; re-basing changes the earnings base", scenarios)

    def test_rebasing_gate_is_symmetric_falsification(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        # Must explicitly test the *understatement* direction, not only over-optimism.
        self.assertIn("understate", scenarios)
        self.assertIn("one favorable quarter", scenarios)

    def test_rebasing_gate_requires_corroborating_evidence(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        # Re-basing up must not rely on the reported number alone.
        for expected in ["new capacity", "backlog", "cash conversion"]:
            self.assertIn(expected, scenarios, f"valuation-scenarios.md re-basing gate missing evidence item {expected!r}")

    def test_controller_wires_in_the_rebasing_gate(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("Earnings Base Re-basing Gate", controller)


# ---------------------------------------------------------------------------
# Contract tests: diagnostics must check earnings-base representativeness
# ---------------------------------------------------------------------------

class EarningsBaseRepresentativenessContractTests(unittest.TestCase):
    def test_financial_diagnostics_check_base_representativeness(self) -> None:
        diagnostics = read("skills/analyzing-stocks/references/financial-diagnostics.md")
        for expected in [
            "Earnings base representativeness",
            "annualized run-rate",
            "trailing full-year or TTM",
            "structural step-change",
            "one-off",
            "seasonality",
        ]:
            self.assertIn(expected, diagnostics, f"financial-diagnostics.md missing {expected!r}")


# ---------------------------------------------------------------------------
# Contract tests: report template must carry an explicit earnings-base row
# ---------------------------------------------------------------------------

class ReportTemplateRebasingContractTests(unittest.TestCase):
    def test_template_has_earnings_base_rebasing_section(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        for expected in [
            "盈利基准 re-basing",
            "forward run-rate",
            "trailing",
            "结构性跳档",
            "一次性",
        ]:
            self.assertIn(expected, template, f"report-template.md missing {expected!r}")

    def test_red_team_gate_has_upside_understatement_falsification(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        # The Red-Team gate must be able to catch over-pessimism, not only over-optimism.
        self.assertIn("盈利中枢", template)
        self.assertIn("系统性低估", template)


# ---------------------------------------------------------------------------
# Contract tests: value-investing lens must avoid the omission-style trap
# ---------------------------------------------------------------------------

class ValueInvestingLensRebasingContractTests(unittest.TestCase):
    def test_lens_uses_forward_base_for_confirmed_inflection(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("forward run-rate", lens)
        self.assertIn("re-basing", lens)

    def test_lens_warns_high_trailing_multiple_is_not_automatically_a_trap(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("a high trailing multiple is not by itself a value-trap signal", lens)


# ---------------------------------------------------------------------------
# Contract tests: sector skills must distinguish peak/one-off from re-basing
# ---------------------------------------------------------------------------

class SectorRunRateContractTests(unittest.TestCase):
    def test_industrials_distinguishes_oneoff_annualization_from_rebasing(self) -> None:
        industrials = read("skills/analyzing-industrials-transport/SKILL.md")
        self.assertIn("structural earnings re-basing", industrials)

    def test_semis_distinguishes_peak_annualization_from_rebasing(self) -> None:
        semis = read("skills/analyzing-semiconductors-hardware/SKILL.md")
        self.assertIn("structural earnings re-basing", semis)
        # The original peak-demand caution must stay intact.
        self.assertIn("peak-demand annualization", semis)


# ---------------------------------------------------------------------------
# E2E report-quality fixture: an earnings-inflection name must show re-basing
# ---------------------------------------------------------------------------

def make_earnings_inflection_report_stub() -> str:
    """Minimal fixture for an operating company at a profit-center inflection.

    Models a 宏景科技-style A-share name where the latest quarter run-rate
    already exceeds the prior full year.
    """
    return """
## 2. 公司与行业分型
Analysis Family: operating-company
Valuation Family: cash-flow-and-multiples
路由到的行业 skill: analyzing-industrials-transport

## 6. 财报与财务质量诊断
诊断家族: operating-company
Earnings base representativeness: FY2025 归母净利 26.4M vs Q1 2026 单季 30.3M;
latest-quarter annualized run-rate ~121M >> trailing full-year or TTM base.
Cause classified as structural step-change (AIDC/算力 新业务放量), not one-off.
Seasonality: Q1 通常为季节性偏弱季，单季仍超全年，强化结构性信号。

## 7. 估值与三情景预测
### 7.4 盈利基准 re-basing（盈利拐点/中枢上移时必填）
| 基准 | trailing FY2025 | forward run-rate |
| --- | --- | --- |
| 归母净利 | 26.4M | ~121M (Q1 annualized) |
归类: 结构性跳档 (不是一次性)。证据: new capacity 投产、backlog 在手订单、
gross-margin sustainability、cash conversion 验证。进入 headline Base: 是。

## 9. Red-Team Gate
Red-Team Gate（sign-off 前必答）
盈利中枢上移证伪: 若结构性 re-basing 证据不成立(只是 one favorable quarter),
当前 forward-based 估值是否过度乐观? 反向: 若中枢确已上移, trailing-based 估值是否系统性低估?
9.1 投资结论
Stance: Buy

## 10. 风险、催化剂、监控指标、证据台账
最可能错的地方是：单季利润为项目确认节奏造成的一次性高点，而非中枢上移
"""


class EarningsInflectionReportQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = make_earnings_inflection_report_stub()

    def test_report_flags_base_unrepresentative(self) -> None:
        self.assertIn("Earnings base representativeness", self.report)
        self.assertIn("run-rate", self.report)

    def test_report_classifies_structural_vs_oneoff(self) -> None:
        self.assertIn("structural step-change", self.report)
        self.assertIn("一次性", self.report)

    def test_report_has_rebasing_section_with_both_bases(self) -> None:
        self.assertIn("盈利基准 re-basing", self.report)
        self.assertIn("trailing", self.report)
        self.assertIn("forward run-rate", self.report)

    def test_report_red_team_tests_both_directions(self) -> None:
        self.assertIn("系统性低估", self.report)
        self.assertIn("过度乐观", self.report)


if __name__ == "__main__":
    unittest.main()
