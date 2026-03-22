from __future__ import annotations

from datetime import datetime

from src.actions.executor import ActionExecutor
from src.artifacts.collector import (
    capture_playwright_failure_artifacts,
    create_dry_run_failure_artifacts,
)
from src.asserts.executor import AssertExecutor
from src.core.bootstrap import RunContext
from src.objects.resolver import ObjectRepositoryResolver, ResolvedObject
from src.parser.models import CaseRecord, ParsedObjectRepository, ParsedTestSuite, StepRecord
from src.results.models import (
    AppConfig,
    ArtifactRecord,
    CaseResult,
    ExecutionSummary,
    RunInfo,
    StepResult,
)
from src.utils.data_resolver import DataResolver


PLACEHOLDER_ASSERTION_ACTUAL = "Assertion placeholder left empty in Excel"


def execute_run(
    config: AppConfig,
    run_context: RunContext,
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    if config.dry_run:
        return _execute_dry_run(config, run_context, suite, repository)
    return _execute_live_run(config, run_context, suite, repository)


def _build_run_info(
    config: AppConfig,
    run_context: RunContext,
    summary: ExecutionSummary,
) -> RunInfo:
    now = datetime.now().astimezone().isoformat()
    return RunInfo(
        run_id=run_context.run_id,
        project_name=config.project_name,
        suite_name=config.suite_name,
        trigger_by=config.trigger_by,
        start_time=now,
        end_time=now,
        duration_sec=0,
        environment="local",
        base_url=config.base_url,
        browser=config.browser,
        headless=config.headless,
        execution_summary=summary,
    )


def _execute_dry_run(
    config: AppConfig,
    run_context: RunContext,
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    step_results: list[StepResult] = []
    case_results: list[CaseResult] = []
    artifacts: list[ArtifactRecord] = []

    runnable_cases = _select_runnable_cases(suite.cases)
    case_steps = _group_steps_by_case(suite)
    object_map = {item.object_key: item for item in repository.objects}

    if runnable_cases:
        pass_case = runnable_cases[0]
        pass_case_steps = case_steps.get(pass_case.case_id, [])
        step_results.extend(_build_pass_step_results(run_context.run_id, pass_case.case_id, pass_case_steps, config.base_url))
        case_results.append(
            CaseResult(
                case_result_id=f"CR_{run_context.run_id}_{pass_case.case_id}",
                run_id=run_context.run_id,
                case_id=pass_case.case_id,
                case_name=pass_case.case_name,
                module=pass_case.module,
                sub_module=pass_case.sub_module,
                priority=pass_case.priority,
                status="PASSED",
                failure_category="",
                expected_summary=pass_case.expected_result_summary,
                actual_summary="dry-run mode generated a passing result for the DGX demo template",
            )
        )

    if config.demo_failure and len(runnable_cases) >= 2:
        fail_case = runnable_cases[1]
        fail_steps = case_steps.get(fail_case.case_id, [])
        fail_step = _pick_failure_step(fail_steps)
        object_record = object_map.get(fail_step.target) if fail_step else None
        step_result = StepResult(
            step_result_id=f"SR_{run_context.run_id}_{fail_case.case_id}_{fail_step.step_no:02d}",
            run_id=run_context.run_id,
            case_id=fail_case.case_id,
            step_no=fail_step.step_no,
            step_type=fail_step.step_type,
            step_name=fail_step.step_name,
            action_key=fail_step.action_key,
            assert_key=fail_step.assert_key,
            target=fail_step.target,
            page_name=fail_step.page_name,
            status="FAILED",
            error_type="JS_ERROR",
            error_message="Boundary workflow state did not update after the recorded action",
            page_url=config.base_url.rstrip("/") + "/dgx/f2b850f5-14a0-4325-b56d-cb1213f63ec2",
            locator_used_type=object_record.locator_primary_type if object_record else "",
            locator_used_value=object_record.locator_primary_value if object_record else "",
            component_hint=object_record.ai_component_hint if object_record else "",
            frontend_file_hint=object_record.frontend_file_hint if object_record else "",
            api_hint=object_record.api_hint if object_record else "",
        )
        step_results.append(step_result)
        artifacts.extend(
            create_dry_run_failure_artifacts(
                run_context=run_context,
                run_id=run_context.run_id,
                case_id=fail_case.case_id,
                step_result_id=step_result.step_result_id,
            )
        )
        case_results.append(
            CaseResult(
                case_result_id=f"CR_{run_context.run_id}_{fail_case.case_id}",
                run_id=run_context.run_id,
                case_id=fail_case.case_id,
                case_name=fail_case.case_name,
                module=fail_case.module,
                sub_module=fail_case.sub_module,
                priority=fail_case.priority,
                status="FAILED",
                failed_step_no=fail_step.step_no,
                failed_step_name=fail_step.step_name,
                failure_category="JS_ERROR",
                failure_message="Boundary workflow state did not update after the recorded action",
                expected_summary=fail_case.expected_result_summary,
                actual_summary="The DGX boundary workflow did not reflect the expected state change after the recorded interaction",
                bug_candidate=True,
                dedup_key=f"interaction_fail|/dgx-demo|{fail_step.target or 'unknown_target'}|{fail_step.action_key or fail_step.assert_key or 'unknown_action'}|state_not_updated",
                artifact_ids=[artifact.artifact_id for artifact in artifacts if artifact.case_id == fail_case.case_id],
                suspected_layer="frontend",
            )
        )

    summary = ExecutionSummary.from_case_results(case_results)
    return _build_run_info(config, run_context, summary), case_results, step_results, artifacts


def _execute_live_run(
    config: AppConfig,
    run_context: RunContext,
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    from playwright.sync_api import sync_playwright

    step_results: list[StepResult] = []
    case_results: list[CaseResult] = []
    artifacts: list[ArtifactRecord] = []

    runnable_cases = _select_runnable_cases(suite.cases)
    case_steps = _group_steps_by_case(suite)
    object_resolver = ObjectRepositoryResolver(repository)
    data_resolver = DataResolver(suite)

    with sync_playwright() as playwright:
        browser_factory = getattr(playwright, config.browser)
        browser = browser_factory.launch(headless=config.headless)
        page = browser.new_page()
        action_executor = ActionExecutor(object_resolver)
        assert_executor = AssertExecutor(object_resolver)

        try:
            for case in runnable_cases:
                case_step_list = case_steps.get(case.case_id, [])
                case_data = data_resolver.build_case_data(case)
                case_artifacts_before = len(artifacts)
                current_case_step_results: list[StepResult] = []
                case_failed = False
                failure_message = ""
                failure_category = ""
                failed_step_no = 0
                failed_step_name = ""

                for step in case_step_list:
                    step_result_id = f"SR_{run_context.run_id}_{case.case_id}_{step.step_no:02d}"
                    try:
                        if step.step_type == "action":
                            action_result = action_executor.execute(
                                page=page,
                                step=step,
                                case_data=case_data,
                                base_url=config.base_url,
                                timeout_ms=config.timeout_ms,
                            )
                            current_case_step_results.append(
                                _build_step_result(
                                    run_id=run_context.run_id,
                                    case_id=case.case_id,
                                    step=step,
                                    step_result_id=step_result_id,
                                    status="PASSED",
                                    actual=action_result.actual_value,
                                    page_url=action_result.page_url,
                                    resolved_object=action_result.resolved_object,
                                )
                            )
                            continue

                        if _is_placeholder_assert(step):
                            current_case_step_results.append(
                                _build_step_result(
                                    run_id=run_context.run_id,
                                    case_id=case.case_id,
                                    step=step,
                                    step_result_id=step_result_id,
                                    status="SKIPPED",
                                    actual=PLACEHOLDER_ASSERTION_ACTUAL,
                                    page_url=page.url,
                                    resolved_object=None,
                                )
                            )
                            continue

                        assert_result = assert_executor.execute(
                            page=page,
                            step=step,
                            case_data=case_data,
                            base_url=config.base_url,
                            timeout_ms=config.timeout_ms,
                        )
                        current_case_step_results.append(
                            _build_step_result(
                                run_id=run_context.run_id,
                                case_id=case.case_id,
                                step=step,
                                step_result_id=step_result_id,
                                status="PASSED",
                                actual=assert_result.actual_value,
                                page_url=assert_result.page_url,
                                resolved_object=assert_result.resolved_object,
                            )
                        )
                    except Exception as exc:
                        failure_message = str(exc)
                        failure_category = _categorize_failure(exc, step)
                        failed_step_no = step.step_no
                        failed_step_name = step.step_name
                        resolved_object = None
                        if step.target and object_resolver.has_object(step.target):
                            record = object_resolver.get_object(step.target)
                            resolved_object = object_resolver.build_resolved_object(
                                object_key=record.object_key,
                                locator_type=record.locator_primary_type,
                                locator_value=record.locator_primary_value,
                            )

                        current_case_step_results.append(
                            _build_step_result(
                                run_id=run_context.run_id,
                                case_id=case.case_id,
                                step=step,
                                step_result_id=step_result_id,
                                status="FAILED",
                                actual="",
                                page_url=page.url,
                                resolved_object=resolved_object,
                                error_type=failure_category,
                                error_message=failure_message,
                            )
                        )
                        artifacts.extend(
                            capture_playwright_failure_artifacts(
                                run_context=run_context,
                                run_id=run_context.run_id,
                                case_id=case.case_id,
                                step_result_id=step_result_id,
                                page=page,
                            )
                        )
                        case_failed = True
                        break

                step_results.extend(current_case_step_results)
                case_artifact_ids = [
                    artifact.artifact_id
                    for artifact in artifacts[case_artifacts_before:]
                    if artifact.case_id == case.case_id
                ]

                if case_failed:
                    case_results.append(
                        CaseResult(
                            case_result_id=f"CR_{run_context.run_id}_{case.case_id}",
                            run_id=run_context.run_id,
                            case_id=case.case_id,
                            case_name=case.case_name,
                            module=case.module,
                            sub_module=case.sub_module,
                            priority=case.priority,
                            status="FAILED",
                            failed_step_no=failed_step_no,
                            failed_step_name=failed_step_name,
                            failure_category=failure_category,
                            failure_message=failure_message,
                            expected_summary=case.expected_result_summary,
                            actual_summary=f"步骤失败: {failed_step_name}",
                            bug_candidate=_is_bug_candidate(failure_category),
                            dedup_key=_build_dedup_key(step_results[-1], failure_category),
                            artifact_ids=case_artifact_ids,
                            suspected_layer=_infer_layer(failure_category),
                        )
                    )
                else:
                    case_results.append(
                        CaseResult(
                            case_result_id=f"CR_{run_context.run_id}_{case.case_id}",
                            run_id=run_context.run_id,
                            case_id=case.case_id,
                            case_name=case.case_name,
                            module=case.module,
                            sub_module=case.sub_module,
                            priority=case.priority,
                            status="PASSED",
                            failure_category="",
                            expected_summary=case.expected_result_summary,
                            actual_summary="所有动作通过，未填写的断言占位已标记为跳过",
                        )
                    )
        finally:
            browser.close()

    summary = ExecutionSummary.from_case_results(case_results)
    return _build_run_info(config, run_context, summary), case_results, step_results, artifacts


def _select_runnable_cases(cases: list[CaseRecord]) -> list[CaseRecord]:
    return [item for item in cases if item.status == "active" and item.automation_flag == "Y"]


def _group_steps_by_case(suite: ParsedTestSuite) -> dict[str, list[StepRecord]]:
    grouped: dict[str, list[StepRecord]] = {}
    for step in suite.steps:
        grouped.setdefault(step.case_id, []).append(step)
    for case_id in grouped:
        grouped[case_id].sort(key=lambda item: item.step_no)
    return grouped


def _build_pass_step_results(
    run_id: str,
    case_id: str,
    steps: list[StepRecord],
    base_url: str,
) -> list[StepResult]:
    results: list[StepResult] = []
    for step in steps:
        results.append(
            StepResult(
                step_result_id=f"SR_{run_id}_{case_id}_{step.step_no:02d}",
                run_id=run_id,
                case_id=case_id,
                step_no=step.step_no,
                step_type=step.step_type,
                step_name=step.step_name,
                action_key=step.action_key,
                assert_key=step.assert_key,
                target=step.target,
                page_name=step.page_name,
                status="SKIPPED" if _is_placeholder_assert(step) else "PASSED",
                expected=step.expected,
                actual=PLACEHOLDER_ASSERTION_ACTUAL if _is_placeholder_assert(step) else (step.expected or "PASS"),
                page_url=base_url,
            )
        )
    return results


def _pick_failure_step(steps: list[StepRecord]) -> StepRecord:
    actionable_steps = [step for step in steps if not _is_placeholder_assert(step)]
    for preferred_target in ("done_button", "project_result_cell", "show_hide_all_checkbox"):
        for step in actionable_steps:
            if step.target == preferred_target:
                return step
    return actionable_steps[-1] if actionable_steps else steps[-1]


def _is_placeholder_assert(step: StepRecord) -> bool:
    return step.step_type == "assert" and not step.assert_key.strip()


def _build_step_result(
    run_id: str,
    case_id: str,
    step: StepRecord,
    step_result_id: str,
    status: str,
    actual: str,
    page_url: str,
    resolved_object: ResolvedObject | None,
    error_type: str = "",
    error_message: str = "",
) -> StepResult:
    return StepResult(
        step_result_id=step_result_id,
        run_id=run_id,
        case_id=case_id,
        step_no=step.step_no,
        step_type=step.step_type,
        step_name=step.step_name,
        status=status,
        action_key=step.action_key,
        assert_key=step.assert_key,
        target=step.target,
        page_name=step.page_name,
        expected=step.expected,
        actual=actual,
        error_type=error_type,
        error_message=error_message,
        page_url=page_url,
        locator_used_type=resolved_object.locator_type if resolved_object else "",
        locator_used_value=resolved_object.locator_value if resolved_object else "",
        component_hint=resolved_object.component_hint if resolved_object else "",
        frontend_file_hint=resolved_object.frontend_file_hint if resolved_object else "",
        api_hint=resolved_object.api_hint if resolved_object else "",
    )


def _categorize_failure(exc: Exception, step: StepRecord) -> str:
    if isinstance(exc, AssertionError):
        return "ASSERTION_FAILED"
    if step.step_type == "action":
        return "ACTION_FAILED"
    return "UNKNOWN"


def _is_bug_candidate(failure_category: str) -> bool:
    return failure_category in {"ASSERTION_FAILED", "ACTION_FAILED", "JS_ERROR"}


def _infer_layer(failure_category: str) -> str:
    if failure_category in {"ASSERTION_FAILED", "ACTION_FAILED", "JS_ERROR"}:
        return "frontend"
    return "unknown"


def _build_dedup_key(step_result: StepResult, failure_category: str) -> str:
    target = step_result.target or "no_target"
    page_url = step_result.page_url or "unknown_page"
    action_or_assert = step_result.action_key or step_result.assert_key or "unknown"
    return f"{failure_category.lower()}|{page_url}|{target}|{action_or_assert}"
