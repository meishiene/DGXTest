# 项目使用说明

本文档面向测试同学、开发同学和接手项目的 AI，重点回答三个问题：

1. 怎么写用例
2. 写完用例怎么执行
3. 执行后怎么看报告和 Bug

如果你是第一次接手项目，建议先读完本页，再回头看 `docs/README.md` 和 `README.md`。

## 1. 先认识项目里的几个关键文件

日常使用时，最常接触的是下面这些文件：

- `excels/test_suite_template.xlsx`
  测试用例工作簿，主要在这里写用例、步骤、测试数据和运行筛选条件。
- `object_repo/object_repository_template.xlsx`
  对象库工作簿，页面对象和定位器都放这里。
- `configs/run_config.json`
  默认 dry-run 配置，适合联调用例链路和报告链路。
- `configs/live_run_config.example.json`
  demo 环境真实浏览器 smoke 配置。
- `configs/prod_run_config.json`
  正式环境模板配置，执行前必须先改成真实地址。
- `outputs/`
  每次执行的结果目录，报告、Bug、证据链都在这里。

## 2. 怎么写用例

### 2.1 先写哪几个 Sheet

测试工作簿 `excels/test_suite_template.xlsx` 里，执行器要求至少有下面这些工作表：

- `Case_Index`
- `Case_Steps`
- `Test_Data`
- `Run_Config`
- `Dictionary`

对象库工作簿 `object_repo/object_repository_template.xlsx` 里，至少要有：

- `Page_Index`
- `Element_Objects`

注意：工作表可以带中文副标题，例如 `Case_Index - 用例索引`，解析器会只取英文主名。

### 2.2 `Case_Index` 怎么写

`Case_Index` 一行表示一条测试用例，最常用字段如下：

- `case_id`
  用例唯一编号，例如 `LOGIN_001`、`DGX_010`。
- `case_name`
  用例名称，建议写业务语义，不要只写“测试按钮”。
- `module` / `sub_module`
  模块和子模块，用于报告聚合。
- `priority`
  优先级，例如 `P1`、`P2`。
- `test_level`
  测试层级，例如 `smoke`。
- `tags`
  标签，多个标签用英文逗号分隔，例如 `login,smoke,prod`。
- `status`
  只会执行 `active` 的用例。
- `automation_flag`
  只会执行 `Y` 的用例。
- `data_set_id`
  关联 `Test_Data` 里的测试数据编号。
- `env_scope`
  用例允许在哪些环境跑，例如 `demo`、`prod`。
- `browser_scope`
  用例允许在哪些浏览器跑，例如 `chromium`。
- `retry_policy`
  失败重试策略，例如 `case_retry_1` 表示失败后允许重试 1 次。
- `require_login`
  是否需要登录，当前主要作为元数据。
- `depends_on_case`
  依赖的前置用例编号。若前置用例失败，当前用例会被标记为 `BLOCKED`。
- `expected_result_summary`
  这条用例最终想验证什么，建议写清楚，方便报告和 Bug 汇总。

### 2.3 `Case_Steps` 怎么写

`Case_Steps` 一行表示一个步骤。最重要的规则有 4 条：

1. `step_type` 只能写 `action` 或 `assert`。
2. `action` 步骤只填 `action_key`，不要填 `assert_key`。
3. `assert` 步骤只填 `assert_key`，不要填 `action_key`。
4. 普通页面元素优先在 `target` 写对象库里的 `object_key`，不要直接把 XPath 写进步骤。

常用字段说明：

- `case_id`
  这一步属于哪条用例。
- `step_no`
  步骤序号，同一条用例内不能重复。
- `step_name`
  步骤名称，建议写人能看懂的动作。
- `page_name`
  当前步骤所属页面，例如 `LoginPage`。
- `target`
  目标对象。大多数情况下写对象库里的 `object_key`。
- `target_type`
  常见有 `element`、`route`、`api`。
- `value`
  动作输入值，例如输入文本、按键名、上传文件路径。
- `expected`
  断言预期值。
- `match_type`
  常见有 `contains`、`equals`。
- `wait`
  等待策略，例如 `visible`、`hidden`、`dom_ready`、`networkidle`。
- `timeout`
  步骤超时，单位秒。
- `continue_on_fail`
  写 `Y` 时，该步骤失败后继续执行后续步骤。
- `screenshot_on_fail`
  写 `Y` 时，失败步骤会采集截图。

### 2.4 当前支持哪些 `action_key`

当前执行器支持这些动作关键字：

- `open_page`
- `click`
- `hover`
- `press_key`
- `clear_and_input`
- `input_password`
- `input_text`
- `check`
- `uncheck`
- `wait_element`
- `wait_url`
- `select_option`
- `upload_file`

最常见的写法示例：

```text
case_id    step_no step_type step_name                 action_key   page_name       target                    target_type value             wait      timeout
LOGIN_001  1       action    打开登录页                open_page    LoginPage       /login                    route                     dom_ready 10
LOGIN_001  2       action    输入用户名                input_text   LoginPage       username_input            element     ${username}       visible   10
LOGIN_001  3       action    输入密码                  input_password LoginPage      password_input            element     ${password}       visible   10
LOGIN_001  4       action    点击登录按钮              click        LoginPage       login_button              element                    visible   10
LOGIN_001  5       assert    断言跳转到首页            assert_url_contains HomePage     /home                     route       
```

### 2.5 当前支持哪些 `assert_key`

当前执行器支持这些断言关键字：

- `assert_url_contains`
- `assert_url_equals`
- `assert_text_contains`
- `assert_text_equals`
- `assert_element_visible`
- `assert_element_hidden`
- `assert_element_enabled`
- `assert_count_equals`
- `assert_api_called`
- `assert_api_status`
- `assert_value_equals`

常见断言示例：

```text
case_id    step_no step_type step_name           assert_key              page_name   target              target_type expected         match_type wait    timeout
LOGIN_001  5       assert    断言跳转到首页     assert_url_contains                          route       https://site/home contains          10
LOGIN_001  6       assert    断言欢迎语可见     assert_text_contains    HomePage    welcome_text        element     欢迎回来         contains   visible 10
LOGIN_001  7       assert    断言按钮可点击     assert_element_enabled  HomePage    submit_button       element                               visible 10
LOGIN_001  8       assert    断言接口返回 200   assert_api_status       HomePage    /api/login          api         200              equals           10
```

### 2.6 测试数据怎么写

`Test_Data` 用来放变量化数据。执行时支持 `${变量名}` 这种写法。

例如：

```text
data_set_id   data_name      env   username      password      expected_name
DATA_LOGIN_01 登录默认数据   demo  tester        123456        tester
```

步骤里可以这样引用：

- `value = ${username}`
- `value = ${password}`
- `expected = ${expected_name}`

### 2.7 什么时候要改对象库

如果步骤里的 `target` 是页面元素，那么这个元素必须先在 `object_repo/object_repository_template.xlsx` 里存在。

`Element_Objects` 常用字段：

- `object_key`
  步骤里引用它。
- `object_name`
  给人看的名字。
- `page_name`
  属于哪个页面。
- `object_type`
  例如 `button`、`input`、`checkbox`。
- `locator_primary_type` / `locator_primary_value`
  主定位器。
- `locator_backup_1_type` / `locator_backup_1_value`
  备用定位器。
- `default_wait`
  默认等待策略。
- `default_timeout_sec`
  默认超时。

建议：

- 优先用稳定定位，例如 `id`、`name`、稳定文本。
- 尽量不要在步骤里直接写 XPath。
- 一个新按钮、新输入框、新标签，最好先补对象库，再写用例步骤。

## 3. 写完用例怎么执行

### 3.1 执行前检查

执行前建议按这个顺序确认：

1. `Case_Index` 里的用例 `status=active` 且 `automation_flag=Y`
2. `Case_Steps` 的 `case_id`、`step_no`、`step_type`、`action_key` / `assert_key` 没填错
3. `target` 能在对象库里找到，除非它是 `route`、`url`、`api`
4. `data_set_id` 能在 `Test_Data` 里找到
5. 配置文件里的 `test_workbook_path`、`object_repository_path` 指向正确文件

### 3.2 三种常用执行方式

#### 方式 1：dry-run 联调

适合先验证 Excel 结构、结果链路、报告链路，不打开真实浏览器。

```powershell
python -m src.main --config configs/run_config.json --dry-run
```

#### 方式 2：demo live smoke

适合在 DGX demo 环境做真实浏览器回归。

```powershell
python -m src.main --config configs/live_run_config.example.json
```

#### 方式 3：正式环境受控运行

执行前必须先把 `configs/prod_run_config.json` 里的 `base_url` 改成真实地址。

```powershell
python -m src.main --config configs/prod_run_config.json
```

当前入口护栏会自动拦住这些错误：

- `base_url` 是占位地址
- `base_url` 带了业务路径、query、fragment
- 正式运行配置没有显式写 `test_workbook_path` / `object_repository_path`
- `demo_failure=true` 却想跑正式环境
- `output_root` 指向了文件而不是目录

### 3.3 用标签筛选执行

筛选逻辑主要来自工作簿 `Run_Config` 里的配置，而不是命令行参数。

当前常用配置项有：

- `target_env`
  例如 `demo`
- `include_tags`
  例如 `smoke,login`
- `retry_failed_cases`
  写 `Y` 表示允许按用例重试

如果你只想跑某一批用例，可以修改 `Run_Config` 的 `include_tags`，再执行命令。

## 4. 执行后怎么看结果

每次执行后都会在 `outputs/` 下生成一轮目录，例如：

- `outputs/2026-03-24_135653_RUN_20260324_135653/`

这个目录下最重要的文件有：

- `test_report.html`
  最适合第一眼查看整体执行情况。
- `case_results.xlsx`
  适合按用例看通过/失败/阻断情况。
- `bug_list.xlsx`
  适合按缺陷维度看失败聚类和待处理问题。
- `run_manifest.json`
  最完整的结构化结果，适合脚本或 AI 继续消费。
- `artifacts/`
  截图、DOM、控制台日志、网络日志等证据链。
- `ai_bugs/`
  如果生成了 AI Bug 文档，这里会有单 Bug 的 Markdown 任务单。

## 5. 怎么看 Bug

建议按下面顺序看：

### 5.1 先看 `test_report.html`

先确认：

- 总用例数
- 通过数 / 失败数 / 阻断数
- 是否有明显集中失败的模块

### 5.2 再看 `case_results.xlsx`

`case_results.xlsx` 更适合从“哪条用例失败了”这个角度切入。

重点看这些字段：

- `case_id`
- `case_name`
- `status`
- `failed_step_no`
- `failed_step_name`
- `failure_category`
- `failure_message`
- `actual_summary`
- `bug_id`
- `retry_count`

如果某条用例是 `BLOCKED`，通常说明它依赖的前置用例没有通过。

### 5.3 最后看 `bug_list.xlsx`

`bug_list.xlsx` 更适合从“现在到底有哪些问题要处理”这个角度看。

重点看这些字段：

- `bug_id`
- `title`
- `module` / `sub_module`
- `severity`
- `priority`
- `root_cause_category`
- `suspected_layer`
- `affected_case_ids`
- `failed_step_no`
- `failed_step_name`
- `expected_result`
- `actual_result`
- `artifact_ids`
- `ai_bug_doc_path`

你可以把它理解成“缺陷列表总表”。

### 5.4 要排查失败细节时，看 `artifacts/`

如果要真正定位问题，通常看这几类证据：

- `artifacts/screenshots/`
  看页面失败时长什么样。
- `artifacts/html_snapshots/`
  看当时 DOM 结构。
- `artifacts/console_logs/`
  看前端报错。
- `artifacts/network_logs/`
  看接口请求和响应状态。

### 5.5 要交给开发或 AI 修复时，看 `ai_bugs/`

如果这一轮生成了 AI Bug 文档，可以直接打开 `ai_bugs/*.md`。这里通常已经整理好了：

- Bug 标题
- 失败用例
- 失败步骤
- 预期结果
- 实际结果
- 证据路径
- 修复边界

## 6. 最常见的报错和排查方法

### 6.1 `Target cannot be resolved from object repository`

说明步骤里的 `target` 在对象库里找不到。

优先检查：

- `Case_Steps.target`
- `Element_Objects.object_key`
- 大小写和空格是否一致

### 6.2 `Unknown data_set_id`

说明 `Case_Index.data_set_id` 在 `Test_Data` 里没有对应行。

### 6.3 `Unsupported action_key` 或 `Unsupported assert_key`

说明你写了当前执行器还不支持的关键字。

可以先对照：

- 动作关键字见本页第 2.4 节
- 断言关键字见本页第 2.5 节

### 6.4 `base_url 必须是站点根地址`

说明你在配置里把 `base_url` 写成了带路径的网址，例如：

- 错误：`https://site/app/login`
- 正确：`https://site`

页面路径应该放在用例步骤 `open_page` 的 `target` 里。

## 7. 推荐的实际工作流

如果你是日常写新用例，建议按这个顺序做：

1. 在对象库补页面和元素。
2. 在 `Case_Index` 新增一条用例。
3. 在 `Case_Steps` 补动作和断言步骤。
4. 在 `Test_Data` 补测试数据。
5. 先跑 dry-run 看结构和报告。
6. 再跑 demo live smoke 看真实链路。
7. 失败后先看 `test_report.html`，再看 `case_results.xlsx`、`bug_list.xlsx` 和 `artifacts/`。

## 8. 相关文档

- `README.md`
- `docs/README.md`
- `docs/scenarios/dgx_demo_recorded_cases.md`
- `docs/references/ai-bug-handoff/output-contract.md`
- `docs/references/ai-bug-handoff/bug-task-template.md`
