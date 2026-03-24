# 项目交接说明

本文档用于帮助新的 AI 或开发者快速理解当前项目状态、已完成工作和下一步推进方向。

接手时建议按顺序阅读：

1. `docs/development-plan.md`
2. `docs/status/handoff.md`
3. `docs/guides/development-guidelines.md`

## 1. 项目概况

当前项目是一个基于 `Playwright + Python` 的 Web 自动化测试框架，用于支持 DGX demo / live 场景的测试执行与结果产出。

## 2. 基本信息

- Demo URL：`https://dgx.xlook.ai/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2`
- 工作目录：`D:/work/xkool/DGXTest`

## 3. 技术栈

- `Python 3.10`
- `Playwright`
- `openpyxl`
- `pytest`

## 4. 当前进度

### 4.1 已完成阶段

- `P0-1` 模板与基础框架
- `P0-2` live 失败证据链补齐
- `P0-3` 正式运行配置收口
- `P1-1` 的 `hover`、`press_key`、`wait_url`
- `P1-2` 的断言关键字补齐
- `P1-3` 报告与输出增强
- `P2-1` 正式运行配置与执行入口安全收口

### 4.2 最新推进

- 已完成正式运行入口第二轮安全护栏收口：
  - 正式运行配置必须显式填写 `test_workbook_path` / `object_repository_path`
  - 配置加载阶段拦截未知字段和非对象顶层 JSON
  - `base_url` 必须是站点根地址，禁止携带业务路径 / query / fragment
  - 正式运行时禁止 `demo_failure=true`
  - `output_root` 不能指向文件
  - CLI 入口补充用户友好的中文报错和非零退出码
  - live / prod 示例配置显式补齐工作簿路径
  - 配置与入口测试补齐

## 5. 能力概览

### 5.1 动作能力

`src/actions/executor.py` 当前已支持：

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

### 5.2 断言能力

`src/asserts/executor.py` 当前已支持：

- `assert_url_contains`
- `assert_url_equals`
- `assert_text_contains`
- `assert_text_equals`
- `assert_element_visible`
- `assert_element_hidden`
- `assert_element_enabled`
- `assert_value_equals`
- `assert_count_equals`
- `assert_api_called`
- `assert_api_status`

## 6. 最近验证

验证命令：

```powershell
python -m pytest -q
```

验证结果：

- `pytest`：`56 passed`
- 已验证正式运行配置护栏没有破坏既有执行、报告和输出链路

## 7. 关键文件

- `src/parser/config_loader.py`
- `src/validator/config_validator.py`
- `src/main.py`
- `src/asserts/executor.py`
- `src/parser/template_generator.py`
- `src/reports/report_generator.py`
- `tests/test_config_loader.py`
- `tests/test_main.py`
- `tests/test_execution_support.py`
- `tests/test_ai_bug_handoff_output.py`

## 8. 下一步建议

1. 用显式的 live / prod 配置做一次受控真实 smoke 验证
2. 如需进入下一阶段，先确认 `P2` 后续目标名称和范围
3. 在不破坏统一结果模型的前提下继续推进

## 9. 接手动作

1. 阅读 `docs/development-plan.md`
2. 阅读 `docs/status/handoff.md`
3. 阅读 `docs/guides/development-guidelines.md`
4. 优先查看 `src/parser/config_loader.py`、`src/validator/config_validator.py`、`src/main.py`
5. 开工前运行：

```powershell
python -m pytest -q
```

---

最新状态：`2026-03-24`，`P2-1` 已完成，当前正式运行配置和执行入口护栏已收口，并通过全量测试 `56 passed`。
