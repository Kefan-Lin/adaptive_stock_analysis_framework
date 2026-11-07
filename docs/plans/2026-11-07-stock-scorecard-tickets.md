# 股票研究打分卡 v1：已发布任务图

日期：2026-11-07（Asia/Shanghai）
状态：拆分已获用户认可，任务已发布；尚未开始实施。

父规格：[GitHub Issue #9](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/9)。
本地规格：[股票研究打分卡 v1](2026-11-07-stock-scorecard-spec.md)。

| 拆分序号 | GitHub 任务 | 交付 | Blocked by |
| --- | --- | --- | --- |
| 1 | [#10](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/10) | 完整研究生成可追溯的三层卡片 | 无 |
| 2 | [#11](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/11) | 研究卡片保存为私人不可变快照 | [#10](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/10) |
| 3 | [#12](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/12) | 局部复核、错误修正与历史变化对比 | [#11](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/11) |
| 4 | [#13](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/13) | 投资决策引用具体快照并兼容旧记录 | [#11](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/11) |
| 5 | [#14](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/14) | 行业适配及报告内容验收 | [#10](https://github.com/Kefan-Lin/adaptive_stock_analysis_framework/issues/10) |

## 执行方式

- 所有任务标记 ready-for-agent；该标签表示描述完整，不表示没有阻塞。
- 初始可执行任务只有 #10。
- #10 完成后，#11 与 #14 可并行。
- #11 完成后，#12 与 #13 可并行；#14 与这两项之间没有阻塞关系。
- 每项任务自带行为验收；全部完成后，由 implement-spec 对统一集成分支进行整体审查与修复。
- 具体需求以父规格及各任务正文为准，本文件是任务导航，不是另一份规格。

## 关联方式与核验

本次 GitHub 连接器未提供原生 sub-issue / dependency 写入接口，执行环境中的 gh 连接仍受限制。任务正文使用 Part of #9 和显式 Blocked by 记录关联，尚未建立 GitHub 原生父子/阻塞关系。implement-spec 应读取正文依赖，不能仅从原生依赖为空推断任务可执行。

发布后重新读取了全部五个任务，核对正文、标签及 open 状态；父规格 #9 的正文与状态均保持不变。

## 实施准备

当前本地设计、术语、ADR 和工程流程配置尚未提交。建立隔离 worktree 前，应将本功能所需的这些已确认材料纳入集成分支；不要将已有的无关研究报告、架构图册或其他 .scratch 内容一并提交。实际股票快照继续只进入私人 state-home，本次未读取私人研究数据或修改业务功能。
