# 开发计划

本文档用于记录当前项目的阶段目标、已完成事项、当前推进点和后续接手建议。
新的开发者或 AI 接手时，应先阅读本文档，再阅读 `docs/status/handoff.md` 和 `docs/status/handoff.json`。

## 项目目标

围绕 DGX demo / live 场景，完成一个基于 `Playwright + Python` 的 Web 自动化测试框架 V1 闭环，包括：

- Excel 用例解析
- 对象库映射
- dry-run / live-run 执行
- 统一结果模型
- 缺陷归并与 AI bug 交接产物
- HTML / Excel / Markdown 报告输出

## 当前阶段

- 主阶段：`P2`
- 最新完成任务：`P2-1 正式运行配置与执行入口安全收口`
- 当前关注点：
  1. 保持 `P1-3` 输出契约稳定
  2. 在正式运行前继续使用显式配置和受控 smoke 验证
  3. 每次推进后同步更新交接文档

## 阶段状态

### P0-1 模板与基础框架

- 状态：`DONE`

### P0-2 live 失败证据链补齐

- 状态：`DONE`

### P0-3 正式运行配置收口

- 状态：`DONE`

### P1-1 动作关键字补齐

- 状态：`DONE`
- 已完成：`hover`、`press_key`、`wait_url`

### P1-2 断言关键字补齐

- 状态：`DONE`
- 已完成：`assert_element_enabled`、`assert_count_equals`、`assert_api_called`、`assert_api_status`

### P1-3 报告与输出增强

- 状态：`DONE`
- 已完成：
  - `test_report.html` 执行总览与聚合统计
  - `case_results.xlsx` richer 字段与 `Case_Stats`
  - `bug_list.xlsx` richer 字段与 `Bug_Stats`

### P2-1 正式运行配置与执行入口安全收口

- 状态：`DONE`
- 已完成：
  - `base_url` 基础格式校验
  - 非 `dry_run` 时拦截占位 live host
  - `test_workbook_path` / `object_repository_path` 存在性校验
  - 正式运行配置必须显式填写 `test_workbook_path` / `object_repository_path`
  - 配置加载阶段拦截未知字段和非对象顶层 JSON
  - `base_url` 必须是站点根地址，禁止携带业务路径 / query / fragment
  - 正式运行时禁止 `demo_failure=true`
  - `output_root` 不能指向文件
  - CLI 入口补充用户友好的中文报错和非零退出码
  - `live_run_config.example.json` / `prod_run_config.json` 显式补齐工作簿路径
  - 配置与入口测试补齐

## 最近验证

- 验证命令：`python -m pytest -q`
- 验证结果：`56 passed`

## 接手建议

1. 先读 `docs/development-plan.md`
2. 再读 `docs/status/handoff.md`
3. 如需结构化状态，再读 `docs/status/handoff.json`
4. 开工前阅读 `docs/guides/development-guidelines.md`
5. 如果要进入真实环境，优先使用显式 live / prod 配置做一次受控 smoke 验证

## 变更记录

- `2026-03-23`
  - 完成 `P0-1` 模板与基础框架
  - 完成 `P0-2` live 失败证据链补齐
  - 完成 `P0-3` 正式运行配置收口
  - 完成 `P1-1` 动作关键字补齐
  - 完成 `P1-2` 断言关键字补齐
  - 完成 `P1-3` 报告与 richer Excel 输出
  - 启动 `P2-1` 并落地第一轮正式运行配置安全护栏
- `2026-03-24`
  - 完成 `P2-1` 正式运行配置与执行入口安全收口
  - 补齐配置加载层、配置校验层、CLI 入口层的正式运行保护
  - 新增入口友好报错测试，回归通过 `56 passed`
