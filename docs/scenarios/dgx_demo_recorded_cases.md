# DGX Demo 录制用例说明

本文整理当前基于 Playwright 录制和模板化生成的 DGX demo 样例用例，帮助维护者理解每条用例在验证什么、为什么这样录，以及后续扩展时要注意哪些点。

## 场景来源

- 目标地址：`https://dgx.xlook.ai/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2`
- 录制模板来源：`templates/dgx_demo_codegen.py`
- 录制输出参考：`outputs/recordings/dgx_demo_codegen.py`

## 当前录制用例

### DGX_001 打开 DGX demo 并进入 Set Boundaries

这个用例用于验证 demo 首页入口是否可用，以及项目工作区是否能顺利进入边界设置流程。

关键步骤：

1. 打开 DGX demo 页面。
2. 点击 `Faya Al Saadiyat` 项目入口按钮。
3. 点击项目卡片中的 `Go to Configuration`。
4. 进入工作区后点击 `Set Boundaries`。
5. 确认 `UploadPlot CAD File` 入口可见。

### DGX_002 完成边界配置主流程

这个用例用于验证边界配置流程的主链路是否可走通，包括打开上传弹窗、切换步骤、图层显隐和最终结果展示。

关键步骤：

1. 打开 DGX demo 页面。
2. 进入 `Faya Al Saadiyat` 项目工作区。
3. 点击 `Set Boundaries`。
4. 打开 `UploadPlot CAD File` 弹窗。
5. 为第一层选择 `Not Required`。
6. 为第二层选择 `Not Required`。
7. 点击 `Cancel` 关闭弹窗。
8. 点击 `Next` 进入后续步骤。
9. 切换 `Show/Hide All` 复选框。
10. 勾选单个图层复选框。
11. 再次切换 `Show/Hide All`。
12. 点击 `Done` 完成流程。
13. 确认结果区域出现 `Park Hyatt Abu Dhabi Hotel`。

### DGX_003 检查 DGX 首页入口稳定性

这个用例是一个更轻量的 smoke 检查，重点验证 DGX 首页路由和项目入口控件是否稳定可见。

关键步骤：

1. 打开 DGX demo 页面。
2. 断言当前 URL 正确。
3. 检查项目入口按钮可见。
4. 检查 `Go to Configuration` 按钮可见。

## 维护注意事项

- 当前很多定位来自录制结果，后续如果 UI 文案、层级结构或按钮顺序变化，优先检查对象库而不是直接改断言。
- 如果页面按钮文案包含图标或尾部装饰字符，建议保留稳定文本作为主定位，避免把视觉符号误写进模板。
- 如果后续把 demo 场景扩展为正式环境，请区分“录制样例”与“正式业务用例”，不要直接复用所有测试数据。
