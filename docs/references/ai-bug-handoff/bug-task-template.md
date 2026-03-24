# Bug 任务模板

下面这个模板用于把一次自动化失败整理成可继续执行的 Bug 任务。建议保留英文主键，并在后面补中文说明，方便 AI、开发和测试共同接手。

## 基本信息

- `bug_id`：
  Bug 唯一编号，建议可回链到 `bug_list.xlsx`。
- `title`：
  一句话描述业务影响，不只写“断言失败”。
- `run_id`：
  对应哪一轮执行。
- `case_id`：
  失败用例编号。
- `case_name`：
  失败用例名称。
- `module`：
  所属模块。
- `severity`：
  严重程度，例如 `S1` / `S2` / `S3`。
- `priority`：
  优先级，例如 `P1` / `P2`。
- `owner`：
  当前建议接手人或接手角色，可为空。

## 问题摘要

- `summary`：
  用中文简要概括这个 Bug 对业务造成了什么影响。
- `user_impact`：
  如果是线上或正式环境问题，说明用户会看到什么异常。
- `scope`：
  说明影响范围，是单页、单功能还是整个流程。

## 复现路径

建议使用“前置条件 -> 操作步骤 -> 实际现象”的顺序描述：

1. 前置条件：
2. 操作步骤：
3. 实际现象：

## 失败现场

- `failed_step_no`：
  失败步骤号。
- `failed_step_name`：
  失败步骤名称。
- `page_name`：
  所在页面对象。
- `target`：
  失败目标元素、对象 key 或接口 key。
- `action_or_assert`：
  对应的 `action_key` 或 `assert_key`。
- `failure_type`：
  建议使用固定分类，例如 `ASSERTION_FAILED`、`LOCATOR_MISSING`、`JS_ERROR`。
- `failure_message`：
  原始失败消息，尽量保留关键信息。

## 预期与实际

- `expected_result`：
  预期应该出现什么结果。
- `actual_result`：
  实际发生了什么。
- `comparison_note`：
  如果预期和实际差异不明显，这里补一句中文解释。
- `first_bad_signal`：
  最先暴露异常的信号，比如按钮缺失、接口 500、文本不一致。
- `suspected_layer`：
  初步怀疑层级，例如前端、接口、配置、对象库。

## 证据清单

- `screenshot_path`：
  失败截图路径。
- `html_path`：
  失败页面 HTML 或 DOM 快照路径。
- `console_log_path`：
  控制台日志路径。
- `network_log_path`：
  网络日志路径。
- `extra_artifacts`：
  其他补充证据，例如 trace、录像、接口响应样本。

## 可能原因

- `root_cause_hypothesis`：
  当前最可能的原因。
- `why_this_hypothesis`：
  为什么会怀疑这个方向。
- `need_manual_check`：
  是否需要人工确认，若需要说明原因。
- `related_change`：
  若怀疑与近期变更有关，补充关联 PR、提交或需求编号。

## 修改边界

- `change_scope`：
  允许修改的范围。
- `do_not_change`：
  不允许顺手改动的范围。
- `validation_expectation`：
  修复后至少需要通过哪些校验或回归。

## 建议动作

- `recommended_fix_direction`：
  推荐优先尝试的修复方向。
- `recommended_tests`：
  修复后建议补跑哪些测试。
- `rollback_or_fallback`：
  如果暂时无法修复，有没有兜底方案。

## 交接备注

- `handoff_note`：
  给下一个接手人的补充说明。
- `linked_bug_ids`：
  相关 Bug 编号列表，如有。
- `linked_docs`：
  相关文档、场景说明、报告链接。

## 示例提醒

写任务单时尽量避免下面这些常见问题：

- 只贴报错，不解释业务影响。
- 只有截图，没有步骤和预期。
- 写了“可能是前端问题”，但没有任何判断依据。
- 修改边界为空，导致后续修复范围失控。
