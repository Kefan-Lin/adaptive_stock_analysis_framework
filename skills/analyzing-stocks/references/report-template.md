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

### 7.2 估值结果

| 场景 | 主估值方法 | 辅助估值方法 | 综合每股价值 |
| --- | --- | --- | --- |
| Bear |  |  |  |
| Base |  |  |  |
| Bull |  |  |  |

- 概率加权价值：
- 期望收益与收益/风险比：

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

在写下最终 Stance 之前，完成以下三项强制falsification检查：

1. **最高风险桶驱动的反转场景**：如果 `risk-register.md` 中评级最高的一个桶演变成现实，
   Stance 将如何变化？（例如："监管风险升为高 → 营收下降 20% → DCF 价值降至 Bear 场景以下 → Stance 降为 Avoid"）
   结论：

2. **关键假设失效测试**：Base 估值中哪一个假设如果被证伪，会让加权公允价值跌破当前价格的 10%？
   结论：

3. **确认偏误检查**：写出一条最容易让当前论点显得比实际更强的证据（过度加权的证据、遗漏的反驳）。
   结论：

如果三条中有任一条导致论点无法支持当前 Stance，必须将 Stance 至少降低一档后再继续。

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

最后一行固定输出（与 Section 9.0 Red-Team Gate 第 2 条呼应）：
`最可能错的地方是：...`
