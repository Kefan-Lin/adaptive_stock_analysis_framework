# 研究打分卡 v1：单一规范与卡片契约

完整研究完成既有分析和关键输入核验后，从已引用的分析证据组装三卡。运行公开入口 `scorecard.card.validate_card(card)`，通过后在十章报告摘要展示并将论证指向正文。完整报告确认完成后通过下述快照入口保存，并依据返回结果说明保存状态。卡片组装不执行估值计算，不把质量分用于买卖或仓位自动映射。

## 规范版本与公用接口

结构版本 `schema_version: 1` 与评分规范版本 `rubric_version: "1.0"` 分开。卡片顶层包含 `company_quality`、`price_attractiveness`、`decision_conditions` 和 `report_reference`。公开的 Python 校验入口接收字典，合法时原样返回，非法时抛 `CardValidationError`；不读写私人目录。供后续保存、局部复核、精确引用及行业伴侣接入使用同一卡片字典，不各造评分规范。虚构完整示例见 `examples/research-scorecard/fictional-card.json`，报告见其同目录 `fictional-report.md`。快照的独立身份与时点见下述持久化入口；历史比较由后续任务定义；卡片中的 `assessed_at` 是原评估日，`as_of` 是信息截止日，沿用项的 `source_snapshot` 为来源版本，`review_status: carried_forward` 表示本次未复核。新评估用 `reviewed`。报告引用为可定位的 `report_reference`，当前不是已保存快照的承诺。

八维在 `company_quality.dimensions` 中各出现一次，使用以下稳定 id。每项必含 `id`、`status`（`assessed`、`insufficient_information`、`not_applicable`）、`score`、`confidence`、`rationale`、`supporting_evidence`、`counterevidence`、`counterevidence_search`、`open_questions`、`review_triggers`、`assessed_at`、`as_of`、`review_status`。2/4 分另加 `adjacent_anchor_explanation`，写清满足的相邻锚点及未达到更高档的差距；沿用另加 `source_snapshot`。已评估的分数严格为 1–5 整数，可信度严格为 high / medium / low，必须有支持证据、反证或具体检索范围。没有形成判断用空分数和空可信度，信息不足写明具体缺口；不适用给出适用性理由。不得因表现差或资料缺失标不适用，不得用低可信度代替信息不足。事实材料可跨维使用，但逐维说明其不同含义，不重复加权；无跨维总分。缺足够材料时坦陈尚未核查，不编造反证或来源。

每条证据至少含 `id`、`source`（精确定位）、`source_date`、`summary` 与 `kind`（fact / management_claim / inference）。推断还含 `depends_on`（本项已有证据 id）和 `assumptions`；来源日期不得晚于信息截止日。可信度高指关键判断直接可追溯、覆盖必要时期且解释主要矛盾；中指足以判断但历史覆盖、独立核实或细节有缺口；低指初步判断依赖单方说法、间接指标或强假设，须列出待验证事项。官方披露不自动等于高可信度，转载不算独立来源。

## 完整研究快照

只有分析、输入核验、卡片校验和完整报告都完成后，才调用 `scorecard.create_snapshot(home, symbol, market, card, as_of=...)`。`home` 是现有私人 state-home 的绝对目录，缺失或不可访问时可传 `None` 或原路径。`symbol` 和 `market` 遵守 canonical tradable-line 身份；`as_of` 是本次研究信息截至日，与各维原评估日分开。返回的 `SaveResult(saved, snapshot_id, reason)` 仅在 `saved=True` 时提供可引用的快照标识；`saved=False` 时明确告诉用户未保存及原因，不退回公共仓库。纯研究不需要 stance、execution_method 或决策记录；临时聊天不调用保存入口。

快照无覆盖写入 `<state-home>/research-scorecards/<SYMBOL>/<YYYY-MM-DD-UUID>.json`，与 `records/` 分开。`scorecard.read_snapshot(home, symbol, snapshot_id)` 精确读取并验证身份；`scorecard.validate_snapshot(snapshot)` 校验独立结构版本、评分规范版本、三卡、证据、创建时点、信息截至时点、复核范围和报告引用。目前只接受 `review_scope='full'` 且八维均标记本次复核。局部复核、修正和历史比较由后续任务实现。

## 八维锚点

| id 与维度 | 1：明显薄弱 | 3：中等、优劣并存 | 5：突出且可持续 |
| --- | --- | --- | --- |
| `industry_economics` 行业经济性 | 长期供过于求、议价弱，价值难留在行业内 | 有合理盈利空间，但竞争或周期约束明显 | 需求韧性强，供给纪律和价值分配有利于长期回报 |
| `business_model` 商业模式 | 单位经济性差，规模扩大仍难改善 | 盈利机制成立，但受成本、资本投入等约束 | 客户价值可稳定转化为股东收益，规模与资本效率良好 |
| `product_competitiveness` 产品竞争力 | 客户持续流失，产品性价比或效果落后 | 能满足需求，与竞争者各有优劣 | 客户选择、留存及付费行为体现明显优势 |
| `moat_durability` 护城河持续性 | 优势易被复制，替代或侵蚀正在发生 | 存在一定壁垒，但耐久性有限 | 优势难以复制，竞争与技术变化下仍能维持 |
| `management_governance` 管理层与治理 | 已证实严重失信、利益侵占或长期执行失当 | 能力与治理表现有好有坏 | 长期兑现承诺，激励合理，公平对待小股东 |
| `capital_allocation` 资本配置与再投资 | 投资、并购或融资持续损害每股价值 | 配置结果参差，整体回报合理 | 再投资及现金分配有纪律，持续提升每股价值 |
| `earnings_cash_quality` 盈利与现金质量 | 盈利失真或不可持续，现金与利润长期背离且解释不足 | 盈利基本可信，但波动、一次性项目或转化存在约束 | 盈利来源可持续、会计稳健，适用的现金或收益质量指标良好 |
| `financial_resilience` 财务韧性 | 流动性、偿债或融资风险可能威胁持续经营 | 正常情况下可承受，压力情景下有明显弱点 | 在合理压力情景下仍有充足缓冲与融资自主性 |

2、4 分位于相邻锚点之间，理由说明符合项及剩余差距。产品竞争力看当前客户选择；护城河持续性看优势耐久。行业和诊断家族选择适用指标：银行用资本、资产质量、流动性评价财务韧性，不强制普通企业 FCF 或净债务/EBITDA；未商业化企业不因尚无收入在盈利质量得 1 分，应判断适用性并检查现金消耗、融资依赖。行业专项映射以后单独接入。

## 价格与决策

`price_attractiveness` 有 `status`、`reason`、`valuation`；无估值时状态为 not_assessed 或 insufficient_information，原因写明，valuation 为 null。已有估值原样引用来源报告、币种、价格及估值时点、主方法、盈利/现金流口径、预测期限，以及原报告实际具有的情景及其含义、合理价值、安全边际和市场隐含预期。原模式未产出的情景用空映射，未产出的安全边际或隐含预期明确为 null；不补造输出。首次局部研究尚无判断的维度，`assessed_at` 与 `as_of` 可为 null，已有证据则须给资料截至时点。只引用原框架已有输出，不为填卡创造新模型。纯价格变化只更新价格相关信息，不倒推质量分或内在价值。

`decision_conditions` 有 `material_issues`、`thesis`、`falsifiers`、`evidence_gaps`、`portfolio_fit`、`execution_conditions`。重大问题独立写 `status`（unverified / confirmed）、`description`、`impact`、`verification`、`evidence`；已确认要有来源证据，待核实疑点不直接定性为欺诈。组合或执行缺材料时状态为 insufficient_information 或 not_assessed，并说明原因。重大问题独立呈现，不被高分抵消，也不是自动交易信号。

## 与原报告及估值的边界

保留原 0–5 护城河维度评分与原五类加权财务评分的名称、用途和数值；新质量分另名且不机械换算。分歧写清双方衡量对象和具体复核事项。已有股票先读原报告与决策记录，核对原方法、盈利/现金流口径、估值时点、期限、Bear/Base/Bull 含义。现有模式内可以用有来源的新输入重估或修算术错误并解释影响；卡片组装本身不重估。新 gate、完整重跑、错误修复或第二意见不构成换模式许可；用户明确许可优先，改模式时记录许可与日期，保留旧模型并区分事实、方法和假设变化。旧模式限制可指出，但不能把沿用值称为重新确认。报告十章保持原结构，摘要三卡与对应正文使用同一张已校验卡。
