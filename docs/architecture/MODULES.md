# 自适应股票分析框架 · 架构与模块手册

核对日期：2026-10-30（Asia/Shanghai）；源码基准：`59f227e15ec34e143fb2335b139fe3798760df41`。

基于当前 checkout 的静态源码核对。16 个技能、10 个行业策略、15 份共享参考；50 个功能模块。技能节点描述宿主执行的约定，Python 节点描述已存在的函数/CLI。箭头聚焦主要调用、文件消费或技能交接，不代表常驻服务 RPC。

## 图册

- [全景架构](01-overview.html) · [Archify JSON](01-overview.architecture.json)
- [研究与决策](02-research.html) · [Archify JSON](02-research.architecture.json)
- [反转发现](03-discovery.html) · [Archify JSON](03-discovery.architecture.json)
- [私有状态与晨检](04-state-monitor.html) · [Archify JSON](04-state-monitor.architecture.json)
- [评分与回测](05-evaluation.html) · [Archify JSON](05-evaluation.architecture.json)
- [安装、CI 与原型](06-runtime-support.html) · [Archify JSON](06-runtime-support.architecture.json)

## 关键阅读边界

- 决策记录是文件型数据枢纽；仓库外的真实状态没有嵌入本图册。
- 发现技能可以直接交接研究控制器；需要行动方案时再由决策工作流统筹。
- 代码筛选不自动触发 LLM 辩论；技能层必经门与 Python 排序资格是两种不同约束。
- P0、P1、P2 是独立 CLI；P1/P2 没有自动执行 P0 的完整严格校验。
- P1 用每个标的 latest；P2 用所有有效真实记录；历史 INDEX 行不进入 P2。
- 结果校准目前只测量、不自动反馈控制；晨检与评分手动触发。
- Web App 计划与 .scratch 本地原型分开标识；本轮未验证线上部署。

## 模块详解

## 研究与决策

### r01 · 决策工作流与模式路由

状态：技能契约 · 宿主 Agent 执行

**输入**

- 用户想法、已有报告、真实持仓/期权腿、事件；可读的外置状态目录

**内部主要逻辑**

1. 按 Position Review > Event Review > Existing Report to Action > New Idea Decision 选择 Mode，并给 Reason。
2. 读取组合与目标标的最新记录；执行 Live Verification、Stale Check 和 Action-Blocking Refresh Gate。
3. 新研究或重大过期调用 analyzing-stocks；已有材料执行增量估值更新。

**输出**

- Mode / Reason、核验结果、过期项、Missing Inputs；研究调用范围

**源码证据**

- [skills/investment-decision-workflow/SKILL.md:16](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/investment-decision-workflow/SKILL.md#L16)

### r02 · 研究控制器与行业 Merge schema

状态：技能契约 · 宿主 Agent 执行

**输入**

- 公司、交易所、币种、日期、投资期限和风格

**内部主要逻辑**

1. 确定实际可交易上市线；构造最强反方以隔离用户方向性观点。
2. 选择一个主行业、可选副行业；选 analysis family 与 valuation family；多引擎控股业务按 SOTP 分部估值。
3. 合并 subtype、kpi tree、normalizations、valuation anchors、risk checklist、monitor triggers、sections influenced；副行业只补约定章节。

**输出**

- 统一分析路由与行业契约；缺字段时标记不完整、下调置信度

**源码证据**

- [skills/analyzing-stocks/SKILL.md:46](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L46)
- [skills/analyzing-stocks/SKILL.md:250](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L250)

### r03 · 共享参考与证据台账

状态：技能契约 · 宿主 Agent 执行

**输入**

- 行业路由、财报/公告/指引/资本行动、价格与宏观事实

**内部主要逻辑**

1. 共享参考共 15 份：source-policy、industry-structure、industry-playbooks、business-moat、financial-diagnostics、capital-allocation、macro-overlay、valuation-router、valuation-scenarios、value-investing-lens、risk-register、portfolio-sizing、portfolio-construction、report-template、decision-records。
2. 为关键量标日期与来源；区分 Fact / Inference / Assumption，维护假设优先级与敏感性。
3. 按路由决定财务诊断与估值锚；decision-records 在配置状态目录时加载。

**输出**

- Source map、evidence ledger、假设台账、行业方法约束

**源码证据**

- [skills/analyzing-stocks/SKILL.md:114](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L114)
- [skills/analyzing-stocks/SKILL.md:134](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L134)

### r04 · 财务诊断、情景估值与估值更新门

状态：技能契约 · 宿主 Agent 执行

**输入**

- 行业 KPI、归一化财务、来源证据、宏观参数、原有情景

**内部主要逻辑**

1. 按经营公司/资产周期/金融账簿/地产/概率医疗/受监管网络选择诊断与估值家族。
2. 形成 Bear/Base/Bull 假设与敏感性；检验结构重评级、盈利基准重设及周期谷底交叉核查。
3. 价格本身不构成内在价值变动证据；估值变化必须归因于可验证的经营/现金流/风险变化。

**输出**

- Bear/Base/Bull、公允价值加权值 WFV、安全边际、市场隐含预期、价值陷阱判断

**源码证据**

- [skills/analyzing-stocks/SKILL.md:148](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L148)
- [skills/analyzing-stocks/references/valuation-scenarios.md:59](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/references/valuation-scenarios.md#L59)

### r05 · 输入核验与统一 10 块报告

状态：技能契约 · 宿主 Agent 执行

**输入**

- 稀释股数、净债务、估值使用的基期财务量、情景与概率

**内部主要逻辑**

1. 核验关键输入并检查基期盈利合理性；修正输入后重算所有依赖数字。
2. 显式展示 sum(probability × fair value)；形成 Stance、Position Size 和触发条件。
3. 输出执行摘要、分类、行业结构、护城河、资本配置、财务诊断、估值情景、安全边际、结论仓位、风险证据台账等 10 块。

**输出**

- 统一研究报告；Buy/Add/Hold/Reduce/Avoid；Core/Starter/Speculative/Watch-Avoid

**源码证据**

- [skills/analyzing-stocks/SKILL.md:186](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L186)
- [skills/analyzing-stocks/SKILL.md:271](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/SKILL.md#L271)

### r06 · 多方辩论、独立核查与裁决

状态：技能契约 · 宿主 Agent 执行

**输入**

- 争议 resolution、当前价格锚、期限、双方论点与研究范围

**内部主要逻辑**

1. 主持人保存转录并设定双方；同轮独立 Debater 平行研究，输出最强论证和情景回报拆解。
2. 将对方上一轮完整论点送入交叉反驳；中立 verifier 对实质主张标 Supported / Disputed / Unverifiable，并重算算术。
3. 主持人折扣争议事实后合成 cruxes、置信度、翻转条件；回填 Red-Team / value-trap / Stance / 仓位。

**输出**

- 核查台账、强反方、情景年化回报、裁决、Add-on/Trim-Exit 与监控条件

**源码证据**

- [skills/debating-stocks/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/debating-stocks/SKILL.md#L31)

边界：这是文档定义的多 Agent 工作流；本轮未执行股票辩论或验证具体模型调用。

### r07 · 行动适配、风险预算与记录写入

状态：技能契约 · 宿主 Agent 执行

**输入**

- 当前有效估值、Candidate Tier、Valuation Zone、真实敞口、期权条款

**内部主要逻辑**

1. 映射 Core Candidate / Tactical Candidate / Reject 与四个估值区；应用技术执行过滤、财报风险和期权门。
2. 扣除指派预留和现金底线，给 stock-equivalent exposure、单名/分组上限、资金分配与再平衡方案。
3. 生成 Decision Brief + Execution Sheet；有有效立场/执行方式时按技能契约写记录与 INDEX；确认成交后补 action_taken / portfolio。

**输出**

- 具体条件执行表或 No Action；decision-record/v1 与时间线

**源码证据**

- [skills/investment-decision-workflow/SKILL.md:309](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/investment-decision-workflow/SKILL.md#L309)

边界：纯 Missing Inputs / conditional-only 结果不产生记录；这里的执行表不等于自动向券商下单。

### r08 · 行业策略 · 软件与平台

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：ARR、NRR、bookings、毛利、CAC payback、SBC、每股 FCF。
2. 检查递延收入、资本化佣金、并购增长、principal-agent；比较订阅与 usage/AI 变现的持久性。
3. 选择估值路径：FCFF DCF；成熟期 EBIT/P/E；Sales 必须有利润率桥；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-software-platforms/SKILL.md:37](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-software-platforms/SKILL.md#L37)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r09 · 行业策略 · 消费与零售

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：客流、同店销售、客单价、促销、库存、租约、会员与广告。
2. 归一化库存、租赁杠杆、GMV 到收入与加盟/平台净额；检验促销依赖与会员经济。
3. 选择估值路径：DCF/FCFE；EV/EBIT/P/E；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-consumer-retail/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-consumer-retail/SKILL.md#L31)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r10 · 行业策略 · 工业与运输

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：订单、backlog、利用率、book-to-bill、维护资本开支、服务附着。
2. 检查完工比例确认、重组与养老金/租赁；量化不可取消订单覆盖，建立谷底利用率与盈利底。
3. 选择估值路径：穿周期 DCF；EV/EBITDA/EBIT；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-industrials-transport/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-industrials-transport/SKILL.md#L31)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r11 · 行业策略 · 半导体与硬件

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：ASP、出货、稼动率、良率、库存、资本开支、SCA/LTA。
2. 归一化折旧和峰值利润；区分价格/数量保护；用已披露合约覆盖与 P/B/重置成本交叉核查周期 Bear。
3. 选择估值路径：穿周期 DCF；按成熟度补 EV/Sales 或 EV/EBITDA；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-semiconductors-hardware/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-semiconductors-hardware/SKILL.md#L31)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r12 · 行业策略 · 资源、能源与材料

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：价格、产量、储量、AISC、维持资本开支、对冲与承购。
2. 按中周期/谷底商品价格重估；区分增长与维持 capex；量化披露的对冲/承购保护和关闭义务。
3. 选择估值路径：中周期 DCF/NAV；EV/resource、EV/EBITDA；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-resource-energy-materials/SKILL.md:35](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-resource-energy-materials/SKILL.md#L35)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r13 · 行业策略 · 银行

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：NIM、信贷成本、CET1、存款 beta、ROTCE、TBV。
2. 分离准备金释放、CECL、AOCI 与真实信用趋势；检查存款质量、资本生成与盈利波动。
3. 选择估值路径：P/TBV + ROTE / Gordon；稳定盈利时补 P/E；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-banks/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-banks/SKILL.md#L31)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r14 · 行业策略 · 保险

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：combined ratio、准备金、偿付能力、float、BVPS、ROE。
2. 归一化灾损和准备金释放；核查资产负债期限错配、定价充足性及 float 的持久性。
3. 选择估值路径：P/B + ROE / 超额资本；股息或盈利收益率；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-insurers/SKILL.md:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-insurers/SKILL.md#L31)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r15 · 行业策略 · 地产与 REIT

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：入住率、NOI、NAV、AFFO、LTV、到期债务、WALT。
2. 归一化直线租金、维护 capex 与开发利润；检查租户信用与 cap rate；轻资产服务可留经营公司估值。
3. 选择估值路径：重资产 NAV + FFO/AFFO；轻资产 EBIT/FCF/DCF；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-real-estate/SKILL.md:34](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-real-estate/SKILL.md#L34)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r16 · 行业策略 · 医疗与生物科技

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：成功概率、峰值销售、医保准入、试验催化、现金 runway、稀释。
2. 区分商业运营与未商业化管线；归一化合作款/里程碑，概率加权并计入融资/版税泄漏。
3. 选择估值路径：未商业化 rNPV/SOTP；商业医药/器械/服务按 DCF/倍数；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-healthcare-biotech/SKILL.md:35](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-healthcare-biotech/SKILL.md#L35)

边界：由控制器合并并统一输出，不单独替代研究控制器。

### r17 · 行业策略 · 公用事业与通信

状态：技能契约 · 宿主 Agent 执行

**输入**

- 控制器已选此主/副行业；行业子类型；财务与业务证据

**内部主要逻辑**

1. 建立 KPI 树：用户、ARPU、churn、rate base、允许 ROE、capex、PPA。
2. 核查资本化成本、费率时滞、股息覆盖、频谱与网络负担，以及合同/监管可见性。
3. 选择估值路径：公用 DCF/DDM；通信 DCF/EV/EBITDA；塔纤可用 AFFO；输出三项价值驱动、失败风险和 monitor thresholds。

**输出**

- subtype、analysis/valuation family、KPI tree、normalizations、anchors、risk checklist、monitor triggers、sections influenced

**源码证据**

- [skills/analyzing-utilities-telecom/SKILL.md:34](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-utilities-telecom/SKILL.md#L34)

边界：由控制器合并并统一输出，不单独替代研究控制器。

## 反转发现

### d01 · 发现 CLI 与 LLM 预筛脚本

状态：已实现 · Python

**输入**

- cmd、tickers、top_n、with_text、control_keep、as_of；可选 ticker 文件

**内部主要逻辑**

1. CLI 分派 canary / backtest / discover / ashare-discover；不同命令明确选择 PIT 回测或当期数据。
2. prescreen 要求至少 60 条价格、A 门通过、可用财务；达到 limit 后停止并按 A 分数排序。

**输出**

- 命令行候选摘要；--out 回测 JSON；LLM 可读预筛名单

**源码证据**

- [inflection_discovery/cli.py:18](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/cli.py#L18)
- [skills/discovering-inflections/scripts/prescreen.py:28](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/discovering-inflections/scripts/prescreen.py#L28)

### d02 · SEC EDGAR 与缓存配置

状态：已实现 · Python

**输入**

- ticker / URL；SEC_USER_AGENT；INFLECTION_CACHE、超时、重试与请求间隔配置

**内部主要逻辑**

1. 当前 SEC ticker map 解析 CIK；读取 companyfacts / submissions。
2. JSON 请求命中磁盘缓存优先；未命中先核 UA，再限频并对 403/429/5xx 或传输异常退避重试。
3. companyfacts / submissions 另做进程内 memo；配置默认在 .cache_inflection 创建缓存目录。

**输出**

- 原始 JSON、None 数据缺口或请求错误；缓存 JSON

**源码证据**

- [inflection_discovery/edgar.py:43](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/edgar.py#L43)
- [inflection_discovery/config.py:10](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/config.py#L10)

边界：SEC ticker map 是当前上市池；退市覆盖与对照全集存在存活偏差边界。

### d03 · PIT 财务重建

状态：已实现 · Python

**输入**

- ticker、as-of T、可选 companyfacts JSON

**内部主要逻辑**

1. 合并多个 GAAP 标签以应对 tag drift；只接受 filed ≤ T 的已披露观测。
2. 按财务期取当时最新披露；duration 过滤季度长度，余额项目按 instant；收入缺失时尝试 IFRS 路径。
3. 组装季度收入、毛利/成本、库存、EPS、股数、现金和 OCF；可派生 gross margin。

**输出**

- Fundamentals 数据类；n_quarters、available 与季度序列

**源码证据**

- [inflection_discovery/pit/fundamentals.py:61](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/fundamentals.py#L61)
- [inflection_discovery/pit/fundamentals.py:98](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/fundamentals.py#L98)

### d04 · PIT 价格、流动性与远期收益

状态：已实现 · Python

**输入**

- ticker、T、lookback 或 forward months；yfinance 历史行情和拆股

**内部主要逻辑**

1. 取得原始历史并截到 T；对 OHLC 撤销 T 以后拆股的影响、反向调整 Volume，重建当时价格尺度。
2. 取最近 60 session 的 Close×Volume 中位数作为美元 ADV。
3. forward_return 专供评估，可读取未来；用退市登记与身份分段阻断 ticker 回收造成的虚假盈利，窗口结束前退市保留末值损失。

**输出**

- PIT OHLCV；median_dollar_adv；6/12 月价格收益或 None

**源码证据**

- [inflection_discovery/pit/prices.py:181](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/prices.py#L181)
- [inflection_discovery/pit/prices.py:124](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/prices.py#L124)
- [inflection_discovery/pit/dead_tickers.py:21](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/dead_tickers.py#L21)

### d05 · PIT 披露文档与文本

状态：已实现 · Python

**输入**

- ticker、T、forms、limit；SEC submissions / Archives 文档

**内部主要逻辑**

1. 按 filingDate ≤ T 和表单类型筛披露，并按日期倒序取最近文档。
2. 构造 EDGAR primaryDocument URL，限频下载；BeautifulSoup/lxml 去 HTML，缓存纯文本，默认截至 400000 字符。

**输出**

- 最近两份等文档元数据、纯文本；失败时空串

**源码证据**

- [inflection_discovery/pit/filing_text.py:25](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/filing_text.py#L25)
- [inflection_discovery/pit/filing_text.py:63](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/filing_text.py#L63)

边界：读取 submissions 的 recent 区块；长历史的 overflow 分页没有实现。

### d06 · 股票池与可用性判断

状态：已实现 · Python

**输入**

- 当前 SEC ticker map、随机 seed、exclude、T、最少价格行数

**内部主要逻辑**

1. 生成去除指定股票的固定 seed 随机对照池。
2. 检查 T 时点价格行数和季度财务可用性；对照全集进一步由 harness 按 ref_date 过滤并缓存。

**输出**

- all_tickers、random_control_tickers、data_available；对照 ticker 列表

**源码证据**

- [inflection_discovery/pit/universe.py:33](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/pit/universe.py#L33)
- [inflection_discovery/harness/backtest.py:24](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/backtest.py#L24)

### d07 · 共享记分卡 A/B/C/trap/D

状态：已实现 · Python

**输入**

- PIT 或明确标注当期的价格、Fundamentals、最新/上期披露文本

**内部主要逻辑**

1. A 用 3 年高点回撤及 52 周低位距离；较高点回撤 ≥30% 才过硬门。
2. B 用 YoY 增长加速度、毛利拐点、库存天数；C 先清披露套话，再比较关键词种类/频次变化；trap 检查稀释、现金 runway 与衰退。
3. D=(0.4A+0.5max(B,C)+0.1站上50日均线)×(1−0.4trap)；composite 仅作透明度指标，实际按 D 排名。

**输出**

- 0..1 的分数、A gate、evidence、price_rows、n_quarters、composite

**源码证据**

- [inflection_discovery/scorecard/score.py:258](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/scorecard/score.py#L258)
- [inflection_discovery/scorecard/taxonomy.py:10](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/scorecard/taxonomy.py#L10)

### d08 · Implementation B 代码发现引擎

状态：已实现 · Python

**输入**

- tickers、T、with_text、可注入财务 JSON

**内部主要逻辑**

1. score_one 调 compute_dimensions；两种数据都不可重建时跳过；异常返回 None。
2. score_universe 去重，A gate 且 trap_risk ≤0.70 的股票按 D 降序编号。
3. 返回全部 eligible 与 all_scored；调用方切 top_n。此层不强制 B∨C 门、不实施 ADV，也不调用辩论。

**输出**

- Candidate(engine=B)、ranked eligible、all_scored

**源码证据**

- [inflection_discovery/engine_b/pipeline.py:31](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/engine_b/pipeline.py#L31)
- [inflection_discovery/engine_b/pipeline.py:52](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/engine_b/pipeline.py#L52)

边界：技能正文的 A∧(B∨C)∧¬trap 表述与代码资格门不同，图册按当前函数实装分别标明。

### d09 · US / ADR 当期发现与财务回退

状态：已实现 · Python

**输入**

- 当期 ticker；SEC 当前可得财务；akshare 外国公司财务；yfinance 价格

**内部主要逻辑**

1. 以 today 取价格和 SEC 财务；SEC 收入季度不足 4 个时回退 live_fundamentals。
2. akshare source 解析外部报表并转为 Fundamentals；可取最新两份披露生成 C。
3. 复用记分卡，填明来源、NON-PIT 标签和 canonical symbol/market；A 门 + trap 上限后 D 排名。

**输出**

- 当期 Candidate、eligible、all_scored

**源码证据**

- [inflection_discovery/live/discover.py:23](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/live/discover.py#L23)
- [inflection_discovery/live/akshare_source.py:56](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/live/akshare_source.py#L56)

边界：仅供 live discovery；回填重述财务不能进入 PIT 回测。

### d10 · A 股当期适配与发现

状态：已实现 · Python

**输入**

- 6 位 A 股代码；akshare 后复权日线与同花顺财务指标

**内部主要逻辑**

1. 解析中文单位与百分比，整理季度收入同比、毛利率、存货周转天数。
2. 复用 score_A / score_D；A 股专用 B 与衰退陷阱；无免费叙事引擎，C=None。
3. 按代码推断交易所并转 canonical identity；A 门与 trap 上限后按 D 排名。

**输出**

- A 股 NON-PIT Candidate(symbol如600519.SH, market=CN, currency=CNY)、eligible/all_scored

**源码证据**

- [inflection_discovery/ashare/data.py:18](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/ashare/data.py#L18)
- [inflection_discovery/ashare/discover.py:78](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/ashare/discover.py#L78)

### d11 · Candidate 契约与证券身份归一

状态：已实现 · Python

**输入**

- ticker、交易所、币种、日期、engine、A/B/C/trap/D 与证据

**内部主要逻辑**

1. Candidate dataclass 以固定形状封装分数、rank、routing、thesis，可 to_dict。
2. validate 检查必要字段、engine、分数字段与 canonical symbol/market；make_routing 预填 exchange/currency/tradable_line/turnaround。
3. canonical_symbol 处理证券代码；失败时 routing 保留 canonicalization_error，避免硬崩溃。

**输出**

- 相同形状的 A/B 引擎候选；研究交接 routing；契约错误列表

**源码证据**

- [inflection_discovery/contract.py:19](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/contract.py#L19)
- [inflection_discovery/contract.py:77](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/contract.py#L77)
- [inflection_discovery/symbols.py:23](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/symbols.py#L23)

边界：PIT B 的 symbol/market 顶层字段保留默认空值，canonical identity 位于 routing；live/ashare 同时写顶层字段。

### d12 · Implementation A：LLM 发现漏斗

状态：技能契约 · 宿主 Agent 执行

**输入**

- 低预期底预筛名单、财务/披露；live 模式可加新闻和电话会

**内部主要逻辑**

1. LLM 对盈利与叙事分别判断并填 Candidate；comparison 模式只读冻结的 ≤T 资料。
2. D 排序；技能要求 ADV 约束及每个拟交接 Top-N 的必经辩论门。
3. trap/likely-trap 裁决止步；存活者携 routing+thesis 交给 analyzing-stocks；有状态目录时可保存 new-idea 记录。

**输出**

- 带可追溯证据的 A 候选；辩论裁决；研究交接与可选记录

**源码证据**

- [skills/discovering-inflections/SKILL.md:86](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/discovering-inflections/SKILL.md#L86)

边界：该技能可直接把候选交给研究控制器；用户要行动方案时由 investment-decision-workflow 统筹。

## 私有状态与晨检

### s01 · 状态目录、组合与决策记录契约

状态：技能契约 · 宿主 Agent 执行

**输入**

- --home 或 ~/.investing-home 指针；用户确认的决策与成交事实

**内部主要逻辑**

1. 仓库外存 portfolio.yaml 与 records/<SYMBOL>/YYYY-MM-DD-<mode>.md，单标的 INDEX 串起时间线。
2. 身份键为 (symbol,date,mode)；同键覆盖更新，同日 latest 优先 position-review > event-review > existing-report > new-idea > research。
3. 记录用 YAML frontmatter 承载 schema、价格、情景、立场、触发、review_by 等，Markdown 正文承载研究；related_symbols 关联不同上市线。

**输出**

- decision-record/v1、portfolio/v1、INDEX.md 与可选 source_report/action_taken

**源码证据**

- [skills/analyzing-stocks/references/decision-records.md:25](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/analyzing-stocks/references/decision-records.md#L25)
- [scripts/validate_records.py:567](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/validate_records.py#L567)

边界：这是文件型存储；本轮没有读取用户私有状态目录或把真实持仓嵌入图册。

### s02 · P0：校验、交叉链接和 reindex

状态：已实现 · Python

**输入**

- 外置状态目录的记录、portfolio.yaml 与 INDEX

**内部主要逻辑**

1. 校验 frontmatter、文件身份/目录匹配、词表、数值与日期、成组字段、情景概率、触发、action_taken、source_report 在状态目录内解析。
2. 检查组合与期权字段，INDEX 行排序/链接和 related_symbols 双向 See also。
3. --reindex 由 frontmatter 重建行、保留 historical，遇畸形索引不重写；缺文件行会说明后删除。

**输出**

- 错误诊断；退出 0/1/2；可重建 INDEX 与 See-also 链接

**源码证据**

- [scripts/validate_records.py:108](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/validate_records.py#L108)
- [scripts/validate_records.py:490](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/validate_records.py#L490)

边界：reindex 写入不是原子事务；P1/P2 不会自动先完整跑此校验器。

### s03 · P1：容错加载、latest 和扫描全集

状态：已实现 · Python

**输入**

- records/**/*.md、portfolio.yaml

**内部主要逻辑**

1. 复用 frontmatter 正则、日期/数值词表；YAML 无法解析时跳过或返回空字典。
2. 每个标的按日期和 mode priority 取最新记录。
3. universe 为记录标的 ∪ 持仓 ∪ 期权 underlying；持有但没有记录的标的进入 data_gaps。

**输出**

- latest: symbol→meta、portfolio dict、扫描 universe

**源码证据**

- [scripts/morning_check.py:126](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L126)
- [scripts/morning_check.py:161](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L161)
- [scripts/morning_check.py:182](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L182)

### s04 · P1：报价源与 provider_for

状态：已实现 · Python

**输入**

- canonical symbol；可选手动报价 YAML；--offline

**内部主要逻辑**

1. CN A 股映射 akshare 裸代码，其余市场通过 yfinance。
2. yfinance 优先 fast_info.last_price，再取 5d Close；akshare 读未复权日线末条。
3. FilePriceSource 提供人工报价；ChainSource 文件优先再 live；失败返回 None，由检查层报告缺口。

**输出**

- spot(symbol) → float 或 None；无隐式 FX 换算

**源码证据**

- [scripts/morning_check.py:42](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L42)
- [scripts/morning_check.py:79](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L79)
- [scripts/morning_check.py:67](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L67)

### s05 · P1：确定性规则与 findings

状态：已实现 · Python

**输入**

- 最新记录、spot、as_of；默认财报窗7天/复查窗14天

**内部主要逻辑**

1. 价格触发按 above ≥level / below ≤level 判断；现价跌破记录 Bear 生成 drawdown review。
2. 检查 review_by 过期/临近，next_earnings 临近；未知财报日期或缺价显式报 gap。
3. 抽取 KPI/event 触发及 monitor 交给 llm_todo；规则结果按 act/review/watch 排序。

**输出**

- {as_of, findings:[symbol,kind,urgency,detail,evidence], data_gaps, llm_todo}；JSON/Markdown

**源码证据**

- [scripts/morning_check.py:351](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L351)
- [scripts/morning_check.py:282](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L282)

### s06 · P1：现金担保 Put 指派检查

状态：已实现 · Python

**输入**

- portfolio.option_legs 中 qty<0 的 cash-secured-put；underlying 价格和记录

**内部主要逻辑**

1. 跳过过期腿；算 DTE、实值 spot≤strike、近行权价 spot≤strike×1.03 和到期≤7天。
2. 检验记录的财报日在到期前；reserve=strike×multiplier×abs(qty)，缺 multiplier 默认100。
3. 任何风险旗标出现即提醒；实值且近到期标 act，其余 watch；缺标的价入 data_gaps。

**输出**

- options_assignment findings：strike/expiry/dte/spot/reserve/各布尔证据

**源码证据**

- [scripts/morning_check.py:297](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/morning_check.py#L297)

### s07 · 晨检 Skill：LLM 事件/KPI 与简报

状态：技能契约 · 宿主 Agent 执行

**输入**

- Python JSON 的 findings、data_gaps、llm_todo

**内部主要逻辑**

1. 价格缺口用人工报价文件回跑；财报日期未知和缺 thesis 分别进入简报。
2. 对自由文本 KPI/event 做实时检索，输出 fired/not-fired/uncertain 和来源；合并紧急度简报。
3. 触发后可发起 Position Review；保存 monitoring 报告按技能约定需用户同意。

**输出**

- Act now / Review / Watch / KPI-event / Data gaps；可保存 Markdown

**源码证据**

- [skills/morning-check/SKILL.md:18](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/morning-check/SKILL.md#L18)

边界：手动运行，无内置 cron、券商同步或自动下单。

## 评分与回测

### e01 · P2：可评分记录加载与历史适配

状态：已实现 · Python

**输入**

- 所有真实记录；手动历史价或 yfinance/akshare；as_of 与 windows

**内部主要逻辑**

1. 跳过 INDEX、坏 frontmatter、非正决策价和无效日期；historical 仅在 INDEX，天然不评分。
2. 按 symbol 聚合全跨度后 prefetch；FileHistory/LiveHistory/ChainHistory 供注入、离线与人工数据优先回退。
3. close_on 在目标日及前7个自然日取最近收盘；low_high 取窗口日内范围，文件源用收盘近似范围。

**输出**

- 可评分 meta 列表；close_on / low_high 接口；每个 symbol 的缓存日线

**源码证据**

- [scripts/outcome_score.py:97](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L97)
- [scripts/outcome_score.py:340](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L340)
- [scripts/outcome_score.py:51](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L51)

边界：当前 P2 的 yfinance history 未显式固定 auto_adjust；A 股是 adjust=""。图册未把这个价格口径问题描述成已解决。

### e02 · P2：逐记录窗口评分

状态：已实现 · Python

**输入**

- meta、history、as_of；默认90/180/365个自然日窗口

**内部主要逻辑**

1. 未成熟窗口进入 pending；成熟但目标收盘缺失进入 data_gaps。
2. 算 (exit−p0)/p0；Buy/Add 看正收益，Reduce/Avoid 看负收益；Hold 看情景范围，缺情景用 ±10%。
3. 测 WFV 缺口收敛、落在 Bear/Base/Bull 的区间、窗口 high/low 是否触及价格线；不反推真实成交。

**输出**

- 逐记录 windows、pending、data_gaps；return/direction_hit/gap_closed/converged/scenario_landing/trigger_touches

**源码证据**

- [scripts/outcome_score.py:202](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L202)
- [scripts/outcome_score.py:129](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L129)

### e03 · P2：校准分桶与叙述包装

状态：已实现 · Python

**输入**

- 所有成熟记录窗口的评分结果

**内部主要逻辑**

1. 按 stance、confidence、valuation_zone、market 和 overall、每个 window 分桶。
2. 汇总 n、命中率、均值/中位收益、WFV 收敛率；n<3 标 low_n。
3. outcome-scoring Skill 调 Python 后解释统计，缺历史价可人工补；用户同意后存 scoring 报告。

**输出**

- {scored,pending,data_gaps,calibration}；JSON/Markdown；校准解释

**源码证据**

- [scripts/outcome_score.py:317](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/outcome_score.py#L317)
- [skills/outcome-scoring/SKILL.md:19](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/skills/outcome-scoring/SKILL.md#L19)

边界：仅绝对本币价格结果，无 FX、基准或分红总回报保证；不自动调整后续置信度/概率。

### e04 · 发现评估：benchmark 与时间标签

状态：已实现 · Python

**输入**

- benchmark/benchmark.csv；ticker、label、t_star/as_of、inflection_type

**内部主要逻辑**

1. 正例在 t_star−6/3/1月取点，固定 −3月作为 hit；负例/对照等取显式 as_of。
2. 同 ticker 不同日期可有相反标签；BenchmarkRow 生成待测日期。

**输出**

- BenchmarkRow 列表与 hit_date/as_of_dates

**源码证据**

- [inflection_discovery/benchmark/loader.py:24](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/benchmark/loader.py#L24)

### e05 · 发现评估：B harness、ADV 与收益统计

状态：已实现 · Python

**输入**

- 标签集、可重建对照池、top_n、with_text

**内部主要逻辑**

1. 每个样本日用 control + 目标 ticker 调 B 引擎；按 D 排序后过滤 60 session 中位美元 ADV <100万 或不可验证流动性。
2. 判目标是否进入可交易 Top-N；区分 no_data、illiquid、gate 和 rank；固定日期衡量正例 hit、负例 trap。
3. 同入场日期计算 picks 和 control 的6/12月收益；Wilson CI 报告命中/陷阱比例与 n，并保留 excluded 列表。

**输出**

- run_backtest 原始结果与 summarize 指标；区分能力诊断报告

**源码证据**

- [inflection_discovery/harness/backtest.py:50](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/backtest.py#L50)
- [inflection_discovery/harness/backtest.py:101](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/backtest.py#L101)
- [inflection_discovery/harness/metrics.py:8](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/metrics.py#L8)

边界：此实验是 discrimination probe，不能声称为普遍化准确率；对照池使用当前上市映射。

### e06 · 发现评估：A-vs-B 比较 harness

状态：已实现 · Python

**输入**

- 冻结 llm_scores.json 的 B/C/trap；同一 PIT 输入、同一控制臂

**内部主要逻辑**

1. A 候选与 B 共用 A gate/分数、价格动量与 score_D，只替换候选 B/C/trap 判断。
2. 对照组仍由 B 评分；A/B 使用同一 ADV、Top-N 和 summarize。
3. 逐 ticker/date 缓存 B 候选和 control 评分，再 run_pair 输出两组结果。

**输出**

- A/B 对照指标、分数和候选明细；比较结果 JSON

**源码证据**

- [inflection_discovery/harness/llm_backtest.py:76](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/llm_backtest.py#L76)
- [inflection_discovery/harness/llm_backtest.py:159](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/llm_backtest.py#L159)

边界：运行时读取预先整理的 LLM 分数文件，不在 Python harness 内实时调用模型；历史结果有模型记忆污染。

### e07 · 发现评估：五类 Canary

状态：已实现 · Python

**输入**

- 已知拆股、披露滞后、注入未来值、退市和 ticker 回收案例

**内部主要逻辑**

1. run_battery 顺序执行 split_adjustment、filing_lag、injected_future_value、survivorship、recycled_ticker。
2. 比较不应泄漏的输入与收益结果，输出各检查 detail；CLI 汇总失败返回非0。

**输出**

- [{name,passed,detail}]；CLI PASS/FAIL

**源码证据**

- [inflection_discovery/harness/canary.py:128](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/harness/canary.py#L128)
- [inflection_discovery/cli.py:28](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/inflection_discovery/cli.py#L28)

边界：canary 是独立入口；backtest 不会自动先执行这组检查。

### e08 · 发现评估：Holdout 抽样与复验

状态：已实现 · Python

**输入**

- 时点股票快照、n、seed；独立 holdout universe 与 LLM分数文件

**内部主要逻辑**

1. sample_holdout 去重保序，用 random.Random(seed).sample；记录源 SHA-256、seed 与生成时间。
2. run_holdout 读取独立名单/判断，构造 A/B 候选、按 D 排序并测远期结果与稳健性摘要。
3. 既有 comparison-report 披露旧 holdout 的采样与极值敏感限制；新 sampler 存在不等于旧实验已可完全复现。

**输出**

- 带 _meta 的抽样 JSON；holdout_results.json 与诊断摘要

**源码证据**

- [reports/sample_holdout.py:28](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/sample_holdout.py#L28)
- [reports/run_holdout.py:72](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/run_holdout.py#L72)
- [reports/comparison-report.md:5](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/comparison-report.md#L5)

边界：仓库报告将既有 holdout 结论标为 suggestive、not validated；本轮不重新拉行情复验。

### e09 · 静态研究报告与图表生成

状态：已实现 · Python

**输入**

- 回测/A-B/holdout 结果 JSON；基准、价格曲线、说明文本

**内部主要逻辑**

1. make_report_html / make_ab_compare 把指标与逐样本结果制成 HTML 卡片和条图。
2. make_price_curves / make_ashare_curves 生成价格曲线；make_dashboard 聚合各已有页面。
3. 输出 reports/*.html 等展示产物；不形成线上 API 或写回决策估值。

**输出**

- 自包含静态 HTML、对比表、价格 SVG/展示页

**源码证据**

- [reports/make_report_html.py:20](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/make_report_html.py#L20)
- [reports/make_ab_compare.py:27](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/make_ab_compare.py#L27)
- [reports/make_dashboard.py:21](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/reports/make_dashboard.py#L21)

## 安装、CI 与原型

### t01 · 安装器与平台适配

状态：已实现 · Python

**输入**

- codex/claude、--dest、--copy、--force、可选 skill 列表

**内部主要逻辑**

1. 默认 Codex 安装到 ~/.agents/skills、Claude 到 ~/.claude/skills。
2. 无指定列表时安装所有技能；默认符号链接，--copy 复制；已存在目标需显式 --force。
3. 平台说明给宿主调用约定；各 skills/agents/openai.yaml 提供元数据。

**输出**

- 本地可被宿主发现的技能目录；安装日志

**源码证据**

- [install/install.sh:33](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/install/install.sh#L33)
- [docs/platforms/codex.md:1](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/docs/platforms/codex.md#L1)
- [docs/platforms/claude.md:1](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/docs/platforms/claude.md#L1)

### t02 · 仓库结构校验、测试和 CI

状态：已实现 · Python

**输入**

- push main / pull_request；源码、skills 元数据、fixtures 和测试

**内部主要逻辑**

1. test job 在 Python3.9/3.11/3.12 安装 PyYAML，运行 unittest、validate_repo --profile full 与 shell 安装 e2e。
2. inflection-tests 在3.12安装数据依赖，运行 package offline subset 与 test_contract。
3. validate_repo 检查约定文件是否存在；它不验证投资结论，也不代表实时外部源可用。

**输出**

- CI job 结果、结构缺失清单、测试诊断

**源码证据**

- [.github/workflows/ci.yml:8](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/.github/workflows/ci.yml#L8)
- [scripts/validate_repo.py:92](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/scripts/validate_repo.py#L92)

边界：图册描述 CI 定义；本轮只检查图册和源码对应关系，未执行全套业务测试。

### t03 · 本地原型：Zone Board

状态：本地原型 · Git 未跟踪

**输入**

- 私有状态记录、组合与当期价格；模板和 ECharts

**内部主要逻辑**

1. export_data.py 导出展示 JSON；build.py 将数据和 ECharts 内联进模板。
2. 展示四个记录估值区，zone 使用记录值；价格/WFV 折价用于排序；持仓/期权作为徽章。
3. 仅检查本地源码与 NOTES 的用途，本轮不读取其真实 data.json 或重新构建。

**输出**

- .scratch 下的本地 Zone Board HTML 原型

**源码证据**

- 本地：`.scratch/stock-analysis-web-app/prototypes/06-zone-board/export_data.py:1`（未提交）
- 本地：`.scratch/stock-analysis-web-app/prototypes/06-zone-board/build.py:1`（未提交）

边界：原型可包含用户真实数据；本图册只展示结构，不嵌入原型 payload。

### t04 · 本地原型：Thesis Timeline

状态：本地原型 · Git 未跟踪

**输入**

- 每标的记录、INDEX historical 链、报告正文、日线与拆股、组合成本

**内部主要逻辑**

1. export_data.py 读取时间线与历史文档，拉行情，归一拆股尺度，渲染报告 HTML；复用 score_record 生成 P2 展示。
2. build.py 内联 data.json、ECharts 和模板；浏览器显示价格/情景阶梯带、决策/action节点、报告展开。
3. 该实现仍位于 .scratch，不能等同于已提交生产 Web App 或已完成计划中的 provider 抽取。

**输出**

- 本地可交互时间线原型；真实/模拟到期展示分开

**源码证据**

- 本地：`.scratch/stock-analysis-web-app/prototypes/07-thesis-timeline/export_data.py:70`（未提交）
- 本地：`.scratch/stock-analysis-web-app/prototypes/07-thesis-timeline/build.py:1`（未提交）

### t05 · Web App 设计与未闭合回路

状态：设计计划 · 未视为已实现

**输入**

- 设计/实施计划、CONSUMPTION_CHECKLIST、现有文件/评分接口

**内部主要逻辑**

1. docs/plans 中定义拟议 Web App 的数据、隐私、价格与静态交付要求。
2. 当前已提交文件没有 webapp/ 运行包；本地只有前述原型，不能把计划当已上线。
3. 定时晨检、券商同步、通知去重和结果自动校准也不属于当前手动核心的实装。

**输出**

- 方案与待实施契约；没有由本模块提供的线上服务

**源码证据**

- [docs/plans/2026-08-11-web-app-design.md:1](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/docs/plans/2026-08-11-web-app-design.md#L1)
- [docs/plans/2026-08-11-web-app-implementation.md:1](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/blob/59f227e15ec34e143fb2335b139fe3798760df41/docs/plans/2026-08-11-web-app-implementation.md#L1)

