﻿# 项目接力进度文档

本文档用于保证任意 AI 或开发者在任何中断点都可以快速恢复本项目工作，不依赖历史对话。

## 1. 项目目标

当前项目目标是构建一套基于 `Playwright + Python` 的 `Web` 自动化测试框架，满足以下要求：

1. 用 `Excel` 管理测试用例。
2. 用对象库管理页面元素定位。
3. 自动执行测试步骤。
4. 自动生成测试报告。
5. 自动生成 `bug_list.xlsx`。
6. 自动生成可被任意 AI 直接领取并修复的 `AI bug` 文档。
7. 保留截图、DOM、控制台日志、网络日志等失败证据。

## 2. 当前技术选型

当前已确定技术栈如下：

- 语言：`Python 3.10`
- 自动化框架：`Playwright`
- Excel 读写：`openpyxl`
- 项目配置：`pyproject.toml`
- 测试框架：`pytest`

## 3. 当前目录结构

当前项目根目录：`D:\work\xkool\DGXTest`

关键目录说明：

- `configs/`
  运行配置文件。
- `excels/`
  测试用例模板文件。
- `object_repo/`
  对象库模板文件。
- `outputs/`
  每轮执行输出目录，以及 `ai-bug-handoff` 技能目录。
- `src/`
  核心代码。
- `tests/`
  自动化测试与回归测试。

## 4. 已完成内容

### 4.1 架构与规范文档

已完成以下文档：

- `web_test_automation_architecture_master.md`
- `development_implementation_checklist.md`
- `agent.md`

这些文档已经定义了：

- 总体架构
- Excel 模板结构
- 对象库结构
- 结果模型
- bug 去重思路
- 代码编写、注释、输出约束

### 4.2 项目骨架

已完成 Python 项目可运行骨架：

- `pyproject.toml`
- `README.md`
- `src/main.py`
- `src/core/*`
- `src/parser/*`
- `src/validator/*`
- `src/results/*`
- `src/reports/*`
- `src/runner/*`
- `src/actions/*`
- `src/asserts/*`
- `src/objects/*`
- `src/utils/*`
- `src/artifacts/*`
- `src/bugs/*`

### 4.3 Excel 模板与解析

已完成模板生成与解析：

- `excels/test_suite_template.xlsx`
- `object_repo/object_repository_template.xlsx`

已实现：

- 测试工作簿解析
- 对象库工作簿解析
- 基础校验
  - 工作表是否存在
  - `case_id` 是否重复
  - `case_id + step_no` 是否重复
  - `data_set_id` 是否存在
  - `target` 是否能在对象库中解析
  - `action_key / assert_key` 是否支持

### 4.4 执行链路

已实现第一版执行链路：

- `ObjectRepositoryResolver`
- `DataResolver`
- `ActionExecutor`
- `AssertExecutor`
- `runner` 按步骤驱动执行

当前真实已接入的动作：

- `open_page`
- `click`
- `clear_and_input`
- `input_password`
- `input_text`

当前真实已接入的断言：

- `assert_url_contains`
- `assert_text_contains`

### 4.5 报告与产物

当前已能生成：

- `run_manifest.json`
- `test_report.html`
- `case_results.xlsx`
- `bug_list.xlsx`
- `ai_bugs/*.md`
- `artifacts/*`

### 4.6 AI bug 输出约束技能

已在 `outputs/` 下创建项目内技能：

- `outputs/ai-bug-handoff/SKILL.md`
- `outputs/ai-bug-handoff/references/output-contract.md`
- `outputs/ai-bug-handoff/references/bug-task-template.md`
- `outputs/ai-bug-handoff/agents/openai.yaml`

该技能用于约束后续 `AI bug` 文档必须：

- 有证据
- 有失败步骤
- 有定位线索
- 有任务领取说明
- 有修改边界
- 有完成定义

### 4.7 AI bug 文档生成器已对齐技能约束

`src/reports/report_generator.py` 已升级，当前生成的 `AI bug` 文档已包含：

- 问题判定
- 复现路径
- 失败位置
- 预期与实际
- 证据列表
- 定位线索
- 任务领取说明
- 修改边界
- 验证步骤
- 完成定义
- contract/template 引用

## 5. 关键文件说明

### 5.1 入口与主流程

- `src/main.py`
  项目命令入口。
- `src/core/app.py`
  主流程编排。当前流程为：加载配置 -> 解析 Excel -> 校验 -> 执行 -> 缺陷归并 -> 产物输出。
- `src/core/bootstrap.py`
  初始化运行目录和输出结构。

### 5.2 配置与模型

- `src/results/models.py`
  项目统一数据模型。
- `src/parser/config_loader.py`
  读取 `run_config.json`。
- `src/validator/config_validator.py`
  运行配置校验。

### 5.3 Excel 与对象库

- `src/parser/template_generator.py`
  生成模板文件。
- `src/parser/excel_parser.py`
  解析测试工作簿和对象库。
- `src/parser/models.py`
  `CaseRecord`、`StepRecord`、`ObjectRecord` 等结构。
- `src/validator/excel_validator.py`
  解析后基础校验。

### 5.4 执行链路

- `src/runner/playwright_runner.py`
  当前执行主逻辑。
- `src/actions/executor.py`
  动作执行器。
- `src/asserts/executor.py`
  断言执行器。
- `src/objects/resolver.py`
  对象库解析器。
- `src/objects/playwright_locator.py`
  Playwright locator 构造和兜底策略。
- `src/utils/data_resolver.py`
  测试数据替换器，支持 `${username}` 这类占位符。

### 5.5 结果与输出

- `src/bugs/bug_analyzer.py`
  当前缺陷聚类逻辑。
- `src/reports/report_generator.py`
  测试报告、`Excel`、`AI bug` 文档生成器。
- `src/results/manifest_writer.py`
  `manifest` 写出逻辑。

## 6. 当前运行方式

### 6.1 dry-run

当前最稳定的运行方式：

```powershell
python -m src.main --config configs/run_config.json --dry-run
```

作用：

- 读取模板文件
- 走完整主流程
- 生成完整产物
- 不依赖真实业务站点

### 6.2 真实 Playwright 模式

配置文件：

- `configs/live_run_config.example.json`

执行方式：

```powershell
python -m src.main --config configs/live_run_config.example.json
```

注意：

当前真实模式虽然已经接上 `Playwright`，但模板默认还是登录示例，真实演示需要：

1. 提供真实可访问站点
2. 或增加本地 demo 页面
3. 或把模板改成适配 `example.com` 的可执行用例

## 7. 最近一次已验证状态

最近一次完整 dry-run 输出目录：

- `D:\work\xkool\DGXTest\outputs\2026-03-20_152042_RUN_20260320_152042`

该目录下包含：

- `run_manifest.json`
- `test_report.html`
- `case_results.xlsx`
- `bug_list.xlsx`
- `ai_bugs/BUG-0001.md`
- `artifacts/*`

## 8. 当前测试状态

最近验证通过的命令：

```powershell
python -m compileall src
python -m pytest -q tests\test_excel_parser.py tests\test_execution_support.py tests\test_ai_bug_handoff_output.py
python -m src.main --config configs/run_config.json --dry-run
```

当前已存在测试文件：

- `tests/test_excel_parser.py`
- `tests/test_execution_support.py`
- `tests/test_ai_bug_handoff_output.py`

## 9. 编码说明

为了避免在 VSCode 中看到乱码，当前已执行以下约定：

1. 主要 `Markdown` 文档统一改为 `UTF-8 with BOM`
2. `AI bug` 文档生成器已改为输出 `UTF-8 with BOM`

如果后续新增会被直接打开查看的中文 `Markdown` 文档，建议继续使用 `utf-8-sig` 写出。

## 10. 当前已知边界与问题

### 10.1 已知边界

1. 当前真实执行器只覆盖了少量 `action_key` / `assert_key`。
2. `dry-run` 仍承担主要演示职责。
3. 真实登录链路还没有接入可控 demo 页面或真实业务环境。
4. `bug_list.xlsx` 还没有完全对齐 `ai-bug-handoff` 的输出契约，当前主要是 `AI bug` 文档已对齐。

### 10.2 已知问题

1. 在 Windows 终端直接 `Get-Content` 某些中文 `Markdown` 时，可能仍看到终端层乱码。
   这是终端编码显示问题，不代表文件内容损坏。
2. `outputs/ai-bug-handoff/SKILL.md` 等技能文档在 PowerShell 直接预览时可能显示异常，但技能结构已通过校验。
3. `pytest` 命令可能指向错误 Python 环境，推荐统一使用：

```powershell
python -m pytest
```

## 11. 下一步建议优先级

### P1：让真实 Playwright 链路可完整演示

推荐方案二选一：

1. 增加一个本地 demo 登录页，完全适配当前模板与对象库。
2. 接入你的真实测试环境地址，并把模板改成能真正跑通的用例。

### P2：继续扩展执行器覆盖面

优先补充：

- `select_option`
- `wait_element`
- `assert_element_visible`
- `assert_element_hidden`
- `assert_value_equals`
- `assert_api_called`
- `assert_api_status`

### P3：升级 bug Excel

把 `bug_list.xlsx` 也升级成遵循 `ai-bug-handoff` 技能约束的格式，补齐：

- change_scope
- do_not_change
- verification_steps
- done_definition
- suspected_files

### P4：完善缺陷归并

当前 `bug_analyzer.py` 仍是较轻量版本，后续建议加强：

- `dedup_key` 归一化
- `root_signature`
- 更准确的层级推断
- 更丰富的主用例选择逻辑

## 12. 如果中断后要继续，建议按这个顺序恢复

1. 先看本文件。
2. 再看 `agent.md`，确认代码约束和分层边界。
3. 再看 `development_implementation_checklist.md`，确认当前阶段任务。
4. 再看：
   - `src/core/app.py`
   - `src/runner/playwright_runner.py`
   - `src/reports/report_generator.py`
5. 再执行一次：

```powershell
python -m pytest -q tests\test_excel_parser.py tests\test_execution_support.py tests\test_ai_bug_handoff_output.py
python -m src.main --config configs/run_config.json --dry-run
```

6. 确认最新输出目录生成成功，再继续改代码。

## 13. 恢复工作时的禁止事项

1. 不要绕开统一结果模型直接生成新格式产物。
2. 不要在 `Case_Steps` 里直接大量写 XPath。
3. 不要把 bug 任务写回成只有现象没有边界的文档。
4. 不要破坏 `agent.md` 已定义的分层边界。
5. 不要用系统默认编码随意覆盖中文 `Markdown` 文件。

## 14. 推荐的下一位 AI 起手任务模板

如果下一位 AI 要继续开发，建议直接从下面任一任务开始：

### 任务 A：补本地 demo 页面

目标：让当前模板中的登录用例在真实 `Playwright` 模式下完整跑通。

### 任务 B：扩展执行器

目标：继续实现更多 `action_key` / `assert_key`，并补对应测试。

### 任务 C：升级 bug Excel

目标：让 `bug_list.xlsx` 与 `AI bug` 文档对齐同一套 handoff 契约。

---

最后更新说明：

- 文档生成时间：2026-03-20
- 当前状态：可运行骨架已完成，模板解析已完成，步骤驱动执行器已接入，AI bug handoff 契约已接入，下一阶段重点是“真实链路演示”和“输出契约全量统一”。
