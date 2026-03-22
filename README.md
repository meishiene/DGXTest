# DGX Web 自动化测试骨架

这是一个基于 `Playwright + Python` 的 `Web` 自动化测试骨架项目，目标是承接以下能力：

1. `Excel` 管理测试用例
2. 对象库管理页面元素
3. 自动化执行
4. 统一结果模型
5. 测试报告与缺陷产物输出

## 当前状态

当前版本为可运行骨架，已包含：

1. 项目目录结构
2. 配置加载
3. 运行目录初始化
4. `dry-run` 演示执行
5. `Playwright` 实际运行入口
6. 统一结果模型
7. 基础报告与缺陷产物输出

## 推荐使用方式

### 1. 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
python -m playwright install chromium
```

### 2. 运行演示模式

```powershell
python -m src.main --config configs/run_config.json --dry-run
```

### 3. 运行真实 Playwright 模式

先修改 `configs/live_run_config.example.json`，再执行：

```powershell
python -m src.main --config configs/live_run_config.example.json
```

## 输出目录

运行后会在 `outputs/` 下生成一轮执行目录，包含：

1. `run_manifest.json`
2. `test_report.html`
3. `case_results.xlsx`
4. `bug_list.xlsx`
5. `ai_bugs/*.md`
6. `artifacts/*`

## 说明

当前骨架优先保证分层、边界和产物结构可用。  
后续可以继续在 `parser`、`validator`、`objects`、`actions`、`asserts` 等模块中逐步补齐真实业务能力。


## ????

??????????????????? `progress_handoff.md`????????????????????????????????????????


## ??????

- `progress_handoff.md` ???? AI ????????
- `progress_handoff.json` ???????????? AI ????????
