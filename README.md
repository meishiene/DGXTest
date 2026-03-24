# DGX Web 自动化测试骨架

这是一个基于 `Playwright + Python` 的 Web 自动化测试框架，当前默认围绕 DGX demo 场景构建和验证。

## 快速开始

### 1. 安装依赖

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .[dev]
python -m playwright install chromium
```

### 2. 配置边界

当前仓库内置三份运行配置，职责已经分开：

- `configs/run_config.json`
  - 默认 CLI 配置
  - 用于 DGX demo 的 `dry-run` 演练和产物联调
  - 保留 `demo_failure=true`，方便验证失败报告链路
- `configs/live_run_config.example.json`
  - 用于 DGX demo 的真实 live smoke
  - 仅建议对 demo 环境执行，不作为正式环境模板
- `configs/prod_run_config.json`
  - 用于正式环境 live 运行模板
  - `base_url` 是占位值，执行前必须替换成真实生产域名或受控正式地址
  - 默认开启 `console` 和 `network` 采集，便于正式问题留证

### 3. 运行 demo dry-run

```powershell
python -m src.main --config configs/run_config.json --dry-run
```

也可以直接省略 `--config`，CLI 默认读取 `configs/run_config.json`。

### 4. 运行 demo live 示例

```powershell
python -m src.main --config configs/live_run_config.example.json
```

也可以直接用根目录脚本缩短命令：

```powershell
.\run.ps1
```

如果要切回 dry-run 或指定其他配置，也可以这样用：

```powershell
.\run.ps1 -Config configs/run_config.json -DryRun
```

### 5. 运行正式环境模板

执行前先确认：

1. `configs/prod_run_config.json` 中的 `base_url` 已替换为真实地址
2. 当前 Excel 用例和对象库允许访问正式环境
3. 执行窗口和账号权限符合正式环境要求

```powershell
python -m src.main --config configs/prod_run_config.json
```

## 推荐使用场景

- 想验证框架链路、失败报告、AI bug 产物：用 `configs/run_config.json`
- 想回归 DGX demo 真实链路：用 `configs/live_run_config.example.json`
- 想接正式环境 smoke：复制或直接编辑 `configs/prod_run_config.json` 后执行

## 产物

每次运行会在 `outputs/` 下生成一轮执行目录，默认包含：

- `run_manifest.json`
- `test_report.html`
- `case_results.xlsx`
- `bug_list.xlsx`
- `ai_bugs/*.md`
- `artifacts/*`

## 文档入口

项目文档已统一放到 `docs/` 下，建议按以下顺序阅读：

1. `docs/guides/quick-start-5-minutes.md`
2. `docs/guides/usage-guide.md`
3. `docs/development-plan.md`
4. `docs/status/handoff.md`
5. `docs/guides/development-guidelines.md`
6. `docs/architecture.md`
7. `docs/README.md`

## 当前默认 demo

- `https://dgx.xlook.ai/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2`

当前模板与对象库已切换到该 demo，默认 smoke 回归基于这条链路。
