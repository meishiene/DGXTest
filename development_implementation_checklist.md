# 开发实施清单

本文档是在《Web 自动化测试架构总稿》基础上压缩得到的可执行版本，便于直接拆分开发任务。

按你的要求，清单分为三大部分：

1. 模块任务
2. 表结构任务
3. 产物任务

---

## 1. 模块任务

## 1.1 主流程模块

1. 实现运行入口模块
   - 读取 `Run_Config`
   - 生成 `run_id`
   - 初始化输出目录
2. 实现执行总控流程
   - 解析输入
   - 校验输入
   - 筛选用例
   - 执行用例
   - 构建结果模型
   - 分析缺陷
   - 生成产物

## 1.2 解析模块

1. 实现测试工作簿解析模块
   - 解析 `Case_Index`
   - 解析 `Case_Steps`
   - 解析 `Test_Data`
   - 解析 `Run_Config`
   - 解析 `Dictionary`
2. 实现对象库工作簿解析模块
   - 解析 `Page_Index`
   - 解析 `Element_Objects`
3. 为解析错误增加行号、列号、字段名定位能力

## 1.3 校验模块

1. 实现必填字段校验
2. 实现枚举值校验
3. 实现唯一性校验
   - `case_id` 唯一
   - `case_id + step_no` 唯一
   - `object_key` 唯一
4. 实现跨表关联校验
   - `Case_Steps.case_id` 必须存在于 `Case_Index`
   - `Case_Index.data_set_id` 必须存在于 `Test_Data`
   - `Case_Steps.target` 必须能在对象库中解析
5. 实现可执行用例筛选
   - 过滤 `status`
   - 过滤 `automation_flag`
   - 过滤环境、浏览器、标签、模块

## 1.4 执行引擎模块

1. 实现用例执行器
2. 实现步骤执行器
   - 动作分发器
   - 断言分发器
3. 实现等待管理器
   - `visible`
   - `clickable`
   - `present`
   - `url_change`
   - `network_idle`
4. 实现重试策略
   - 步骤级兜底重试
   - 用例级失败重跑
5. 实现敏感值脱敏
   - 密码
   - `token`
   - 手机号等敏感信息

## 1.5 动作与断言模块

1. 实现 `V1` 动作关键字
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
2. 实现 `V1` 断言关键字
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

## 1.6 对象库模块

1. 实现对象解析器
   - 将 `target` 解析为 `object_key`
2. 实现定位策略模块
   - 优先主定位器
   - 失败后尝试备用定位器
3. 在步骤执行结果中输出对象上下文
   - 页面名
   - 对象类型
   - 实际命中的定位方式
   - 组件提示
   - 前端文件提示

## 1.7 证据采集模块

1. 实现失败截图采集
2. 实现失败时 `DOM` 快照采集
3. 实现控制台日志采集
4. 实现网络日志采集
5. 可选实现视频录制
6. 实现证据索引构建

## 1.8 结果与缺陷模块

1. 实现统一结果模型构建器
   - `run_info`
   - `execution_summary`
   - `case_results`
   - `step_results`
   - `artifacts`
2. 实现缺陷候选过滤器
3. 实现归一化工具
   - 动态 `id` 清洗
   - 时间戳清洗
   - `token` 清洗
   - `URL` 标准化
   - 接口签名标准化
4. 实现 `dedup_key` 生成器
5. 实现 `bug` 聚类器
   - 生成 `bugs`
   - 生成 `bug_case_links`
6. 实现主用例选择策略

## 1.9 报告与输出模块

1. 实现 `run_manifest.json` 写入
2. 实现 `test_report.html` 生成器
3. 实现 `case_results.xlsx` 生成器
4. 实现 `bug_list.xlsx` 生成器
5. 实现 `ai_bugs/*.md` 生成器

---

## 2. 表结构任务

本部分用于先冻结结构协议，避免编码过程中频繁返工。

## 2.1 输入表结构冻结

1. 确定 `Case_Index` 最终字段
2. 确定 `Case_Steps` 最终字段
3. 确定 `Test_Data` 最终字段
4. 确定 `Run_Config` 最终字段
5. 确定 `Dictionary` 最终字段
6. 确定 `Page_Index` 最终字段
7. 确定 `Element_Objects` 最终字段

## 2.2 校验规则表

建议单独整理一份规则表，至少包含：

1. `field_name`
2. `is_required`
3. `type`
4. `enum_source`
5. `unique_scope`
6. `reference_target`
7. `default_value`
8. `error_message_template`

## 2.3 统一结果模型表结构

明确以下实体结构：

1. `run_info`
2. `execution_summary`
3. `case_results`
4. `step_results`
5. `artifacts`
6. `bugs`
7. `bug_case_links`
8. `generation_outputs`

## 2.4 枚举字典冻结

需要提前冻结的枚举包括：

1. 用例状态
2. 步骤状态
3. 缺陷状态
4. 失败分类
5. 严重级别和优先级
6. 动作关键字
7. 断言关键字
8. 等待策略
9. 定位方式
10. 对象类型

## 2.5 去重规则表

建议补一张专门的去重规则表，至少包含：

1. `failure_category`
2. `dedup_template`
3. `required_dimensions`
4. `normalization_profile`
5. `merge_policy`
6. `confidence_strategy`

---

## 3. 产物任务

## 3.1 运行目录标准

1. 实现一轮执行一个目录
   - `outputs/<timestamp>_<run_id>/`
2. 固定子目录结构
   - `artifacts/screenshots`
   - `artifacts/html_snapshots`
   - `artifacts/console_logs`
   - `artifacts/network_logs`
   - `artifacts/videos`
   - `ai_bugs`

## 3.2 `run_manifest.json`

1. 生成统一入口文件
2. 写入所有输出产物路径
3. 增加产物有效性检查标记

## 3.3 `test_report.html`

必须包含以下内容：

1. 运行头信息和环境信息
2. 执行总览卡片
3. 按模块、优先级、标签、失败分类统计
4. 失败摘要
5. 缺陷摘要
6. 用例明细表

## 3.4 `case_results.xlsx`

1. 生成所有已选用例的执行明细
2. 包含运行信息、用例信息、状态、耗时、失败信息
3. 包含证据路径字段

## 3.5 `bug_list.xlsx`

1. 实现 `Bug_Summary`
2. 实现 `Bug_Case_Map`
3. 实现 `Bug_Stats`
4. 确保每条缺陷记录包含：
   - `dedup_key`
   - 影响用例数量
   - 影响用例编号
   - 关键证据路径
   - `AI` 文档路径

## 3.6 `AI bug` 文档

1. 每条正式缺陷生成一份 `Markdown`
2. 固定文档结构：
   - 基本信息
   - 关联用例
   - 复现步骤
   - 预期结果
   - 实际结果
   - 失败位置
   - 技术证据
   - 接口观察
   - 疑似根因
   - 疑似代码位置
   - 影响范围和去重信息
   - 修复提示
3. 确保每份文档都带有页面、对象、接口、组件、文件线索

---

## 4. 交付里程碑

## 里程碑 1：结构冻结

1. 冻结输入表结构
2. 冻结对象库结构
3. 冻结枚举和校验规则

## 里程碑 2：执行引擎最小闭环

1. 完成解析和校验
2. 完成 `V1` 动作/断言执行
3. 完成步骤和用例结果输出

## 里程碑 3：缺陷分析闭环

1. 完成候选过滤
2. 完成归一化
3. 完成 `dedup_key` 生成
4. 完成缺陷聚类

## 里程碑 4：产物闭环

1. 生成 `manifest`、测试报告、用例结果表
2. 生成 `bug Excel` 和 `AI bug` 文档
3. 校验证据路径和引用完整性

---

## 5. 验收清单

满足以下条件可视为阶段可交付：

1. 所有输入结构能通过校验
2. 至少有一轮完整执行可以跑通并生成输出目录
3. `run_manifest.json` 能正确索引全部产物
4. 所有失败用例都有对应证据
5. 去重后不会产生大量重复 `bug`
6. `AI bug` 文档具备明确的代码定位线索
