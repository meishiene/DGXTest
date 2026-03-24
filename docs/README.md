# 文档导航

这里汇总 `DGXTest` 项目的过程文档、场景说明、Bug 交接规范和阶段交接材料，方便测试、开发、AI 协作代理统一查阅。

文档里的字段名、配置键、工作簿列名会尽量保留英文主键，旁边补充中文说明。这样既方便阅读，也能避免误改执行器依赖的关键字。

## 目录说明

- `development-plan.md`
  项目开发计划与阶段推进记录，适合先了解当前做到了哪一步、下一步准备做什么。
- `guides/quick-start-5-minutes.md`
  面向新手的一页上手版，只保留最常用的写用例、执行、看结果步骤。
- `guides/usage-guide.md`
  面向使用者的项目使用说明，重点介绍怎么写用例、怎么执行、怎么看报告和 Bug。
- `status/handoff.md`
  人类可读的阶段交接说明，重点看最近完成项、遗留风险、下一步建议。
- `status/handoff.json`
  给脚本或代理读取的结构化交接数据，适合自动化接力。
- `references/`
  规范、模板、输出约定等参考资料。
- `references/ai-bug-handoff/output-contract.md`
  AI Bug 交接的正式输出约定，明确 `case_results.xlsx`、`bug_list.xlsx`、Markdown 任务单应包含哪些字段。
- `references/ai-bug-handoff/bug-task-template.md`
  单个 Bug 任务的推荐模板，适合交给开发、测试或 AI 修复代理继续处理。
- `scenarios/`
  业务场景说明、录制路径说明、样例用例说明。
- `scenarios/dgx_demo_recorded_cases.md`
  当前 DGX demo 录制用例的中文解释，包括场景目标、关键步骤和维护注意事项。

## 建议阅读顺序

1. 如果是第一次接手，先读 `docs/guides/quick-start-5-minutes.md`。
2. 再读 `docs/guides/usage-guide.md`，掌握完整的写用例、执行和看结果方式。
3. 再读 `docs/development-plan.md`，了解当前阶段目标和已完成范围。
4. 接着读 `docs/status/handoff.md`，快速掌握最近一次交接结论。
5. 如果要维护用例模板，继续读 `docs/scenarios/dgx_demo_recorded_cases.md`。
6. 如果要接手缺陷流转或 AI 修复，重点读 `docs/references/ai-bug-handoff/output-contract.md`。
7. 如果要新建 Bug 任务单，直接参考 `docs/references/ai-bug-handoff/bug-task-template.md`。

## 文档使用原则

- 英文字段名优先用于执行和解析，中文用于解释字段含义。
- 报告、Bug、用例说明优先写业务语义，不只写技术现象。
- 如果文档里引用了 Excel 字段或 JSON 键，请保持英文主键不变。
- 如果发现执行逻辑更新了，请同步更新对应文档，避免“代码已经改了，说明还停留在旧版本”。
