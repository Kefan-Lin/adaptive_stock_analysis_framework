# Unified Equity Research Report Template

## 1. 执行摘要

- 标的：`<Ticker / Company>`
- 分析日期：`<YYYY-MM-DD>`，币种：`<USD/CNY/AUD...>`
- 当前价格：`<price>`
- `Stance`：`Buy / Add / Hold / Reduce / Avoid`
- `Target Range`：`Bear / Base / Bull`
- `Weighted Fair Value`：
- `Expected Return`：
- `Margin of Safety`：
- `Confidence`：`High / Medium / Low`
- `Position Size`：`Core / Starter / Speculative / Watch-Avoid`

## 2. 公司与行业分型

- 主行业：
- 次行业（如有）：
- 路由到的行业 skill：
- `Analysis Family`：
- `Valuation Family`：
- 为什么使用该行业框架（2-4条）：
  1. ...
  2. ...
- `Merge Schema`：
  - primary skill 提供：`subtype / analysis family / valuation family / kpi tree / valuation anchors`
  - secondary skill 仅补充：`sections influenced`

## 3. 行业结构与核心变量树

- 行业结构判断：`Structural / Cyclical / Policy-driven / Transitional`
- 价值链位置：
- 一级驱动：`<价格 / 量 / 成本 / 资本结构 / 倍数>`
- 二级驱动：`<行业 KPI>`
- 不变量：
- 变量：
- 三个失效触发器：
  1. ...
  2. ...
  3. ...

## 4. 业务模式与护城河

- 客户价值主张：
- 收入机制：
- 成本结构与经营杠杆：
- 再投资路径：

| 护城河维度 | 评分(0-5) | 证据(Fact) | 侵蚀路径 |
| --- | --- | --- | --- |
| 成本优势 |  |  |  |
| 转换成本 |  |  |  |
| 网络效应 |  |  |  |
| 无形资产 |  |  |  |
| 有效规模 |  |  |  |
| 数据/流程优势 |  |  |  |

- 护城河结论：`Strong / Medium / Weak`

## 5. 管理层与资本配置

- 再投资质量：
- 回购/分红纪律：
- 并购质量：
- 稀释风险：
- 资本配置结论：`Strong / Mixed / Weak`

## 6. 财报与财务质量诊断

- 诊断家族：`operating-company / balance-sheet-financial / real-asset-property / probabilistic-healthcare / regulated-or-network / cycle-and-asset`
- 收入、盈利能力或 earning-power 质量：
- 资产负债表、资本或偿付韧性：
- 现金流、资金来源、跑道或分红覆盖：

| 模块 | 权重 | 评分(0-5) | 结论 |
| --- | --- | --- | --- |
| earning-power / 增长质量 | 20% |  |  |
| 利润率 / 承保 / 利差 / 物业现金流质量 | 20% |  |  |
| 资产负债表 / 资本强度 | 25% |  |  |
| 现金流 / 融资 / 跑道质量 | 25% |  |  |
| 会计 / 治理质量 | 10% |  |  |

- 财务质量结论：

## 7. 估值与三情景预测

### 7.0 Valuation change bridge vs prior report（重评时必填）

如果这是对已有本地报告的重评，先填下表。若没有 prior report，写 `N/A - first coverage`。
当前股价变化本身不是调整 Bear/Base/Bull 内在价值的理由；只能改变安全边际、预期收益、市场预期反推和仓位纪律。

| Item | Prior | Current | Change | Reason |
| --- | ---: | ---: | ---: | --- |
| Bear value |  |  |  |  |
| Base value |  |  |  |  |
| Bull value |  |  |  |  |
| Weighted fair value |  |  |  |  |

### 7.1 假设表

| 假设 | Bear | Base | Bull |
| --- | --- | --- | --- |
| 路由相关核心驱动 1 |  |  |  |
| 路由相关核心驱动 2 |  |  |  |
| 估值锚点输入（P/TBV / P/B / NAV / FFO / rNPV / DCF 等） |  |  |  |
| 资本、杠杆、稀释或跑道假设 |  |  |  |
| 概率 |  |  |  |

估值纪律行（必填，配合 value-investing-lens §3 与 valuation-scenarios §1）：
- 折现率构建（discount-rate build 一行式）：`risk-free <x%> + ERP <y%> + adders <z%> = WACC <w%>`（不得低于 risk-free + 300 bps 地板）
- 终值占 PV 比例（TV share of PV）：`<pct>`（若 > 75% 则终值敏感性必填、confidence 上限 Medium）
- 概率分配理由（probability rationale，偏离 25/50/25 超过 ±15pp 时必须给证据）：

### 7.2 估值结果

| 场景 | 主估值方法 | 辅助估值方法 | 综合每股价值 |
| --- | --- | --- | --- |
| Bear |  |  |  |
| Base |  |  |  |
| Bull |  |  |  |

- 概率加权价值：
- 期望收益与收益/风险比：
- 加权公允价值验算（必须显式列出，不能只给结论）：`Weighted Fair Value = sum(probability × scenario value)`

### 7.3 Structural re-rating sensitivity（如适用必填）

当新披露显示商业模式、合同结构、监管资产、收入可见性、盈利波动率、资本回报或融资风险发生结构性变化时，必须填本节；若不适用，写 `N/A - no structural re-rating evidence`。

| Item | Old regime | New regime | Valuation impact | Evidence strength |
| --- | --- | --- | --- | --- |
| 收入/现金流可见性 |  |  |  |  |
| 盈利波动率或风险溢价 |  |  |  |  |
| 估值倍数或折现率 |  |  |  |  |

- 是否进入 headline Base case：
- 若仅作为 sensitivity，触发进入 Base case 的证据：

### 7.4 盈利基准 re-basing（盈利拐点/中枢上移时必填）

当最近一个季度的年化 run-rate 与 trailing 全年/TTM 盈利基准出现显著背离时必须填本节
（参见 financial-diagnostics 的 earnings-base representativeness 检查与 valuation-scenarios
的 `Earnings Base Re-basing Gate`）。若不适用，写 `N/A - trailing base representative`。
注意：re-rating 改的是倍数，re-basing 改的是盈利基数水平，二者独立，可同时发生。

| Item | trailing 基准（FY/TTM） | forward run-rate 基准 | 背离幅度 | 证据强度 |
| --- | ---: | ---: | ---: | --- |
| 营收/盈利基数 |  |  |  |  |

- 背离归类：`结构性跳档（re-base 至 forward run-rate）` / `一次性·峰值·提前确认（维持 trailing 归一化基准）`
- 季节性方向（强劲季度是否本为季节性弱季）：
- 支持向上 re-basing 的佐证（新产能投产 / 在手订单 backlog / 价格·渠道确认 / 毛利可持续性 / 现金转化）：
- 估值实际采用的盈利基数（trailing 还是 forward run-rate）：
- 是否进入 headline Base：`是 / 否（仅作上行 sensitivity）`

### 7.5 Cycle-trough cross-check（周期性/商品关联标的必填）

当标的在 industry-structure 中被判为 cyclical 或 commodity-linked（含 `Cyclical + Structural`），
且正在设定或变更 Bear/Base/Bull 时必须填本节（参见 valuation-scenarios 的
`Cycle-Trough Cross-Check Gate`）。若不适用，写 `N/A - not cyclical/commodity-linked`。
本节是上行两道 gate（re-rating / re-basing）的对称下行交叉检验，不推翻已通过证据门槛的上调，
只暴露其中未被证据支撑的部分。

- `Gate verdict`：`Bear stands / Bear pulled down / insufficient disclosure (Confidence lowered)`（一行结论）：
- 周期位置：`early / mid / late / peak`，证据（价格 vs 成本曲线 / 利润率 vs 历史 / 库存 / 资本开支周期 / 供给公告）：

| 历史振幅（至少最近两个完整周期，公司过短则用最接近的行业代理并说明） | 峰值 | 谷底 | 峰-谷变化% |
| --- | ---: | ---: | ---: |
| 营收 |  |  |  |
| 毛利率 |  |  |  |
| EPS（EPS 转负时改用 FCF 或每股账面价值） |  |  |  |

- Floor-coverage 算术：由 *已披露* 合同机制（take-or-pay / 最低收入条款 / 价格下限或 collar /
  套保头寸 / 带取消条款的 backlog / 受监管或合约锁定收入份额）保护的当前 run-rate 营收与盈利份额：
  Bear 只能计入此已披露覆盖度；未覆盖部分按中周期或历史谷底经济学（取证据支持者）压力测试。
- Bear 内明确的谷底锚（trough 盈利 × trough 倍数，或 P/B / NAV / 重置成本资产底）——采用哪个锚及其数值（即使 headline Bear 高于该锚也须列出）；旧谷底价格不可考据时，以财报每股账面价值为 Fact、谷底价格/倍数标注为 Inference 并注明方法，不得杜撰引用：
- Gap 说明：若 headline Bear 高于谷底锚，把差额换算成 Bear 的*隐含* EPS×倍数、对照历史振幅表检验（Bear 是情景现值、锚是谷底一瞬，须在盈利水平上同口径比较）；差额只能由已披露 floor 覆盖度加已通过上行 gate 的结构性论据解释，其中仅定性通过的论据只能支撑 bear 倍数/久期，不能把 bear 盈利抬到接近当前 run-rate；无法解释则下调 Bear：
- 概率对称性检查：若周期证据为 late-cycle 或 peak，维持对称概率须给出一行理由，否则加厚 Bear 尾部：
- Base-over-run-rate 检查：late/peak 时 Base 归一化盈利 ≥ 最新年化 run-rate 须给一行理由（已通过 re-basing gate 即为该理由），否则 Base 设于中周期或以下：

### 7.6 横截面对标（live comps，必填）

对标 3-5 家可比公司，用估值家族对应的当前倍数，并解释隐含溢价/折价（参见 valuation-scenarios §8）。

| 可比公司 | 估值家族倍数 | 当前倍数 | 本名隐含倍数 | 隐含溢价/折价 |
| --- | --- | --- | --- | --- |
| Peer 1 |  |  |  |  |
| Peer 2 |  |  |  |  |
| Peer 3 |  |  |  |  |

- 对最接近可比公司的隐含溢价/折价理由（1行）：
- 护城河—终值联动（moat verdict < 3.0 时必须说明 excess-return fade 处理）：

## 8. 安全边际、市场预期反推、价值陷阱判断

| 场景 | 内在价值 | 当前价 | 安全边际 |
| --- | --- | --- | --- |
| Bear |  |  |  |
| Base |  |  |  |
| Bull |  |  |  |
| 加权 |  |  |  |

- 安全边际分档：`高 / 中 / 低`
- 市场预期反推方法：`Reverse DCF / implied ROTCE / implied ROE / implied cap rate / implied PoS / other`
- 市场预期反推结论：
- 价值陷阱检查：`通过 / 警惕 / 不通过`
- 明确 downside path：

## 9. Red-Team 门禁 → 投资结论、仓位建议、加减仓条件

### 9.0 Red-Team Gate（sign-off 前必答，不可留空）

在写下最终 Stance 之前，完成以下四项强制falsification检查：

1. **最高风险桶驱动的反转场景**：如果 `risk-register.md` 中评级最高的一个桶演变成现实，
   Stance 将如何变化？（例如："监管风险升为高 → 营收下降 20% → DCF 价值降至 Bear 场景以下 → Stance 降为 Avoid"）
   结论：

2. **关键假设失效测试**：Base 估值中哪一个假设如果被证伪，会让加权公允价值跌破当前价格的 10%？
   结论：

3. **确认偏误检查**：写出一条最容易让当前论点显得比实际更强的证据（过度加权的证据、遗漏的反驳）。
   结论：

4. **盈利中枢上移证伪（双向）**：如果最近季度 run-rate 显著高于 trailing 基准，必须做双向证伪——
   正向：若结构性 re-basing 的佐证不成立（只是 one favorable quarter），forward-based 估值是否过度乐观？
   反向：若盈利中枢确已上移，当前 trailing-based 估值是否系统性低估，从而错误地 Avoid/Reduce 一个拐点标的？
   （若 run-rate 与 trailing 无显著背离，写 `N/A - trailing base representative`。）
   结论：

5. **用户方向观点隔离（User-View Isolation）**：如果用户在 intake 时给了方向性观点，
   在写估值前已构建的最强反方案（strongest opposing case）是什么？（若用户未给方向观点，
   写 `N/A - no user directional view`。）
   结论：

如果以上各条中有任一条导致论点无法支持当前 Stance，必须将 Stance 至少降低一档后再继续。

### 9.1 投资结论

- `Stance`：`Buy / Add / Hold / Reduce / Avoid`
- `Position Size`（per-name，来自 portfolio-sizing.md）：`Core / Starter / Speculative / Watch-Avoid`
- `Position Size`（portfolio-adjusted，来自 portfolio-construction.md）：`Core / Starter / Speculative / Watch-Avoid`
- 如果两者不同，说明调整原因（行业上限/相关性/因子集中度）：
- `Add-on Trigger`：
- `Trim/Exit Trigger`：
- 何种证据会改变观点：

## 10. 风险、催化剂、监控指标、证据台账

### 10.1 风险清单（按类别，参见 risk-register.md）

完成 `risk-register.md` 八桶评估后，在此列出所有 `Medium` 或 `High` 评级的桶：

| 风险类别 | 评级 | 关键证据（1行） |
| --- | --- | --- |
| 监管与政策 |  |  |
| 客户与收入集中度 |  |  |
| 供应链与投入成本 |  |  |
| 杠杆与债务契约 |  |  |
| 会计与盈利质量 |  |  |
| 诉讼、ESG 与或有负债 |  |  |
| 竞争与颠覆 |  |  |
| 地缘政治与汇率 |  |  |

- 整体风险等级：`Low / Medium / High`
- 来自风险清单的 Stance 约束（如有）：

### 10.2 催化剂（每条必须包含时间、概率、估值影响）

| # | 催化剂描述 | 预期时间区间 | 触发概率 | 估值影响（±%） |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

说明：
- 预期时间区间：例如 `2025Q3`、`FY2026H1`、`12-18个月内`
- 触发概率：主观估计，如 `高（>60%）/ 中（30-60%）/ 低（<30%）`
- 估值影响：相对于 Base 估值的加权公允价值变化，例如 `+15%`（正向触发）或 `-20%`（风险催化剂）
- 如果是 biotech 或 binary outcome，每条 catalyst 还需对应 `industry-playbooks.md` 中的 catalyst calendar 格式

### 10.3 监控指标
1. `<KPI/阈值>` → `<动作>`
2. `<KPI/阈值>` → `<动作>`
3. `<KPI/阈值>` → `<动作>`

### 10.4 证据台账
- Facts（带日期与来源）：
- Inferences（推断链）：
- Assumptions（关键假设）：
- 数据缺口及影响：

输入验证块（Input verification，见 Step 6.5，跳过即视为报告不完整）：

| 项目 | 来源 1 | 来源 2 / filing-direct | 通过/存疑 |
| --- | --- | --- | --- |
| 摊薄股数 diluted share count |  |  |  |
| 净债务/净现金 net debt |  |  |  |
| 估值盈利基数 valuation earnings base |  |  |  |

- 币种与交易线核对（ADR / 双重上市时必填）：`<primary currency ↔ tradable line>`

最后一行固定输出（与 Section 9.0 Red-Team Gate 第 2 条呼应）：
`最可能错的地方是：...`
