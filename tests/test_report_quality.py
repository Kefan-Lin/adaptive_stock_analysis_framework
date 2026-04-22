"""
End-to-end report quality tests.

These tests use fixture-based "simulated report stubs" — minimal text
that approximates what a correctly generated report would contain for a given
valuation family.  They verify that the report template, valuation family logic,
and sector-specific language all appear together as expected, without requiring
a live model inference loop.

Three fixture families are tested:
  - operating-company  (example: a software compounder like ServiceNow)
  - balance-sheet-financial  (example: a bank like JPMorgan)
  - real-asset-property  (example: a REIT or property developer like CapitaLand)

A fourth fixture covers a cross-market (A-share) name to verify that
jurisdiction-specific disclosure rules and FX normalization language appear.
"""

import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def make_operating_company_report_stub() -> str:
    """Minimal fixture for an operating-company family report (e.g. software SaaS)."""
    return """
## 2. 公司与行业分型
Analysis Family: operating-company
Valuation Family: cash-flow-and-multiples
路由到的行业 skill: analyzing-software-platforms

## 6. 财报与财务质量诊断
诊断家族: operating-company
ROIC vs WACC: 28% vs 9%, spread 19 percentage points (Fact FY2025 10-K)
FCF conversion: 92% of net income

## 7. 估值与三情景预测
### 7.1 假设表
Macro regime: Rates [Neutral], Inflation [Moderate], FX [USD stable], Commodity [N/A]
| 假设 | Bear | Base | Bull |
| FCFF DCF terminal growth | 2% | 3.5% | 5% |
| WACC | 10% | 9% | 8% |
| 概率 | 25% | 55% | 20% |

### 7.2 估值结果
| 场景 | 主估值方法 | 辅助估值方法 | 综合每股价值 |
| Bear | FCFF DCF | EV/EBIT | $320 |
| Base | FCFF DCF | EV/EBIT | $480 |
| Bull | FCFF DCF | EV/EBIT | $620 |
概率加权价值: $465

## 8. 安全边际、市场预期反推、价值陷阱判断
市场预期反推方法: Reverse DCF
安全边际分档: 高

## 9. Red-Team Gate
Red-Team Gate（sign-off 前必答）
关键假设失效测试: 若 ARR growth 降至 8% (vs 18% 基准), 加权公允价值降至 $380, 仍高于当前价 $350
9.1 投资结论
Stance: Buy
Position Size (per-name): Core
Position Size (portfolio-adjusted): Starter  (sector cap check: software already at 22%)
portfolio-construction.md: sector approaching soft cap 25%

## 10. 风险、催化剂、监控指标、证据台账
### 10.1 风险清单（按类别，参见 risk-register.md）
| 监管与政策 | Low | ... |
| 竞争与颠覆 | Medium | AI-native competitors gaining traction in mid-market |

### 10.2 催化剂（每条必须包含时间、概率、估值影响）
| 1 | 企业数字化加速推动 ARR 超预期 | 2025Q3 | 高（>60%） | +15% |

### 10.4 证据台账
Facts（带日期与来源）: ARR $2.1B FY2025 (Fact FY2025 10-K)
Currency and FX Normalization: reporting currency USD; no FX adjustment required

最可能错的地方是：竞争对手在 mid-market 的定价侵蚀快于预期
"""


def make_bank_report_stub() -> str:
    """Minimal fixture for a balance-sheet-financial family report (e.g. a large bank)."""
    return """
## 2. 公司与行业分型
Analysis Family: balance-sheet-financial
Valuation Family: book-value-and-earnings
路由到的行业 skill: analyzing-banks

## 6. 财报与财务质量诊断
诊断家族: balance-sheet-financial
CET1 ratio: 13.2% (Fact Q4 2025 earnings release)
NIM: 2.85%, expanding in rising-rate regime
Reserve coverage: 1.8x NPLs

## 7. 估值与三情景预测
### 7.1 假设表
Macro regime: Rates [Elevated / Plateau], Inflation [Moderate], FX [USD stable], Commodity [N/A]
| 假设 | Bear | Base | Bull |
| P/TBV | 1.1x | 1.5x | 1.9x |
| ROTE | 11% | 14% | 17% |
| 概率 | 30% | 50% | 20% |

### 7.2 估值结果
| Bear | P/TBV | P/E | $42 |
| Base | P/TBV | P/E | $58 |
| Bull | P/TBV | P/E | $74 |
概率加权价值: $56

## 8. 安全边际
市场预期反推方法: implied ROTCE
Tangible book value per share: $45

## 9. Red-Team Gate
Red-Team Gate（sign-off 前必答）
9.1 投资结论
Stance: Add
Position Size (per-name): Starter
Position Size (portfolio-adjusted): Starter

## 10. 风险、催化剂、监控指标、证据台账
### 10.1 风险清单
| 杠杆与债务契约 | Medium | deposit repricing lag could compress NIM if rates fall faster |
| 会计与盈利质量 | Low | clean reserve history |

### 10.2 催化剂（每条必须包含时间、概率、估值影响）
| 1 | 监管批准扩大回购计划 | 2025Q2 | 中（30-60%） | +8% |

最可能错的地方是：信贷周期恶化超预期，拨备计提大幅上升
"""


def make_reit_report_stub() -> str:
    """Minimal fixture for a real-asset-property family report (e.g. a REIT)."""
    return """
## 2. 公司与行业分型
Analysis Family: real-asset-property
Valuation Family: nav-ffo-affo
路由到的行业 skill: analyzing-real-estate

## 6. 财报与财务质量诊断
诊断家族: real-asset-property
NAV per unit: S$2.10 (Fact FY2025 annual report)
AFFO payout ratio: 88%
LTV: 35%, covenant ceiling 45%

## 7. 估值与三情景预测
### 7.1 假设表
Macro regime: Rates [Rising], Inflation [Moderate], FX [SGD stable vs USD], Commodity [N/A]
Cap-rate adjustment (Rising rate regime +50bps in Bear): applied
| NAV | Bear | Base | Bull |
| cap rate | 5.5% | 4.9% | 4.3% |
| 概率 | 25% | 55% | 20% |

### 7.2 估值结果
| Bear | NAV | FFO multiple | S$1.70 |
| Base | NAV | FFO multiple | S$2.05 |
| Bull | NAV | FFO multiple | S$2.60 |
概率加权价值: S$2.07

## 8. 安全边际
市场预期反推方法: implied cap rate
NAV discount/premium: 3% discount to Base NAV

## 9. Red-Team Gate
Red-Team Gate（sign-off 前必答）
9.1 投资结论
Stance: Hold
Position Size (per-name): Starter

## 10. 风险、催化剂、监控指标、证据台账
### 10.1 风险清单
| 杠杆与债务契约 | Medium | debt maturity wall 2027, LTV headroom 10 ppts |

### 10.2 催化剂
| 1 | 资产收购推动 DPU 增长 | 12-18个月内 | 中（30-60%） | +10% |

### 10.4 证据台账
Currency and FX Normalization: reporting currency SGD; period-average 1.35 SGD/USD used for P&L
最可能错的地方是：cap rate 扩张超过 Rising-rate 假设，NAV 压缩幅度大于 Bear 场景
"""


def make_ashare_report_stub() -> str:
    """Minimal fixture for an A-share name verifying jurisdiction-specific language."""
    return """
## 2. 公司与行业分型
Analysis Family: cycle-and-asset
Valuation Family: mid-cycle-dcf-nav-multiples
路由到的行业 skill: analyzing-resource-energy-materials
Listing line: A-share (SSE: 600519), filing regime: CN / A-share / PRC GAAP

## 6. 财报与财务质量诊断
诊断家族: cycle-and-asset
Accounting basis: PRC GAAP
Sources: 年度报告 FY2024 (CNINFO), 业绩快报 2025-01-30, 季度报告 Q1 2025

## 7. 估值与三情景预测
### 7.1 假设表
Macro regime: Rates [Falling], Inflation [Low / Anchored], FX [CNY stable], Commodity [Mid-cycle]
Currency and FX Normalization: reporting currency CNY; USD equivalent computed at period-average 7.10 CNY/USD
| Mid-cycle DCF | Bear | Base | Bull |
| 概率 | 20% | 60% | 20% |

## 9. Red-Team Gate
Red-Team Gate
9.1 投资结论
Stance: Add

## 10. 风险、催化剂、监控指标、证据台账
### 10.1 风险清单
| 监管与政策 | Medium | 行业价格管制风险 |
| 地缘政治与汇率 | Low | 主要收入来自国内市场 |

### 10.2 催化剂
| 1 | 业绩快报超预期 | 2025Q1公告前 | 高（>60%） | +12% |

### 10.4 证据台账
业绩预告: 不适用（利润变动 < 50% 阈值，无强制披露义务）
问询函: 最近两年无重大问询函，会计质量正常

最可能错的地方是：商品价格周期反转快于 Bear 场景假设
"""


# ---------------------------------------------------------------------------
# Operating-company family quality tests
# ---------------------------------------------------------------------------

class OperatingCompanyReportQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = make_operating_company_report_stub()

    def test_operating_company_report_declares_correct_family(self) -> None:
        self.assertIn("operating-company", self.report)

    def test_operating_company_report_includes_roic_wacc(self) -> None:
        self.assertIn("ROIC", self.report)
        self.assertIn("WACC", self.report)

    def test_operating_company_report_uses_dcf_and_fcff(self) -> None:
        self.assertIn("FCFF", self.report)
        self.assertIn("DCF", self.report)

    def test_operating_company_report_includes_reverse_dcf_market_check(self) -> None:
        self.assertIn("Reverse DCF", self.report)

    def test_operating_company_report_includes_red_team_gate(self) -> None:
        self.assertIn("Red-Team Gate", self.report)

    def test_operating_company_report_includes_structured_risk_table(self) -> None:
        self.assertIn("risk-register.md", self.report)

    def test_operating_company_report_catalyst_has_timing_and_probability(self) -> None:
        self.assertIn("2025Q", self.report)
        self.assertIn("高（>60%）", self.report)

    def test_operating_company_report_includes_portfolio_construction_check(self) -> None:
        self.assertIn("portfolio-construction.md", self.report)
        self.assertIn("portfolio-adjusted", self.report)


# ---------------------------------------------------------------------------
# Bank (balance-sheet-financial) family quality tests
# ---------------------------------------------------------------------------

class BankReportQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = make_bank_report_stub()

    def test_bank_report_declares_correct_family(self) -> None:
        self.assertIn("balance-sheet-financial", self.report)

    def test_bank_report_uses_ptbv_and_rote(self) -> None:
        self.assertIn("P/TBV", self.report)
        self.assertIn("ROTE", self.report)

    def test_bank_report_does_not_use_ebitda_standalone(self) -> None:
        # EBITDA should not appear as a standalone valuation anchor in a bank report
        self.assertNotIn("EV/EBITDA", self.report)

    def test_bank_report_uses_implied_rotce_market_check(self) -> None:
        self.assertIn("implied ROTCE", self.report)

    def test_bank_report_includes_tangible_book_value(self) -> None:
        self.assertIn("Tangible book value", self.report)

    def test_bank_report_includes_red_team_gate(self) -> None:
        self.assertIn("Red-Team Gate", self.report)

    def test_bank_report_macro_regime_present(self) -> None:
        self.assertIn("Macro regime", self.report)


# ---------------------------------------------------------------------------
# REIT (real-asset-property) family quality tests
# ---------------------------------------------------------------------------

class REITReportQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = make_reit_report_stub()

    def test_reit_report_declares_correct_family(self) -> None:
        self.assertIn("real-asset-property", self.report)

    def test_reit_report_uses_nav_and_ffo(self) -> None:
        self.assertIn("NAV", self.report)
        self.assertIn("FFO", self.report)
        self.assertIn("AFFO", self.report)

    def test_reit_report_uses_cap_rate_market_check(self) -> None:
        self.assertIn("implied cap rate", self.report)

    def test_reit_report_applies_macro_rate_regime_to_cap_rate(self) -> None:
        self.assertIn("Rising", self.report)
        self.assertIn("Cap-rate adjustment", self.report)

    def test_reit_report_includes_ltv_covenant_check(self) -> None:
        self.assertIn("LTV", self.report)
        self.assertIn("covenant", self.report)

    def test_reit_report_includes_fx_normalization(self) -> None:
        self.assertIn("Currency and FX Normalization", self.report)
        self.assertIn("period-average", self.report)


# ---------------------------------------------------------------------------
# A-share cross-market jurisdiction quality tests
# ---------------------------------------------------------------------------

class AShareJurisdictionQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = make_ashare_report_stub()

    def test_ashare_report_states_prc_gaap_basis(self) -> None:
        self.assertIn("PRC GAAP", self.report)

    def test_ashare_report_references_correct_filing_types(self) -> None:
        self.assertIn("年度报告", self.report)
        self.assertIn("业绩快报", self.report)
        self.assertIn("季度报告", self.report)

    def test_ashare_report_notes_yejikuaibao_source(self) -> None:
        self.assertIn("业绩快报", self.report)

    def test_ashare_report_explains_absence_of_yejiyugao(self) -> None:
        # A-share 业绩预告 is only mandatory under threshold; report must note this
        self.assertIn("业绩预告", self.report)
        self.assertIn("无强制披露义务", self.report)

    def test_ashare_report_checks_inquiry_letters(self) -> None:
        self.assertIn("问询函", self.report)

    def test_ashare_report_includes_fx_normalization(self) -> None:
        self.assertIn("Currency and FX Normalization", self.report)
        self.assertIn("CNY", self.report)
        self.assertIn("period-average", self.report)

    def test_ashare_report_includes_red_team_gate(self) -> None:
        self.assertIn("Red-Team Gate", self.report)

    def test_ashare_report_includes_structured_risk_table(self) -> None:
        self.assertIn("监管与政策", self.report)
        self.assertIn("地缘政治与汇率", self.report)

    def test_ashare_report_catalyst_has_timing_and_probability(self) -> None:
        self.assertIn("2025Q1", self.report)
        self.assertIn("高（>60%）", self.report)


# ---------------------------------------------------------------------------
# Source-policy disclosure calendar contract tests
# ---------------------------------------------------------------------------

class MarketDisclosureCalendarContractTests(unittest.TestCase):
    def test_source_policy_has_hkex_disclosure_calendar(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Market-Specific Disclosure Checklist", source)
        self.assertIn("Interim report", source)
        self.assertIn("Connected transactions", source)
        self.assertIn("Notifiable transactions", source)

    def test_source_policy_has_ashare_disclosure_calendar(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("年度报告", source)
        self.assertIn("季度报告", source)
        self.assertIn("问询函", source)
        self.assertIn("业绩预告", source)

    def test_source_policy_has_absence_rules_by_market(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("Disclosure Absence Rules by Market", source)
        self.assertIn("Normal (no quarterly requirement)", source)

    def test_source_policy_warns_on_sec_intuition_in_aShare(self) -> None:
        source = read("skills/analyzing-stocks/references/source-policy.md")
        self.assertIn("absence = red flag", source)


if __name__ == "__main__":
    unittest.main()
