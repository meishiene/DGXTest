from pathlib import Path

from src.core.bootstrap import prepare_run_context
from src.reports.report_generator import generate_output_artifacts
from src.results.models import (
    AppConfig,
    ArtifactRecord,
    BugCaseLink,
    BugRecord,
    CaseResult,
    ExecutionSummary,
    RunInfo,
    StepResult,
)


def test_ai_bug_doc_matches_handoff_contract(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="contract_test",
        trigger_by="tester",
        base_url="https://example.com",
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    summary = ExecutionSummary(
        total_cases=1,
        passed_cases=0,
        failed_cases=1,
        blocked_cases=0,
        skipped_cases=0,
        not_run_cases=0,
        bug_count=1,
    )
    run_info = RunInfo(
        run_id=run_context.run_id,
        project_name=config.project_name,
        suite_name=config.suite_name,
        trigger_by=config.trigger_by,
        start_time="2026-03-20T14:00:00+08:00",
        end_time="2026-03-20T14:01:00+08:00",
        duration_sec=60,
        environment="test",
        base_url=config.base_url,
        browser=config.browser,
        headless=config.headless,
        execution_summary=summary,
    )
    case_result = CaseResult(
        case_result_id="CR_001",
        run_id=run_context.run_id,
        case_id="LOGIN_002",
        case_name="登录按钮点击异常场景",
        module="用户中心",
        sub_module="登录",
        priority="P1",
        status="FAILED",
        failure_category="JS_ERROR",
        expected_summary="点击登录按钮后应正常发起请求",
        actual_summary="点击登录按钮后无跳转且未发起请求",
        failed_step_no=4,
        failed_step_name="点击登录按钮",
        failure_message="Cannot read properties of undefined (reading 'trim')",
        bug_candidate=True,
        dedup_key="interaction_fail|/login|login_submit_button|click|no_request_sent",
        artifact_ids=["ART_001", "ART_002"],
        suspected_layer="frontend",
        bug_id="BUG-0001",
    )
    step_result = StepResult(
        step_result_id="SR_001",
        run_id=run_context.run_id,
        case_id="LOGIN_002",
        step_no=4,
        step_type="action",
        step_name="点击登录按钮",
        status="FAILED",
        action_key="click",
        target="login_submit_button",
        page_name="LoginPage",
        error_type="JS_ERROR",
        error_message="Cannot read properties of undefined (reading 'trim')",
        page_url="https://example.com/login",
        locator_used_type="testid",
        locator_used_value="login-submit",
        component_hint="LoginForm.SubmitButton",
        frontend_file_hint="src/components/auth/LoginForm.tsx",
        api_hint="POST /api/auth/login",
    )
    artifacts = [
        ArtifactRecord(
            artifact_id="ART_001",
            run_id=run_context.run_id,
            case_id="LOGIN_002",
            step_result_id="SR_001",
            artifact_type="screenshot",
            file_path=str(run_context.screenshots_dir / "LOGIN_002_failure.png"),
            description="测试截图",
        ),
        ArtifactRecord(
            artifact_id="ART_002",
            run_id=run_context.run_id,
            case_id="LOGIN_002",
            step_result_id="SR_001",
            artifact_type="dom_snapshot",
            file_path=str(run_context.html_snapshots_dir / "LOGIN_002_failure.html"),
            description="DOM 快照",
        ),
    ]
    bug = BugRecord(
        bug_id="BUG-0001",
        run_id=run_context.run_id,
        title="用户中心 - 点击登录按钮 执行失败",
        module="用户中心",
        sub_module="登录",
        severity="S2",
        priority="P1",
        status="NEW",
        root_cause_category="JS_ERROR",
        suspected_layer="frontend",
        affected_case_ids=["LOGIN_002"],
        affected_case_count=1,
        dedup_key="interaction_fail|/login|login_submit_button|click|no_request_sent",
        expected_result="点击登录按钮后应正常发起请求",
        actual_result="点击登录按钮后无跳转且未发起请求",
        failed_step_no=4,
        failed_step_name="点击登录按钮",
        artifact_ids=["ART_001", "ART_002"],
    )
    bug_link = BugCaseLink(
        bug_id="BUG-0001",
        run_id=run_context.run_id,
        case_id="LOGIN_002",
        case_result_id="CR_001",
        failed_step_no=4,
        failed_step_name="点击登录按钮",
        is_primary_case=True,
    )

    generate_output_artifacts(
        config=config,
        run_context=run_context,
        run_info=run_info,
        case_results=[case_result],
        step_results=[step_result],
        artifacts=artifacts,
        bugs=[bug],
        bug_case_links=[bug_link],
    )

    doc_path = run_context.ai_bugs_dir / "BUG-0001.md"
    content = doc_path.read_text(encoding="utf-8")

    assert "## 2. 问题判定" in content
    assert "## 8. 任务领取说明" in content
    assert "## 9. 修改边界" in content
    assert "change_scope:" in content
    assert "do_not_change:" in content
    assert "done_definition_1:" in content
    assert "contract_reference: outputs/ai-bug-handoff/references/output-contract.md" in content
