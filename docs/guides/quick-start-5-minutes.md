# 新手 5 分钟上手版

这页只讲 4 件事：

1. 去哪里写用例
2. 写哪几个最关键的字段
3. 写完后怎么执行
4. 执行后去哪里看结果和 Bug

如果你是第一次接手项目，先看这一页就够了。需要完整说明时，再看 [usage-guide.md](/D:/work/xkool/DGXTest/docs/guides/usage-guide.md)。

## 1. 先认 3 个文件

- [test_suite_template.xlsx](/D:/work/xkool/DGXTest/excels/test_suite_template.xlsx)
  这里写测试用例、测试步骤、测试数据。
- [object_repository_template.xlsx](/D:/work/xkool/DGXTest/object_repo/object_repository_template.xlsx)
  这里写页面对象和元素定位器。
- [run_config.json](/D:/work/xkool/DGXTest/configs/run_config.json)
  这是最常用的 dry-run 配置，适合先检查 Excel 结构和报告链路。

如果你想直接参考一份已经写好的 DGX 中文示例，可以看：

- [dgx_demo_complete_example_cn.xlsx](/D:/work/xkool/DGXTest/excels/dgx_demo_complete_example_cn.xlsx)
- [dgx_demo_object_repository_cn.xlsx](/D:/work/xkool/DGXTest/object_repo/dgx_demo_object_repository_cn.xlsx)
- [dgx_demo_complete_example_cn.dryrun.json](/D:/work/xkool/DGXTest/configs/dgx_demo_complete_example_cn.dryrun.json)

## 2. 测试用例只先写 3 个 Sheet

在测试工作簿里，你先盯住这 3 个 Sheet 就行：

- `Case_Index`
  一行就是一条用例。
- `Case_Steps`
  一行就是一个步骤。
- `Test_Data`
  放变量化数据，步骤里可以写 `${变量名}`。

### `Case_Index` 最少要写什么

每条用例最少先写这些字段：

- `case_id`
  用例编号，例如 `LOGIN_001`、`DGX_001`
- `case_name`
  用例名称，写清业务含义
- `status`
  写 `active`
- `automation_flag`
  写 `Y`
- `data_set_id`
  关联 `Test_Data`

### `Case_Steps` 最少要写什么

每个步骤最少先写这些字段：

- `case_id`
- `step_no`
- `step_type`
  只能写 `action` 或 `assert`
- `action_key` 或 `assert_key`
  动作步骤填 `action_key`，断言步骤填 `assert_key`
- `page_name`
- `target`
- `target_type`
  常见写法是 `element`、`route`、`api`

最重要的规则只有 3 条：

1. `action` 步骤不要填 `assert_key`
2. `assert` 步骤不要填 `action_key`
3. 页面元素优先写对象库里的 `object_key`，不要把 XPath 直接塞进步骤里

### `Test_Data` 最少要写什么

最少保留：

- `data_set_id`
- 你步骤里要用到的变量列

例如：

```text
data_set_id        username    password
DATA_LOGIN_01      tester      123456
```

步骤里可以这样写：

- `value = ${username}`
- `value = ${password}`

## 3. 对象库只先写 2 个 Sheet

在对象库工作簿里，先看这 2 个 Sheet：

- `Page_Index`
  页面基础信息。
- `Element_Objects`
  页面元素和定位器。

`Element_Objects` 先写这几个字段就够用：

- `object_key`
  步骤里的 `target` 会引用它
- `page_name`
- `object_type`
- `locator_primary_type`
- `locator_primary_value`
- `default_wait`
- `default_timeout_sec`

建议：

- 优先用稳定定位器，例如 `id`、`name`、稳定文本
- 能写对象库就不要在步骤里直接写 XPath

## 4. 新手最常用的 2 条命令

### 先跑 dry-run

适合先确认 Excel 能不能被解析、报告能不能正常生成。

```powershell
python -m src.main --config configs/run_config.json --dry-run
```

如果你要跑刚才那份 DGX 中文示例，用这条：

```powershell
python -m src.main --config configs/dgx_demo_complete_example_cn.dryrun.json --dry-run
```

### 再跑 demo live smoke

适合在真实浏览器里回归 demo 链路。

```powershell
python -m src.main --config configs/live_run_config.example.json
```

如果你想缩短命令，也可以直接在仓库根目录执行：

```powershell
.\run.ps1
```

## 5. 跑完后去哪里看

每次执行都会在 [outputs](/D:/work/xkool/DGXTest/outputs) 下生成一个新的运行目录。

新手先看这 3 份结果：

- `run_manifest.json`
  先看这次跑了几个用例、成功几个、失败几个
- `test_report.html`
  看整体报告和步骤执行情况
- `bug_list.xlsx`
  看失败后生成的 Bug 清单

如果还要追查失败证据，再看：

- `case_results.xlsx`
  每条用例的明细结果
- `artifacts/`
  截图、DOM、console、network 等证据
- `ai_bugs/*.md`
  AI 生成的 Bug 交接文档

## 6. 新手最容易漏的检查项

执行前先快速过一遍：

1. `Case_Index.status=active`
2. `Case_Index.automation_flag=Y`
3. `Case_Steps.case_id` 和 `Case_Index.case_id` 对得上
4. `action_key` / `assert_key` 没填反
5. `target` 能在对象库里找到
6. `data_set_id` 能在 `Test_Data` 里找到

## 7. 一句话记忆

先在测试工作簿里写用例和步骤，再在对象库里补定位器，然后先跑 `dry-run`，最后去 `outputs` 看报告和 Bug。
