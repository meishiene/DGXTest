from __future__ import annotations

from html import escape
from pathlib import Path

from openpyxl import Workbook

from src.core.bootstrap import RunContext
from src.results.models import (
    AppConfig,
    ArtifactRecord,
    BugCaseLink,
    BugRecord,
    CaseResult,
    GenerationOutputs,
    RunInfo,
    StepResult,
)


def generate_output_artifacts(
    config: AppConfig,
    run_context: RunContext,
    run_info: RunInfo,
    case_results: list[CaseResult],
    step_results: list[StepResult],
    artifacts: list[ArtifactRecord],
    bugs: list[BugRecord],
    bug_case_links: list[BugCaseLink],
) -> GenerationOutputs:
    report_path = run_context.root_dir / "test_report.html"
    case_excel_path = run_context.root_dir / "case_results.xlsx"
    bug_excel_path = run_context.root_dir / "bug_list.xlsx"

    _write_test_report(report_path, run_info, case_results, bugs)
    _write_case_results_excel(case_excel_path, case_results, step_results)
    _write_ai_bug_docs(run_context.ai_bugs_dir, bugs, case_results, step_results, artifacts)
    _write_bug_excel(bug_excel_path, bugs, bug_case_links)

    return GenerationOutputs(
        manifest_path=str(run_context.manifest_path),
        test_report_html=str(report_path),
        case_results_excel=str(case_excel_path),
        bug_list_excel=str(bug_excel_path),
        ai_bug_docs_dir=str(run_context.ai_bugs_dir),
        artifacts_dir=str(run_context.artifacts_dir),
    )


def _write_test_report(
    report_path: Path,
    run_info: RunInfo,
    case_results: list[CaseResult],
    bugs: list[BugRecord],
) -> None:
    summary = run_info.execution_summary
    rows = []
    for item in case_results:
        rows.append(
            "<tr>"
            f"<td>{escape(item.case_id)}</td>"
            f"<td>{escape(item.case_name)}</td>"
            f"<td>{escape(item.module)}</td>"
            f"<td>{escape(item.status)}</td>"
            f"<td>{escape(item.failed_step_name)}</td>"
            f"<td>{escape(item.failure_message)}</td>"
            "</tr>"
        )

    bug_rows = []
    for bug in bugs:
        bug_rows.append(
            "<tr>"
            f"<td>{escape(bug.bug_id)}</td>"
            f"<td>{escape(bug.title)}</td>"
            f"<td>{escape(bug.root_cause_category)}</td>"
            f"<td>{bug.affected_case_count}</td>"
            "</tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <title>测试报告 - {escape(run_info.run_id)}</title>
  <style>
    body {{ font-family: \"Microsoft YaHei\", sans-serif; margin: 24px; color: #1f2937; }}
    h1, h2 {{ color: #0f172a; }}
    .cards {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
    .card {{ background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; min-width: 180px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
    th {{ background: #e2e8f0; }}
  </style>
</head>
<body>
  <h1>测试报告</h1>
  <p><strong>run_id:</strong> {escape(run_info.run_id)}</p>
  <p><strong>项目:</strong> {escape(run_info.project_name)} | <strong>套件:</strong> {escape(run_info.suite_name)} | <strong>浏览器:</strong> {escape(run_info.browser)}</p>
  <div class=\"cards\">
    <div class=\"card\"><strong>总用例</strong><div>{summary.total_cases}</div></div>
    <div class=\"card\"><strong>通过</strong><div>{summary.passed_cases}</div></div>
    <div class=\"card\"><strong>失败</strong><div>{summary.failed_cases}</div></div>
    <div class=\"card\"><strong>缺陷数</strong><div>{summary.bug_count}</div></div>
  </div>
  <h2>用例明细</h2>
  <table>
    <thead>
      <tr><th>case_id</th><th>case_name</th><th>module</th><th>status</th><th>failed_step</th><th>failure_message</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <h2>缺陷摘要</h2>
  <table>
    <thead>
      <tr><th>bug_id</th><th>title</th><th>category</th><th>affected_cases</th></tr>
    </thead>
    <tbody>
      {''.join(bug_rows)}
    </tbody>
  </table>
</body>
</html>
"""
    report_path.write_text(html, encoding="utf-8")


def _write_case_results_excel(
    excel_path: Path,
    case_results: list[CaseResult],
    step_results: list[StepResult],
) -> None:
    workbook = Workbook()
    case_sheet = workbook.active
    case_sheet.title = "Case_Results"
    case_sheet.append(
        [
            "run_id",
            "case_id",
            "case_name",
            "module",
            "sub_module",
            "priority",
            "status",
            "failed_step_no",
            "failed_step_name",
            "failure_category",
            "failure_message",
            "expected_summary",
            "actual_summary",
            "bug_id",
        ]
    )
    for item in case_results:
        case_sheet.append(
            [
                item.run_id,
                item.case_id,
                item.case_name,
                item.module,
                item.sub_module,
                item.priority,
                item.status,
                item.failed_step_no,
                item.failed_step_name,
                item.failure_category,
                item.failure_message,
                item.expected_summary,
                item.actual_summary,
                item.bug_id,
            ]
        )

    step_sheet = workbook.create_sheet("Step_Results")
    step_sheet.append(
        [
            "run_id",
            "case_id",
            "step_no",
            "step_name",
            "step_type",
            "action_key",
            "assert_key",
            "target",
            "status",
            "error_type",
            "error_message",
            "page_url",
        ]
    )
    for item in step_results:
        step_sheet.append(
            [
                item.run_id,
                item.case_id,
                item.step_no,
                item.step_name,
                item.step_type,
                item.action_key,
                item.assert_key,
                item.target,
                item.status,
                item.error_type,
                item.error_message,
                item.page_url,
            ]
        )

    workbook.save(excel_path)


def _write_bug_excel(
    excel_path: Path,
    bugs: list[BugRecord],
    bug_case_links: list[BugCaseLink],
) -> None:
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Bug_Summary"
    summary_sheet.append(
        [
            "bug_id",
            "title",
            "module",
            "sub_module",
            "severity",
            "priority",
            "status",
            "root_cause_category",
            "suspected_layer",
            "affected_case_count",
            "affected_case_ids",
            "dedup_key",
            "expected_result",
            "actual_result",
            "failed_step_no",
            "failed_step_name",
            "ai_bug_doc_path",
        ]
    )
    for bug in bugs:
        summary_sheet.append(
            [
                bug.bug_id,
                bug.title,
                bug.module,
                bug.sub_module,
                bug.severity,
                bug.priority,
                bug.status,
                bug.root_cause_category,
                bug.suspected_layer,
                bug.affected_case_count,
                ",".join(bug.affected_case_ids),
                bug.dedup_key,
                bug.expected_result,
                bug.actual_result,
                bug.failed_step_no,
                bug.failed_step_name,
                bug.ai_bug_doc_path,
            ]
        )

    case_map_sheet = workbook.create_sheet("Bug_Case_Map")
    case_map_sheet.append(
        [
            "bug_id",
            "run_id",
            "case_id",
            "case_result_id",
            "failed_step_no",
            "failed_step_name",
            "is_primary_case",
        ]
    )
    for link in bug_case_links:
        case_map_sheet.append(
            [
                link.bug_id,
                link.run_id,
                link.case_id,
                link.case_result_id,
                link.failed_step_no,
                link.failed_step_name,
                "Y" if link.is_primary_case else "N",
            ]
        )

    stats_sheet = workbook.create_sheet("Bug_Stats")
    stats_sheet.append(["metric", "value"])
    stats_sheet.append(["bug_count", len(bugs)])
    stats_sheet.append(["linked_case_count", len(bug_case_links)])

    workbook.save(excel_path)


def _write_ai_bug_docs(
    ai_bugs_dir: Path,
    bugs: list[BugRecord],
    case_results: list[CaseResult],
    step_results: list[StepResult],
    artifacts: list[ArtifactRecord],
) -> None:
    case_map = {item.case_id: item for item in case_results}
    steps_by_case: dict[str, list[StepResult]] = {}
    artifacts_by_case: dict[str, list[ArtifactRecord]] = {}

    for step in step_results:
        steps_by_case.setdefault(step.case_id, []).append(step)
    for case_id in steps_by_case:
        steps_by_case[case_id].sort(key=lambda item: item.step_no)
    for artifact in artifacts:
        artifacts_by_case.setdefault(artifact.case_id, []).append(artifact)

    for bug in bugs:
        primary_case = case_map[bug.affected_case_ids[0]]
        case_steps = steps_by_case.get(primary_case.case_id, [])
        step = next((item for item in case_steps if item.step_no == bug.failed_step_no), None)
        case_artifacts = artifacts_by_case.get(primary_case.case_id, [])

        screenshot_path = _find_artifact_path(case_artifacts, "screenshot")
        dom_snapshot_path = _find_artifact_path(case_artifacts, "dom_snapshot")
        console_log_path = _find_artifact_path(case_artifacts, "console_log")
        network_log_path = _find_artifact_path(case_artifacts, "network_log")
        video_path = _find_artifact_path(case_artifacts, "video")
        evidence_paths = _build_artifact_lines(case_artifacts)
        suspected_files = _build_suspected_files(step)
        change_scope = _build_change_scope(step, bug)
        do_not_change = _build_do_not_change(bug)
        verification_steps = _build_verification_steps(primary_case)
        done_definition = _build_done_definition(primary_case)
        first_check, second_check, third_check = _build_task_handoff(step, bug)
        root_cause_hypothesis = _build_root_cause_hypothesis(primary_case, step, bug)
        issue_judgement = _build_issue_judgement(primary_case)
        repro_steps = _build_repro_steps(case_steps)
        contract_path = "outputs/ai-bug-handoff/references/output-contract.md"
        template_path = "outputs/ai-bug-handoff/references/bug-task-template.md"

        doc_path = ai_bugs_dir / f"{bug.bug_id}.md"
        bug.ai_bug_doc_path = str(doc_path)
        content = f"""# {bug.bug_id} {bug.title}

## 1. 基本信息
- bug_id: {bug.bug_id}
- title: {bug.title}
- run_id: {bug.run_id}
- case_id: {primary_case.case_id}
- case_name: {primary_case.case_name}
- module: {bug.module}
- sub_module: {bug.sub_module}
- severity: {bug.severity}
- priority: {bug.priority}
- suspected_layer: {bug.suspected_layer}
- contract_reference: {contract_path}
- template_reference: {template_path}

## 2. 问题判定
- 是否为正式 bug: {"是" if primary_case.bug_candidate else "否"}
- 判定依据: {issue_judgement}
- 当前不确定点: {_build_uncertainty(bug)}

## 3. 复现路径
{repro_steps}

## 4. 失败位置
- page_name: {step.page_name if step else ""}
- page_url: {step.page_url if step else ""}
- failed_step_no: {bug.failed_step_no}
- failed_step_name: {bug.failed_step_name}
- target: {step.target if step else ""}
- locator_type: {step.locator_used_type if step else ""}
- locator_value: {step.locator_used_value if step else ""}

## 5. 预期与实际
- expected_result: {bug.expected_result}
- actual_result: {bug.actual_result}
- failure_category: {primary_case.failure_category}
- failure_message: {primary_case.failure_message}

## 6. 证据列表
- screenshot: {screenshot_path}
- dom_snapshot: {dom_snapshot_path}
- console_log: {console_log_path}
- network_log: {network_log_path}
- video: {video_path}
- evidence_paths:
{evidence_paths}

## 7. 定位线索
- suspected_files: {suspected_files}
- component_hint: {step.component_hint if step else ""}
- api_hint: {step.api_hint if step else ""}
- root_cause_hypothesis: {root_cause_hypothesis}

## 8. 任务领取说明
- first_check: {first_check}
- second_check: {second_check}
- third_check: {third_check}

## 9. 修改边界
- change_scope: {change_scope}
- do_not_change: {do_not_change}

## 10. 验证步骤
1. {verification_steps[0]}
2. {verification_steps[1]}
3. {verification_steps[2]}

## 11. 完成定义
- done_definition_1: {done_definition[0]}
- done_definition_2: {done_definition[1]}
- done_definition_3: {done_definition[2]}

## 12. 影响范围和去重信息
- affected_case_count: {bug.affected_case_count}
- affected_case_ids: {", ".join(bug.affected_case_ids)}
- dedup_key: {bug.dedup_key}
"""
        doc_path.write_text(content, encoding="utf-8-sig")


def _build_artifact_lines(artifacts: list[ArtifactRecord]) -> str:
    if not artifacts:
        return "- 无"
    return "\n".join(f"- {artifact.artifact_type}: {artifact.file_path}" for artifact in artifacts)


def _find_artifact_path(artifacts: list[ArtifactRecord], artifact_type: str) -> str:
    for artifact in artifacts:
        if artifact.artifact_type == artifact_type:
            return artifact.file_path
    return ""


def _build_suspected_files(step: StepResult | None) -> str:
    if step is None:
        return ""
    return step.frontend_file_hint or ""


def _build_change_scope(step: StepResult | None, bug: BugRecord) -> str:
    if step is None:
        return f"仅在 {bug.module} 模块当前失败步骤直接相关的逻辑内排查和修改。"
    scope_parts: list[str] = []
    if step.page_name:
        scope_parts.append(f"{step.page_name} 页面逻辑")
    if step.target:
        scope_parts.append(f"{step.target} 对应交互或断言逻辑")
    if step.component_hint:
        scope_parts.append(f"{step.component_hint} 相关组件")
    if step.api_hint:
        scope_parts.append(f"{step.api_hint} 触发链路")
    return "；".join(scope_parts) if scope_parts else f"{bug.module} 模块内与失败步骤直接相关的逻辑"


def _build_do_not_change(bug: BugRecord) -> str:
    if bug.suspected_layer == "frontend":
        return "不要优先修改无证据指向的后端服务、数据库结构或无关业务模块。"
    if bug.suspected_layer == "backend":
        return "不要优先修改无证据指向的前端页面结构或样式逻辑。"
    return "不要优先修改与当前失败步骤无直接证据关联的模块。"


def _build_verification_steps(primary_case: CaseResult) -> list[str]:
    return [
        f"重新执行用例 {primary_case.case_id}，确认原失败步骤恢复通过。",
        f"确认用例 {primary_case.case_id} 的关键预期结果与实际结果一致。",
        "确认原错误信息不再出现，并检查没有引入明显范围外回归。",
    ]


def _build_done_definition(primary_case: CaseResult) -> list[str]:
    return [
        f"用例 {primary_case.case_id} 可以稳定通过。",
        "原关键失败日志或错误现象不再复现。",
        "修改范围内未观察到新的阻断性问题或明显副作用。",
    ]


def _build_task_handoff(step: StepResult | None, bug: BugRecord) -> tuple[str, str, str]:
    if step is None:
        return (
            "先检查失败步骤对应的代码入口。",
            "再检查当前错误信息是否有更直接的代码线索。",
            "最后补充验证步骤确保问题闭环。",
        )
    first_check = f"先检查 {step.frontend_file_hint or step.page_name or bug.module} 中与 {step.target or bug.failed_step_name} 直接相关的实现。"
    second_check = f"再检查 {step.component_hint or step.target or bug.failed_step_name} 的事件绑定、参数传递和状态更新逻辑。"
    third_check = f"最后检查 {step.api_hint or '相关接口链路'} 与页面行为是否一致，确认修改未超出当前边界。"
    return first_check, second_check, third_check


def _build_root_cause_hypothesis(
    primary_case: CaseResult,
    step: StepResult | None,
    bug: BugRecord,
) -> str:
    if step is None:
        return "当前仅能确认存在失败现象，缺少足够步骤上下文。"
    if bug.suspected_layer == "frontend":
        return f"当前更像是前端侧问题，优先检查 {step.target or '目标对象'} 的事件绑定、参数处理和页面状态更新逻辑。"
    return "当前根因仍需进一步结合日志、接口和代码上下文确认。"


def _build_issue_judgement(primary_case: CaseResult) -> str:
    if primary_case.bug_candidate:
        return "当前失败属于产品缺陷候选，且已有失败步骤、失败信息和证据文件支撑。"
    return "当前失败暂不满足正式产品缺陷判定条件。"


def _build_uncertainty(bug: BugRecord) -> str:
    if bug.suspected_layer == "frontend":
        return "当前更偏向前端问题，但仍建议在修复后结合真实链路回归确认接口与数据侧未受影响。"
    return "当前疑似层级仍需结合更多证据进一步确认。"


def _build_repro_steps(case_steps: list[StepResult]) -> str:
    if not case_steps:
        return "1. 当前缺少步骤数据，请回看执行结果。"
    return "\n".join(f"{index}. {step.step_name}" for index, step in enumerate(case_steps, start=1))
