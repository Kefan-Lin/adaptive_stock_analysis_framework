# Valuation Reliability Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the 4-task valuation-reliability hardening backlog (`docs/plans/2026-07-03-valuation-hardening-backlog.md`) — strengthen the point-estimate layer of the analysis engine (input verification, WACC/TV/probability/bear discipline, cross-sectional reconciliation, run-stability guards) so every report's numbers are more trustworthy and P2 scoring can later measure the effect.

**Architecture:** Pure skill-and-reference contract edits in `skills/analyzing-stocks/` and `skills/investment-decision-workflow/`, each new rule pinned by a string-level contract test in the existing `tests/test_skill_contracts.py` style. No code, no new dependencies. Branch: `valuation-hardening` (already created off main `e3b0629`; this plan is committed on it).

**Tech Stack:** Markdown reference/skill files (bilingual: Chinese section prose + English anchor terms); Python `unittest` string-contract tests run with `.venv/bin/python` (PyYAML-only, mirrors CI). The reference files are prompt-contracts for an LLM — the quality bar is that a rule is unambiguous enough to change model behavior AND pinned by a test so it cannot silently regress.

**Backlog spec (normative):** `docs/plans/2026-07-03-valuation-hardening-backlog.md`. Findings register: E1–E4 (execution), M5–M10 (methodology). Read it before starting.

---

## Execution Rules

- One task per commit. Do not batch. Avoid unrelated cleanup.
- TDD every task: write the failing contract test(s) → run and watch them fail → make the skill/reference edits → run and watch them pass → run the full suite + validator → commit.
- Use `.venv/bin/python` for every command (PyYAML-only, mirrors main CI). Never the global interpreter.
- Anchor terms that a test asserts must appear **verbatim** in both the test and the reference file. When adding a rule to a bilingual file, keep the surrounding prose in the file's existing language and embed the English anchor term inline (matching how `Weighted Fair Value`, `Structural re-rating sensitivity`, `Red-Team Gate` already appear inside Chinese rows).
- Numbers are fixed by the backlog: WACC floor = risk-free + 300 bps min for equities; terminal value > 75% of PV triggers mandatory sensitivity + caps confidence at Medium; probability prior 25/50/25, deviations beyond ±15 pp need evidence; bear vs worst historical drawdown; MoS process-noise floor 25–30% for long-duration/growth; material second opinion at ≥ 2%–3% NLV, WFV divergence > 15% caps confidence and defaults execution to Wait; moat verdict below 3.0 forces excess-return fade.
- Commit messages: plain imperative; end every message with the footer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Privacy: fictional tickers only in any example text.

## File Structure

| Path | Action | Responsibility |
| --- | --- | --- |
| `tests/test_skill_contracts.py` | Modify | Append 4 new test classes (one per task) |
| `skills/analyzing-stocks/SKILL.md` | Modify | Task 1 (Step 6.5 verification), Task 4 (Step 1 user-view isolation) |
| `skills/analyzing-stocks/references/source-policy.md` | Modify | Task 1 critical-input dual-source verification |
| `skills/analyzing-stocks/references/report-template.md` | Modify | Task 1 (§7.2 WFV math line, §10.4 verification block), Task 2 (§7.1 rows), Task 3 (§7.5 comps), Task 4 (opposing-case line) |
| `skills/analyzing-stocks/references/valuation-scenarios.md` | Modify | Task 2 (§1 probability prior + bear benchmark), Task 3 (§8 required comps + moat linkage) |
| `skills/analyzing-stocks/references/value-investing-lens.md` | Modify | Task 2 (§3 WACC build + TV guardrail), Task 4 (§5 MoS noise floor) |
| `skills/analyzing-stocks/references/macro-overlay.md` | Modify | Task 2 (adjustments may not breach the WACC floor) |
| `skills/investment-decision-workflow/SKILL.md` | Modify | Task 4 material-decision second opinion |

---

### Task 1: Arithmetic & Input Verification Pass (E2, part of E3)

The single highest-leverage fix: a wrong diluted share count or net-debt figure corrupts every downstream number. Add a mandatory, cheap verification step to the ordinary path so no report finalizes without it, and make the WFV arithmetic an explicit shown computation rather than an asserted scalar.

**Files:**
- Modify: `skills/analyzing-stocks/SKILL.md` (Control Flow list + new `## Step 6.5`)
- Modify: `skills/analyzing-stocks/references/source-policy.md` (new `## Critical-Input Verification` section)
- Modify: `skills/analyzing-stocks/references/report-template.md` (§7.2 explicit math line; §10.4 verification block)
- Modify: `tests/test_skill_contracts.py` (new class `InputVerificationContractTests`)

- [ ] **Step 1: Write the failing contract tests**

Append to `tests/test_skill_contracts.py` (before the `if __name__` block):

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.InputVerificationContractTests -v
```

Expected: all four FAIL (`AssertionError: ... not found`).

- [ ] **Step 3: Add Step 6.5 to the controller**

In `skills/analyzing-stocks/SKILL.md`, in the `## Control Flow` numbered list, change the current step 8 to keep the report last but insert a verification step. Replace the line:

```
8. Produce the unified report with stance and position sizing.
```

with:

```
8. Run the input verification pass: confirm the critical valuation inputs and show the weighted-fair-value arithmetic before anything is finalized.
9. Produce the unified report with stance and position sizing.
```

Then insert a new section between `## Step 6` (ends before `## Step 7`) and `## Step 7`:

```markdown
## Step 6.5: Input Verification Pass (Mandatory)

Before producing the report, run a cheap audit of the inputs every downstream
number depends on. A wrong diluted share count or net debt figure silently
corrupts Weighted Fair Value, margin of safety, and sizing.

- Verify the three critical inputs per [source-policy](references/source-policy.md)
  `Critical-Input Verification`: the **diluted share count**, **net debt** (or net
  cash), and the **valuation earnings base** (the earnings/cash-flow numerator the
  valuation actually uses). Each must be confirmed by two independent sources or one
  filing-direct citation; state any discrepancy and lower confidence one band.
- Recompute Weighted Fair Value as an explicit shown line, `sum(probability ×
  scenario value)`, not an asserted scalar; it must reconcile with the scenario
  table.
- For dual-listed / ADR names, assert the currency-and-tradable-line reconciliation
  before stating the target range.
- Record the pass in report Section 10.4's `输入验证块` so skipping it is visible.
```

- [ ] **Step 4: Add the Critical-Input Verification section to source-policy**

In `skills/analyzing-stocks/references/source-policy.md`, insert a new section immediately before `## Failure Conditions`:

```markdown
## Critical-Input Verification

Three inputs drive every downstream valuation number and must be verified before a
report finalizes (see controller Step 6.5):

1. **Diluted share count** — fully diluted, including options, RSUs, convertibles,
   and recent issuance/buyback since the last balance sheet.
2. **Net debt / net cash** — total debt minus cash and equivalents at the latest
   reporting date, plus any post-period capital action.
3. **Valuation earnings base** — the earnings, FCF, book value, NAV, or float figure
   the chosen valuation family actually multiplies or discounts.

Each must be confirmed by **two independent sources** (e.g. the filing plus a data
service) or **one filing-direct citation** (the primary document itself, cited with
date and line). If the two sources disagree, state the discrepancy, use the
filing-direct value, and **lower confidence one band**. Do not silently pick one.

This is the ordinary-path equivalent of the fact-checker that `debating-stocks`
runs; it is not optional.
```

- [ ] **Step 5: Add the WFV math line and verification block to report-template**

In `skills/analyzing-stocks/references/report-template.md`, in `### 7.2 估值结果`, after the line `- 期望收益与收益/风险比：` add:

```markdown
- 加权公允价值验算（必须显式列出，不能只给结论）：`Weighted Fair Value = sum(probability × scenario value)`
```

Then in `### 10.4 证据台账`, after the line `- 数据缺口及影响：` and before the fixed closing line, add:

```markdown

输入验证块（Input verification，见 Step 6.5，跳过即视为报告不完整）：

| 项目 | 来源 1 | 来源 2 / filing-direct | 通过/存疑 |
| --- | --- | --- | --- |
| 摊薄股数 diluted share count |  |  |  |
| 净债务/净现金 net debt |  |  |  |
| 估值盈利基数 valuation earnings base |  |  |  |

- 币种与交易线核对（ADR / 双重上市时必填）：`<primary currency ↔ tradable line>`
```

- [ ] **Step 6: Run the tests, full suite, and validator**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.InputVerificationContractTests -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: new tests PASS; full suite OK; validator passes.

- [ ] **Step 7: Commit**

```bash
git add skills/analyzing-stocks/SKILL.md skills/analyzing-stocks/references/source-policy.md skills/analyzing-stocks/references/report-template.md tests/test_skill_contracts.py
git commit -m "Add mandatory input-verification pass and explicit WFV arithmetic"
```

---

### Task 2: Valuation Input Discipline (M5, M6, M7, M8)

Bound the free parameters that dominate value: discount rate, terminal value, scenario probabilities, bear depth. Today the macro-overlay adjusts a discount rate relative to an *undefined* baseline; there is no WACC construction rule, no terminal-value numeric guardrail, no probability prior, and no bear plausibility benchmark.

**Files:**
- Modify: `skills/analyzing-stocks/references/value-investing-lens.md` (§3 modeling rules → WACC build + TV guardrail)
- Modify: `skills/analyzing-stocks/references/valuation-scenarios.md` (§1 → probability prior + bear benchmark)
- Modify: `skills/analyzing-stocks/references/macro-overlay.md` (floor note)
- Modify: `skills/analyzing-stocks/references/report-template.md` (§7.1 assumption rows)
- Modify: `tests/test_skill_contracts.py` (new class `ValuationInputDisciplineContractTests`)

> **Rebase note (Cycle-Trough Gate):** the merged-in Gate added a `### Cycle-Trough
> Cross-Check Gate` subsection to valuation-scenarios §1 (after the Re-basing Gate, at
> ~line 107) that includes a *cyclical* probability-asymmetry check. This task's
> `default prior of 25 / 50 / 25` is a **global** Hard-rule appended to the §1 bullet list
> (append after the existing `Do not change Bear/Base/Bull ... share price changed` line) —
> keep them distinct and complementary; do not edit inside the Gate's subsection.
> value-investing-lens.md and macro-overlay.md were NOT touched by the Gate, so §3 / §5 /
> the macro floor note apply cleanly.

- [ ] **Step 1: Write the failing contract tests**

Append to `tests/test_skill_contracts.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.ValuationInputDisciplineContractTests -v
```

Expected: all six FAIL.

- [ ] **Step 3: Add the WACC construction rule and TV guardrail to value-investing-lens §3**

In `skills/analyzing-stocks/references/value-investing-lens.md`, replace the `Modeling rules:` block (currently rules 1–5 ending with "Avoid terminal value dominating all value without justification.") with:

```markdown
Modeling rules:
1. Explicit forecast horizon: 5-10 years.
2. Growth and margin path must match moat and industry logic.
3. Discount rate must reflect business risk and leverage, built by the rule below.
4. Terminal growth should be conservative and below long-run nominal GDP in mature cases.
5. Avoid terminal value dominating all value without justification, bounded by the guardrail below.

### Discount Rate Construction

Build the discount rate explicitly, do not assert a round number:

- **Base:** current 10Y risk-free of the pricing currency + a stated **equity risk
  premium** (name the source/vintage) + business and leverage adders.
- **Floor:** for equities the discount rate may not fall below **risk-free + 300 bps**
  (adjust the exact adder only with stated justification). Macro-overlay regime
  adjustments apply on top of this build and may not breach the floor.
- State the build as a one-line sum in report Section 7.1 so the number is auditable.

### Terminal Value Guardrail

If **terminal value exceeds 75%** of total present value, a
**terminal sensitivity is mandatory** (vary terminal growth / exit multiple across a
plausible band) and **confidence caps at `Medium`** unless a Structural Re-rating Gate
with contracted-visibility evidence justifies the durability. Report the TV share of PV
in Section 7.1.
```

- [ ] **Step 4: Add the probability prior and bear benchmark to valuation-scenarios §1**

In `skills/analyzing-stocks/references/valuation-scenarios.md`, in `## 1) Scenario Construction Rules`, extend the `Hard rules:` list by appending two bullets after `- Do not change Bear/Base/Bull fair values solely because the current share price changed.`:

```markdown
- Probability discipline: start from a **default prior of 25 / 50 / 25** (Bear / Base /
  Bull). Deviations beyond **±15 pp** on any scenario require stated evidence; the
  **Bull scenario may not silently carry the thesis** via a probability shift in place
  of an assumption change.
- Bear plausibility benchmark: compare the Bear KPI path against the name's (or
  industry's) **worst historical drawdown** (revenue/margin/KPI). A generic −10% /
  −20% Bear is too mild for cyclicals; **a milder Bear must be justified** in one line.
```

- [ ] **Step 5: Add the floor note to macro-overlay**

In `skills/analyzing-stocks/references/macro-overlay.md`, in `## 1) Rate Regime`, after the per-family adjustments block (after the `Regulated utilities / telecom` bullet), add:

```markdown

**Floor interaction:** these regime adjustments apply on top of the discount-rate build
in `value-investing-lens.md` (§3 Discount Rate Construction) and
**may not breach the discount-rate floor** (risk-free + 300 bps for equities). A
`Falling`-rate cut that would push the rate below the floor is capped at the floor.
```

- [ ] **Step 6: Add the discipline rows to report-template §7.1**

In `skills/analyzing-stocks/references/report-template.md`, in `### 7.1 假设表`, immediately after the assumption table (after the `| 概率 |  |  |  |` row), add:

```markdown

估值纪律行（必填，配合 value-investing-lens §3 与 valuation-scenarios §1）：
- 折现率构建（discount-rate build 一行式）：`risk-free <x%> + ERP <y%> + adders <z%> = WACC <w%>`（不得低于 risk-free + 300 bps 地板）
- 终值占 PV 比例（TV share of PV）：`<pct>`（若 > 75% 则终值敏感性必填、confidence 上限 Medium）
- 概率分配理由（probability rationale，偏离 25/50/25 超过 ±15pp 时必须给证据）：
```

- [ ] **Step 7: Run the tests, full suite, and validator**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.ValuationInputDisciplineContractTests -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: new tests PASS; full suite OK; validator passes.

- [ ] **Step 8: Commit**

```bash
git add skills/analyzing-stocks/references/value-investing-lens.md skills/analyzing-stocks/references/valuation-scenarios.md skills/analyzing-stocks/references/macro-overlay.md skills/analyzing-stocks/references/report-template.md tests/test_skill_contracts.py
git commit -m "Bound WACC, terminal value, probabilities, and bear depth with explicit rules"
```

---

### Task 3: Cross-Sectional Reconciliation (M10, M9)

No valuation finalizes without live peer context and a moat-consistent terminal assumption. Today a valuation can pass every gate while implying an unexplained premium to the entire live peer set, and a weak moat does not force excess-return fade.

**Files:**
- Modify: `skills/analyzing-stocks/references/valuation-scenarios.md` (§8 sanity checks → required comps + moat linkage)
- Modify: `skills/analyzing-stocks/references/report-template.md` (new §7.6 comps table)
- Modify: `tests/test_skill_contracts.py` (new class `CrossSectionalReconciliationContractTests`)

> **Rebase note (Cycle-Trough Gate collision):** the merged-in Cycle-Trough Gate already
> occupies report-template `### 7.5 Cycle-trough cross-check`, so this task's comps table
> is **§7.6**, not §7.5. Its "Cross-Sectional Reconciliation" (peer comps) is a distinct
> concept from the Gate's "Cycle-Trough Cross-Check" (own-history cycle trough) — do not
> conflate or merge the two sections.

- [ ] **Step 1: Write the failing contract tests**

Append to `tests/test_skill_contracts.py`:

```python
class CrossSectionalReconciliationContractTests(unittest.TestCase):
    def test_scenarios_require_live_comps_reconciliation(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        self.assertIn("Cross-Sectional Reconciliation", scenarios)
        self.assertIn("3-5 peers", scenarios)
        self.assertIn("implied premium/discount", scenarios)
        self.assertIn("required output", scenarios)

    def test_scenarios_have_moat_terminal_linkage_rule(self) -> None:
        scenarios = read("skills/analyzing-stocks/references/valuation-scenarios.md")
        self.assertIn("moat verdict below 3.0", scenarios)
        self.assertIn("excess-return fade", scenarios)

    def test_report_template_has_live_comps_section(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("7.6 横截面对标", template)
        for column in ["可比公司", "当前倍数", "隐含溢价/折价"]:
            self.assertIn(column, template)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.CrossSectionalReconciliationContractTests -v
```

Expected: all three FAIL.

- [ ] **Step 3: Make cross-sectional reconciliation required in valuation-scenarios**

In `skills/analyzing-stocks/references/valuation-scenarios.md`, in `## 8) Sanity Checks`, after the existing four bullets (ending `- Confirm valuation does not ignore balance-sheet, dilution, or refinancing downside.`) add:

```markdown

### Cross-Sectional Reconciliation (required output)

A compact **live comps table** is a **required output**, not an optional sanity check:

- **3-5 peers** appropriate to the valuation family, with current multiples (the family's
  own multiple: EV/EBITDA or P/E for operating; P/TBV or P/B for financials; NAV or
  P/FFO for real estate; EV/resource for cyclicals).
- One-line reconciliation of the name's **implied premium/discount** vs the closest
  peer and why it is justified. A valuation implying an unexplained premium to the
  entire live peer set fails this check and must be revised or explained.

### Moat–Terminal Linkage

A **moat verdict below 3.0** (from `business-moat.md`) forces an explicit
**excess-return fade** horizon in the terminal assumptions: above-peer growth or margins
may not persist to perpetuity. A weak-moat name modeling decade-long above-peer economics
must state the specific evidence that overrides the fade.
```

- [ ] **Step 4: Add the comps section to report-template**

In `skills/analyzing-stocks/references/report-template.md`, insert a new subsection after the merged-in `### 7.5 Cycle-trough cross-check ...` block (before `## 8. 安全边际...`):

```markdown
### 7.6 横截面对标（live comps，必填）

对标 3-5 家可比公司，用估值家族对应的当前倍数，并解释隐含溢价/折价（参见 valuation-scenarios §8）。

| 可比公司 | 估值家族倍数 | 当前倍数 | 本名隐含倍数 | 隐含溢价/折价 |
| --- | --- | --- | --- | --- |
| Peer 1 |  |  |  |  |
| Peer 2 |  |  |  |  |
| Peer 3 |  |  |  |  |

- 对最接近可比公司的隐含溢价/折价理由（1行）：
- 护城河—终值联动（moat verdict < 3.0 时必须说明 excess-return fade 处理）：
```

- [ ] **Step 5: Run the tests, full suite, and validator**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.CrossSectionalReconciliationContractTests -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: new tests PASS; full suite OK; validator passes.

- [ ] **Step 6: Commit**

```bash
git add skills/analyzing-stocks/references/valuation-scenarios.md skills/analyzing-stocks/references/report-template.md tests/test_skill_contracts.py
git commit -m "Require live peer reconciliation and moat-consistent terminal fade"
```

---

### Task 4: Run-Stability & Adversarial Guards (E1 consumption, E3, E4)

Make estimate noise visible and directional bias resistible, without new infrastructure. Convert the *optional* `debating-stocks` escalation into a *required* second opinion for material decisions, isolate the user's stated view, and stop a below-noise-floor margin of safety from justifying a Buy.

**Files:**
- Modify: `skills/investment-decision-workflow/SKILL.md` (material-decision second opinion)
- Modify: `skills/analyzing-stocks/SKILL.md` (Step 1 user-view isolation)
- Modify: `skills/analyzing-stocks/references/value-investing-lens.md` (§5 MoS noise floor)
- Modify: `skills/analyzing-stocks/references/report-template.md` (opposing-case line in §9.0)
- Modify: `tests/test_skill_contracts.py` (new class `RunStabilityAdversarialContractTests`)

- [ ] **Step 1: Write the failing contract tests**

Append to `tests/test_skill_contracts.py`:

```python
class RunStabilityAdversarialContractTests(unittest.TestCase):
    def test_workflow_requires_second_opinion_on_material_decisions(self) -> None:
        workflow = read("skills/investment-decision-workflow/SKILL.md")
        self.assertIn("Material-Decision Second Opinion", workflow)
        self.assertIn("record both", workflow)
        self.assertIn("divergence > 15%", workflow)
        self.assertIn("defaults the execution to `Wait`", workflow)

    def test_controller_step1_isolates_user_directional_view(self) -> None:
        controller = read("skills/analyzing-stocks/SKILL.md")
        self.assertIn("User-View Isolation", controller)
        self.assertIn("strongest opposing case", controller)

    def test_lens_has_mos_process_noise_floor(self) -> None:
        lens = read("skills/analyzing-stocks/references/value-investing-lens.md")
        self.assertIn("process-noise floor", lens)
        self.assertIn("25-30%", lens)
        self.assertIn("cannot justify `Buy` on valuation grounds alone", lens)

    def test_report_template_red_team_has_opposing_case(self) -> None:
        template = read("skills/analyzing-stocks/references/report-template.md")
        self.assertIn("用户方向观点隔离", template)
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.RunStabilityAdversarialContractTests -v
```

Expected: all four FAIL.

- [ ] **Step 3: Add the Material-Decision Second Opinion to the workflow**

In `skills/investment-decision-workflow/SKILL.md`, in `## Adversarial Stress-Test (optional escalation)`, after the existing paragraph add:

```markdown

**Material-Decision Second Opinion (required, not optional):** for a decision at or
above the material-exposure threshold (`>= 2% - 3%` of net liquidation value, or a top
portfolio driver), a single valuation pass is not enough. Require **either** a
`$debating-stocks` run **or** an independent second valuation pass before execution, and
**record both** Weighted Fair Values in the decision record. If the two WFVs show
**divergence > 15%**, cap confidence one band and **defaults the execution to `Wait`**
until the divergence is reconciled. This is the manual precursor to measured run-variance
(P2 will score the paired WFVs).
```

- [ ] **Step 4: Add User-View Isolation to controller Step 1**

In `skills/analyzing-stocks/SKILL.md`, in `## Step 1: Define Scope`, after the line `- If user gives no constraints, assume a fundamental-investor context and label assumptions.` add:

```markdown
- **User-View Isolation:** if the user states a directional view at intake (e.g. "this
  looks like a golden pit", "I think this is a short"), construct and document the
  **strongest opposing case** before writing the valuation section, so the scenario
  construction is not anchored to the user's prior. Record it in report Section 9.0.
```

- [ ] **Step 5: Add the MoS process-noise floor to value-investing-lens §5**

In `skills/analyzing-stocks/references/value-investing-lens.md`, in `## 5) Margin of Safety Rules`, after the line `Do not use margin of safety in isolation. Combine with quality and balance-sheet checks.` add:

```markdown

**Process-noise floor:** the valuation engine has unmeasured run-to-run variance, so a
margin of safety below the **process-noise floor** (default **25-30%** for
long-duration / growth names, where estimate dispersion is widest)
**cannot justify `Buy` on valuation grounds alone**. Below the floor, a Buy needs a
non-valuation reason (quality re-rating with contracted visibility, catalyst, or
asymmetric optionality), stated explicitly.
```

- [ ] **Step 6: Add the opposing-case line to report-template §9.0**

In `skills/analyzing-stocks/references/report-template.md`, in `### 9.0 Red-Team Gate（sign-off 前必答，不可留空）`, after the confirmation-bias check item (item 3, ending `结论：`) and before item 4, add a new mandatory line:

```markdown

5. **用户方向观点隔离（User-View Isolation）**：如果用户在 intake 时给了方向性观点，
   在写估值前已构建的最强反方案（strongest opposing case）是什么？（若用户未给方向观点，
   写 `N/A - no user directional view`。）
   结论：
```

(Renumber is unnecessary — this is an added falsification item; keep it as item 5 after the existing four. Update the sentence "如果四条中有任一条" to "如果以上各条中有任一条" so the count is not hardcoded.)

- [ ] **Step 7: Run the tests, full suite, and validator**

```bash
.venv/bin/python -m unittest tests.test_skill_contracts.RunStabilityAdversarialContractTests -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' 2>&1 | tail -3
.venv/bin/python scripts/validate_repo.py --profile full
```

Expected: new tests PASS; full suite OK; validator passes.

- [ ] **Step 8: Commit**

```bash
git add skills/investment-decision-workflow/SKILL.md skills/analyzing-stocks/SKILL.md skills/analyzing-stocks/references/value-investing-lens.md skills/analyzing-stocks/references/report-template.md tests/test_skill_contracts.py
git commit -m "Require material-decision second opinion, user-view isolation, and MoS noise floor"
```

---

## Final Verification (after Task 4)

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | tail -4
.venv/bin/python scripts/validate_repo.py --profile full
.venv/bin/python scripts/validate_records.py --home tests/fixtures/state-home
bash tests/test_install.sh
```

Expected: everything passes. This mirrors CI (3.9/3.11/3.12 with `pip install pyyaml`).

## Spec Coverage Map

| Backlog finding | Task | Where enforced |
| --- | --- | --- |
| E2 single-pass data (share count / net debt / earnings base) | 1 | source-policy `Critical-Input Verification`, controller Step 6.5 |
| E3 (part) arithmetic re-check | 1 | report-template §7.2 explicit WFV math + §10.4 verification block |
| M5 no WACC construction rule / floor | 2 | value-investing-lens §3 `Discount Rate Construction`, macro-overlay floor note |
| M6 terminal-value dominance no guardrail | 2 | value-investing-lens §3 `Terminal Value Guardrail` |
| M7 bear plausibility benchmark | 2 | valuation-scenarios §1 bear-vs-worst-drawdown |
| M8 probability elicitation rules | 2 | valuation-scenarios §1 25/50/25 prior + ±15pp |
| M10 cross-sectional reconciliation | 3 | valuation-scenarios §8 required comps, report-template §7.6 |
| M9 moat→terminal linkage | 3 | valuation-scenarios §8 `Moat–Terminal Linkage` |
| E1 consumption (MoS noise floor) | 4 | value-investing-lens §5 process-noise floor |
| E3 (run-variance) / material second opinion | 4 | workflow `Material-Decision Second Opinion` |
| E4 user-view isolation | 4 | controller Step 1, report-template §9.0 item 5 |
```
