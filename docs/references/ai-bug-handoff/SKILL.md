---
name: ai-bug-handoff
description: Generate and review bug outputs that must be accurate, evidence-backed, and immediately actionable for any AI agent or developer to take ownership and modify code. Use when producing bug reports, AI bug handoff documents, bug task lists, fix-ready issue descriptions, or any output under outputs/ that must support precise implementation handoff.
---

# AI Bug Handoff

## 目标

这个技能用于约束项目中的缺陷输出，确保生成的 `bug Excel`、`AI bug` 文档和相关 handoff 内容都具备足够证据、明确边界，并且能被下一个 AI 或开发者直接接手。

如果一个 bug 输出只能描述现象、不能指导修复，就不符合这个技能的要求。

## 使用场景

当你需要输出以下任意内容时，应遵循本技能：

1. `bug_list.xlsx` 的缺陷记录
2. `outputs/ai_bugs/*.md` 的修复交接文档
3. 给 AI 或开发者的 fix-ready issue 描述
4. 带证据链的缺陷总结
5. 需要明确修改范围的 bug 任务
6. 需要支持下一位执行者直接上手的 handoff 文档

## 基本原则

所有 bug 输出都必须满足以下要求：

1. 明确说明到底失败了什么
2. 明确说明预期结果是什么
3. 明确说明证据在哪里
4. 明确说明怀疑的影响层和定位线索
5. 明确说明允许修改什么、不允许修改什么

如果缺少这些信息，下一位执行者就无法高效接手。

## 必须覆盖的字段

每个 bug handoff 至少应覆盖以下字段：

- `bug_id`
- `title`
- `run_id`
- `case_id`
- `case_name`
- `module`
- `sub_module`
- `page_name`
- `page_url`
- `failed_step_no`
- `failed_step_name`
- `target`
- `locator_type`
- `locator_value`
- `expected_result`
- `actual_result`
- `failure_category`
- `failure_message`
- `suspected_layer`
- `evidence_paths`
- `suspected_files`
- `change_scope`
- `do_not_change`
- `verification_steps`
- `done_definition`

字段可以根据载体格式做轻微调整，但信息本身不能缺失。

## 证据要求

每个 bug 输出至少应尽量提供以下证据中的一部分：

1. 截图
2. DOM 快照
3. 控制台日志
4. 网络日志
5. 视频或其他复现证据

没有证据的 bug 输出只能算线索，不能算可直接接手的修复任务。

## 修改边界

必须明确说明修改边界，至少包含以下两个部分。

### `change_scope`

这里写允许修改的范围，例如：

- 哪个模块可以改
- 哪些对象库可以调
- 哪些模板步骤可以改
- 哪些执行器逻辑可以改

### `do_not_change`

这里写不允许顺手改动的范围，例如：

- 无关业务流程
- 无关页面
- 无关测试数据
- 无关模板结构

## 验证要求

每个 bug 输出必须给出可执行的验证步骤，例如：

1. 运行哪条命令
2. 打开哪个页面
3. 观察哪个元素或结果
4. 通过什么现象确认修复成功

## 完成定义

完成定义必须可判断，至少应覆盖：

1. 缺陷现象消失
2. 相关用例通过
3. 证据链更新
4. 没有引入明显回归

## 输出格式建议

推荐的输出结构如下：

1. 基本信息
2. 失败摘要
3. 复现路径
4. 失败位置
5. 预期与实际
6. 证据列表
7. 定位线索
8. 修改边界
9. 验证步骤
10. 完成定义

## 参考文件

本技能配套参考文件如下：

- `references/output-contract.md`
  用于约束 bug 输出必须包含哪些信息
- `references/bug-task-template.md`
  用于生成单个 bug 交接文档模板
