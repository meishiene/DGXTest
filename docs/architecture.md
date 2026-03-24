# Web 自动化测试架构总稿

## 1. 项目目标

本项目要建设一套完整的 `Web` 自动化测试体系，核心目标不是“把页面点通”，而是形成从用例管理到缺陷输出的完整闭环。

主要目标如下：

1. 使用 `Excel` 管理测试用例，降低维护门槛。
2. 支持跨环境、跨浏览器的稳定自动化执行。
3. 每轮执行后自动生成可读性强的测试报告。
4. 自动生成两类缺陷产物：
   - 面向人工管理和跟踪的 `bug Excel`
   - 面向 `AI` 和开发定位问题的结构化缺陷文档
5. 自动保留失败证据，包括截图、日志、DOM 快照、网络日志和可选视频。
6. 以统一执行结果模型作为唯一事实来源，驱动所有输出产物。

## 2. V1 范围

`V1` 建议包含以下能力：

1. 解析测试用例工作簿和对象库工作簿。
2. 执行前校验和数据合法性检查。
3. 动作关键字和断言关键字执行引擎。
4. 对象库解析和主/备用定位器机制。
5. 步骤级和用例级结果采集。
6. 失败证据采集。
7. 缺陷去重与归并。
8. 生成以下产物：
   - `run_manifest.json`
   - `test_report.html`
   - `case_results.xlsx`
   - `bug_list.xlsx`
   - `ai_bugs/*.md`

## 3. 总体架构

建议整套系统拆分为以下核心模块：

1. `excel_parser`
   - 负责解析所有 `Excel` 工作表。
2. `validator`
   - 负责字段、枚举、唯一性和跨表关联校验。
3. `object_repository`
   - 负责将 `target` 别名解析成页面对象和定位策略。
4. `execution_engine`
   - 负责执行动作和断言，并控制等待、重试等行为。
5. `artifact_collector`
   - 负责采集截图、DOM、控制台日志、网络日志和视频。
6. `result_model_builder`
   - 负责构建统一执行结果模型。
7. `bug_analyzer`
   - 负责失败归一化、`dedup_key` 生成和缺陷聚类。
8. `report_generators`
   - 负责生成测试报告、`Excel` 结果和 `AI` 缺陷文档。
9. `run_archive`
   - 负责按运行批次归档输出结果。

整体数据流如下：

`Excel + 对象库 -> 校验 -> 执行 -> 结果采集 -> 缺陷分析 -> 产物生成`

## 4. 输入设计

### 4.1 测试用例工作簿

建议包含以下 5 个工作表：

1. `Case_Index`
2. `Case_Steps`
3. `Test_Data`
4. `Run_Config`
5. `Dictionary`

### 4.2 对象库工作簿

建议包含以下 2 个工作表：

1. `Page_Index`
2. `Element_Objects`

## 5. Excel 模板设计

### 5.1 `Case_Index`

一行一条测试用例，建议字段如下：

- `case_id`
- `case_name`
- `module`
- `sub_module`
- `feature_name`
- `case_type`
- `priority`
- `test_level`
- `tags`
- `status`
- `automation_flag`
- `precondition_id`
- `preconditions`
- `postconditions`
- `data_set_id`
- `env_scope`
- `browser_scope`
- `can_parallel`
- `retry_policy`
- `owner`
- `require_login`
- `depends_on_case`
- `expected_result_summary`
- `ai_hint`
- `remark`

### 5.2 `Case_Steps`

一行一步，建议字段如下：

- `case_id`
- `step_no`
- `step_type`
- `step_name`
- `action_key`
- `assert_key`
- `page_name`
- `target`
- `target_type`
- `value`
- `value_type`
- `expected`
- `expected_type`
- `match_type`
- `wait`
- `timeout`
- `continue_on_fail`
- `screenshot_on_fail`
- `ai_locator_hint`
- `remark`

规则建议：

1. 一行只做一件事。
2. 动作步骤只填写 `action_key`。
3. 断言步骤只填写 `assert_key`。
4. `target` 优先写对象别名，不写原始 XPath。

### 5.3 `Test_Data`

建议字段如下：

- `data_set_id`
- `data_name`
- `module`
- `env`
- 业务数据列，例如 `username`、`password`、`role`
- `remark`

### 5.4 `Run_Config`

建议字段如下：

- `run_id`
- `run_scope`
- `target_env`
- `browser`
- `headless`
- `include_tags`
- `exclude_tags`
- `include_modules`
- `exclude_case_ids`
- `retry_failed_cases`
- `max_case_retry`
- `capture_video`
- `capture_har`
- `generate_bug_report`
- `generate_ai_bug_doc`
- `executor`
- `remark`

### 5.5 `Dictionary`

建议管理以下枚举：

- `case_type`
- `priority`
- `test_level`
- `status`
- `automation_flag`
- `browser`
- `wait_strategy`
- `action_key`
- `assert_key`

## 6. 关键字规范

### 6.1 动作关键字 `V1`

- `open_page`
- `refresh_page`
- `click`
- `hover`
- `scroll_to`
- `input_text`
- `clear_and_input`
- `input_password`
- `select_option`
- `check`
- `uncheck`
- `press_key`
- `upload_file`
- `wait_element`
- `wait_url`
- `switch_frame`

### 6.2 断言关键字 `V1`

- `assert_url_contains`
- `assert_url_equals`
- `assert_element_visible`
- `assert_element_hidden`
- `assert_element_enabled`
- `assert_text_equals`
- `assert_text_contains`
- `assert_value_equals`
- `assert_toast_contains`
- `assert_count_equals`
- `assert_api_called`
- `assert_api_status`

## 7. 对象库设计

### 7.1 `Page_Index`

建议字段如下：

- `page_name`
- `module`
- `sub_module`
- `route`
- `page_title`
- `load_wait_strategy`
- `load_timeout_sec`
- `frontend_hint`
- `api_group_hint`
- `status`
- `remark`

### 7.2 `Element_Objects`

建议字段如下：

- `object_key`
- `object_name`
- `page_name`
- `module`
- `sub_module`
- `object_type`
- `biz_action`
- `locator_primary_type`
- `locator_primary_value`
- `locator_backup_1_type`
- `locator_backup_1_value`
- `locator_backup_2_type`
- `locator_backup_2_value`
- `default_wait`
- `default_timeout_sec`
- `parent_object_key`
- `frame_key`
- `data_binding_key`
- `sensitive_flag`
- `ai_component_hint`
- `frontend_file_hint`
- `api_hint`
- `enabled`
- `remark`

定位策略建议：

1. 先使用主定位器。
2. 主定位器失败时尝试备用定位器。
3. 记录最终命中的定位方式，便于日志和缺陷分析。

## 8. 统一执行结果模型

建议统一输出以下顶层实体：

1. `run_info`
2. `execution_summary`
3. `case_results`
4. `step_results`
5. `artifacts`
6. `bugs`
7. `bug_case_links`
8. `generation_outputs`

建议顶层 `JSON` 结构如下：

```json
{
  "run_info": {},
  "execution_summary": {},
  "case_results": [],
  "step_results": [],
  "artifacts": [],
  "bugs": [],
  "bug_case_links": [],
  "generation_outputs": {}
}
```

### 8.1 状态枚举

用例状态：

- `PASSED`
- `FAILED`
- `BLOCKED`
- `SKIPPED`
- `NOT_RUN`

步骤状态：

- `PASSED`
- `FAILED`
- `SKIPPED`

缺陷状态：

- `NEW`
- `OPEN`
- `FIXING`
- `RESOLVED`
- `CLOSED`
- `IGNORED`

失败分类：

- `ASSERTION_FAILED`
- `ELEMENT_NOT_FOUND`
- `TIMEOUT`
- `JS_ERROR`
- `API_ERROR`
- `DATA_ERROR`
- `AUTH_ERROR`
- `ENVIRONMENT_ERROR`
- `SCRIPT_ERROR`
- `UNKNOWN`

## 9. 缺陷去重策略

### 9.1 缺陷候选过滤

仅对 `bug_candidate=true` 的失败结果进行正式缺陷归并。

默认属于产品缺陷候选的情况：

- 断言失败
- 页面交互异常
- `JS` 运行时错误
- 接口返回异常
- 业务结果不符合预期

默认不直接进入产品缺陷清单的情况：

- 自动化脚本自身异常
- 环境不可用
- 测试数据污染

### 9.2 归一化规则

生成 `dedup_key` 前建议做以下标准化处理：

1. 替换动态 `id`、时间戳、`token`。
2. 归一化 `URL` 路径并去除动态查询参数。
3. 优先使用 `object_key` 替换原始定位器。
4. 归一化接口签名。
5. 对敏感数据做脱敏。

### 9.3 `dedup_key` 模板

`V1` 推荐模板如下：

- `ui_not_found|{page_route}|{object_key}|{action_key}`
- `interaction_fail|{page_route}|{object_key}|{action_key}|{effect_signature}`
- `assert_text_fail|{page_route}|{object_key}|{assert_key}|{normalized_expected}`
- `navigation_fail|{source_route}|{action_key}|{expected_route}`
- `api_status_fail|{api_signature}|{status_code}|{business_context}`
- `auth_fail|{page_or_api}|{role}|{operation}`

### 9.4 聚类规则

1. 按 `dedup_key` 分组。
2. 每组只生成 1 条正式 `bug`。
3. 将所有受影响用例挂到该 `bug` 下。
4. 从组内选择证据最完整的一条用例作为主用例。

## 10. 输出产物设计

建议输出目录如下：

```text
outputs/
  2026-03-20_143000_run_001/
    run_manifest.json
    test_report.html
    case_results.xlsx
    bug_list.xlsx
    ai_bugs/
      BUG-0001.md
      BUG-0002.md
    artifacts/
      screenshots/
      html_snapshots/
      console_logs/
      network_logs/
      videos/
```

### 10.1 `test_report.html`

建议包含以下版块：

1. 运行头信息
2. 执行总览
3. 按模块、优先级、标签、失败分类统计
4. 失败摘要
5. 缺陷摘要
6. 用例明细和证据索引

### 10.2 `case_results.xlsx`

用于保存所有已选择用例的执行明细。

### 10.3 `bug_list.xlsx`

建议包含以下工作表：

1. `Bug_Summary`
2. `Bug_Case_Map`
3. `Bug_Stats`

### 10.4 `AI bug` 文档

建议一条缺陷一份 `Markdown` 文档，固定结构包括：

1. 基本信息
2. 关联用例
3. 复现步骤
4. 预期结果
5. 实际结果
6. 失败位置
7. 技术证据
8. 接口观察
9. 疑似根因
10. 疑似代码位置
11. 影响范围和去重信息
12. 面向 `AI` 的修复提示

## 11. 目录结构建议

```text
project/
  configs/
  excels/
  object_repo/
  outputs/
  src/
    core/
    parser/
    validator/
    runner/
    actions/
    asserts/
    objects/
    waits/
    artifacts/
    results/
    bugs/
    reports/
    utils/
  templates/
  logs/
  tests/
```

## 12. 执行流程

建议整轮执行流程如下：

1. 读取 `Run_Config`
2. 加载测试工作簿和对象库工作簿
3. 完成字段、枚举、关联和唯一性校验
4. 根据过滤条件筛选可执行用例
5. 执行用例并采集步骤级证据
6. 构建统一执行结果模型
7. 对失败结果做缺陷归并
8. 生成测试报告和两类缺陷产物
9. 将所有结果归档到本次运行目录

## 13. 版本规划

### 13.1 `V1`

1. `Excel` 和对象库解析
2. 输入校验
3. 动作/断言关键字执行
4. 失败证据采集
5. 统一结果模型
6. 缺陷去重归并
7. 报告和缺陷产物生成

### 13.2 `V2`

1. 并行执行
2. 历史趋势对比
3. `CI` 集成和定时执行
4. 消息通知
5. 缺陷状态回流

### 13.3 `V3`

1. 更深度的 `AI` 根因分析
2. 自动修复建议
3. 自动同步缺陷生命周期

## 14. 治理与质量门禁

执行前门禁：

1. 必填字段完整
2. 枚举值合法
3. 跨表引用有效
4. 用例和步骤主键唯一
5. 对象别名可解析

执行后门禁：

1. 必要产物必须生成成功
2. 每条正式缺陷都有对应 `AI bug` 文档
3. 所有失败用例都能关联证据文件
4. `manifest` 引用完整且路径有效

## 15. 最终建议

正式写代码前，建议先冻结以下标准：

1. `Excel` 模板和字典
2. 对象库字段和命名规范
3. `V1` 动作/断言关键字集合
4. 统一结果模型结构
5. `dedup_key` 模板和归一化规则

这些基础协议一旦定下来，后续实现会稳定很多，报告和缺陷产物也不会频繁返工。
