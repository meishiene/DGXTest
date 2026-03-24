from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from src.actions.executor import ActionExecutor
from src.artifacts.collector import (
    PlaywrightRuntimeEvidence,
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
NETWORK_ASSERT_KEYS = frozenset({"assert_api_called", "assert_api_status"})
HEADED_CHROMIUM_LAUNCH_ARGS = ("--start-maximized",)


@dataclass(slots=True, frozen=True)
class SuiteRunSettings:
    target_env: str
    include_tags: frozenset[str]
    retry_failed_cases: bool


@dataclass(slots=True)
class CaseAttemptRuntimeResult:
    step_results: list[StepResult]
    artifacts: list[ArtifactRecord]
    failed: bool
    failure_message: str = ""
    failure_category: str = ""
    failed_step_no: int = 0
    failed_step_name: str = ""
    failed_step_result: StepResult | None = None


def execute_run(
    config: AppConfig,
    run_context: RunContext,
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    run_settings = _build_suite_run_settings(suite)
    if config.dry_run:
        return _execute_dry_run(config, run_context, suite, repository, run_settings)
    return _execute_live_run(config, run_context, suite, repository, run_settings)


def _build_run_info(
    config: AppConfig,
    run_context: RunContext,
    summary: ExecutionSummary,
    environment: str,
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
        environment=environment,
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
    run_settings: SuiteRunSettings,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    step_results: list[StepResult] = []
    case_results: list[CaseResult] = []
    artifacts: list[ArtifactRecord] = []

    runnable_cases = _order_cases_for_execution(_select_runnable_cases(suite.cases, config, run_settings))
    runnable_case_ids = {case.case_id for case in runnable_cases}
    case_steps = _group_steps_by_case(suite)
    object_map = {item.object_key: item for item in repository.objects}
    case_results_by_id: dict[str, CaseResult] = {}
    synthetic_failure_emitted = False

    for case in runnable_cases:
        dependency_case_id, block_reason = _resolve_case_block_reason(case, case_results_by_id, runnable_case_ids)
        if block_reason:
            blocked_result = _build_blocked_case_result(run_context.run_id, case, dependency_case_id, block_reason)
            case_results.append(blocked_result)
            case_results_by_id[case.case_id] = blocked_result
            continue

        max_attempts = _resolve_case_attempt_limit(case, run_settings)
        should_fail_case = config.demo_failure and not synthetic_failure_emitted

        if should_fail_case:
            synthetic_failure_emitted = True
            fail_steps = case_steps.get(case.case_id, [])
            fail_step = _pick_failure_step(fail_steps)
            object_record = object_map.get(fail_step.target) if fail_step else None
            final_failed_step_result: StepResult | None = None
            case_artifacts: list[ArtifactRecord] = []

            for attempt_no in range(1, max_attempts + 1):
                step_result = StepResult(
                    step_result_id=_build_step_result_id(run_context.run_id, case.case_id, fail_step.step_no, attempt_no),
                    run_id=run_context.run_id,
                    case_id=case.case_id,
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
                    attempt_no=attempt_no,
                )
                step_results.append(step_result)
                final_failed_step_result = step_result
                attempt_artifacts = create_dry_run_failure_artifacts(
                    run_context=run_context,
                    run_id=run_context.run_id,
                    case_id=case.case_id,
                    step_result_id=step_result.step_result_id,
                    capture_screenshot=config.capture_screenshot and _is_enabled(fail_step.screenshot_on_fail),
                    capture_dom_snapshot=config.capture_dom_snapshot,
                    capture_console_log=config.capture_console_log,
                    capture_network_log=config.capture_network_log,
                )
                artifacts.extend(attempt_artifacts)
                case_artifacts.extend(attempt_artifacts)

            case_result = _build_failed_case_result(
                run_id=run_context.run_id,
                case=case,
                failure_category="JS_ERROR",
                failure_message="Boundary workflow state did not update after the recorded action",
                failed_step_no=fail_step.step_no,
                failed_step_name=fail_step.step_name,
                failed_step_result=final_failed_step_result,
                artifact_ids=[artifact.artifact_id for artifact in case_artifacts],
                retry_count=max_attempts - 1,
                actual_summary="The DGX boundary workflow did not reflect the expected state change after the recorded interaction",
            )
            case_results.append(case_result)
            case_results_by_id[case.case_id] = case_result
            continue

        pass_case_steps = case_steps.get(case.case_id, [])
        step_results.extend(_build_pass_step_results(run_context.run_id, case.case_id, pass_case_steps, config.base_url))
        case_result = _build_pass_case_result(run_context.run_id, case, retry_count=0)
        case_results.append(case_result)
        case_results_by_id[case.case_id] = case_result

    summary = ExecutionSummary.from_case_results(case_results)
    return _build_run_info(
        config,
        run_context,
        summary,
        environment=run_settings.target_env or "local",
    ), case_results, step_results, artifacts


def _execute_live_run(
    config: AppConfig,
    run_context: RunContext,
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
    run_settings: SuiteRunSettings,
) -> tuple[RunInfo, list[CaseResult], list[StepResult], list[ArtifactRecord]]:
    from playwright.sync_api import sync_playwright

    step_results: list[StepResult] = []
    case_results: list[CaseResult] = []
    artifacts: list[ArtifactRecord] = []

    runnable_cases = _order_cases_for_execution(_select_runnable_cases(suite.cases, config, run_settings))
    runnable_case_ids = {case.case_id for case in runnable_cases}
    case_steps = _group_steps_by_case(suite)
    object_resolver = ObjectRepositoryResolver(repository)
    data_resolver = DataResolver(suite)
    case_results_by_id: dict[str, CaseResult] = {}

    with sync_playwright() as playwright:
        browser_factory = getattr(playwright, config.browser)
        browser = _launch_browser(browser_factory, config)
        page = _create_browser_page(browser, config)
        runtime_evidence = PlaywrightRuntimeEvidence(
            capture_console_log=config.capture_console_log,
            capture_network_log=config.capture_network_log or _suite_requires_network_evidence(suite),
        )
        runtime_evidence.attach(page)
        action_executor = ActionExecutor(object_resolver)
        assert_executor = AssertExecutor(object_resolver, runtime_evidence=runtime_evidence)

        try:
            for case in runnable_cases:
                dependency_case_id, block_reason = _resolve_case_block_reason(case, case_results_by_id, runnable_case_ids)
                if block_reason:
                    blocked_result = _build_blocked_case_result(run_context.run_id, case, dependency_case_id, block_reason)
                    case_results.append(blocked_result)
                    case_results_by_id[case.case_id] = blocked_result
                    continue

                case_data = data_resolver.build_case_data(case)
                case_step_list = case_steps.get(case.case_id, [])
                max_attempts = _resolve_case_attempt_limit(case, run_settings)
                attempts_used = 0
                final_attempt_result: CaseAttemptRuntimeResult | None = None
                case_artifacts: list[ArtifactRecord] = []

                for attempt_no in range(1, max_attempts + 1):
                    attempts_used = attempt_no
                    attempt_result = _execute_live_case_attempt(
                        page=page,
                        case=case,
                        case_steps=case_step_list,
                        run_context=run_context,
                        config=config,
                        object_resolver=object_resolver,
                        action_executor=action_executor,
                        assert_executor=assert_executor,
                        case_data=case_data,
                        attempt_no=attempt_no,
                        runtime_evidence=runtime_evidence,
                    )
                    final_attempt_result = attempt_result
                    step_results.extend(attempt_result.step_results)
                    artifacts.extend(attempt_result.artifacts)
                    case_artifacts.extend(attempt_result.artifacts)
                    if not attempt_result.failed:
                        break

                if final_attempt_result is None:
                    continue

                if final_attempt_result.failed:
                    case_result = _build_failed_case_result(
                        run_id=run_context.run_id,
                        case=case,
                        failure_category=final_attempt_result.failure_category,
                        failure_message=final_attempt_result.failure_message,
                        failed_step_no=final_attempt_result.failed_step_no,
                        failed_step_name=final_attempt_result.failed_step_name,
                        failed_step_result=final_attempt_result.failed_step_result,
                        artifact_ids=[artifact.artifact_id for artifact in case_artifacts],
                        retry_count=max(0, attempts_used - 1),
                    )
                else:
                    case_result = _build_pass_case_result(
                        run_context.run_id,
                        case,
                        retry_count=max(0, attempts_used - 1),
                    )

                case_results.append(case_result)
                case_results_by_id[case.case_id] = case_result
        finally:
            browser.close()

    summary = ExecutionSummary.from_case_results(case_results)
    return _build_run_info(
        config,
        run_context,
        summary,
        environment=run_settings.target_env or "local",
    ), case_results, step_results, artifacts


def _launch_browser(browser_factory, config: AppConfig):
    launch_options: dict[str, object] = {"headless": config.headless}
    if not config.headless and config.browser == "chromium":
        launch_options["args"] = list(HEADED_CHROMIUM_LAUNCH_ARGS)
    return browser_factory.launch(**launch_options)


def _create_browser_page(browser, config: AppConfig):
    page_options: dict[str, object] = {}
    if not config.headless:
        page_options["no_viewport"] = True

    page = browser.new_page(**page_options)
    if not config.headless:
        _try_resize_window_to_screen(page)
    return page


def _try_resize_window_to_screen(page) -> None:
    try:
        page.evaluate(
            "() => { if (typeof window !== 'undefined' && window.screen) { window.moveTo(0, 0); window.resizeTo(window.screen.availWidth, window.screen.availHeight); } }"
        )
    except Exception:
        return


def _execute_live_case_attempt(
    page,
    case: CaseRecord,
    case_steps: list[StepRecord],
    run_context: RunContext,
    config: AppConfig,
    object_resolver: ObjectRepositoryResolver,
    action_executor: ActionExecutor,
    assert_executor: AssertExecutor,
    case_data,
    attempt_no: int,
    runtime_evidence: PlaywrightRuntimeEvidence,
) -> CaseAttemptRuntimeResult:
    current_case_step_results: list[StepResult] = []
    current_case_artifacts: list[ArtifactRecord] = []
    case_failed = False
    failure_message = ""
    failure_category = ""
    failed_step_no = 0
    failed_step_name = ""
    failed_step_result: StepResult | None = None
    runtime_evidence.reset()

    for step in case_steps:
        step_result_id = _build_step_result_id(run_context.run_id, case.case_id, step.step_no, attempt_no)
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
                        attempt_no=attempt_no,
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
                        attempt_no=attempt_no,
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
                    attempt_no=attempt_no,
                )
            )
        except Exception as exc:
            current_failure_message = str(exc)
            current_failure_category = _categorize_failure(exc, step)
            if not case_failed:
                failure_message = current_failure_message
                failure_category = current_failure_category
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

            failed_step_result = _build_step_result(
                run_id=run_context.run_id,
                case_id=case.case_id,
                step=step,
                step_result_id=step_result_id,
                status="FAILED",
                actual="",
                page_url=page.url,
                resolved_object=resolved_object,
                error_type=current_failure_category,
                error_message=current_failure_message,
                attempt_no=attempt_no,
            )
            current_case_step_results.append(failed_step_result)
            current_case_artifacts.extend(
                capture_playwright_failure_artifacts(
                    run_context=run_context,
                    run_id=run_context.run_id,
                    case_id=case.case_id,
                    step_result_id=step_result_id,
                    page=page,
                    runtime_evidence=runtime_evidence,
                    capture_screenshot=config.capture_screenshot and _is_enabled(step.screenshot_on_fail),
                    capture_dom_snapshot=config.capture_dom_snapshot,
                    capture_console_log=config.capture_console_log,
                    capture_network_log=config.capture_network_log,
                )
            )
            case_failed = True
            if _should_continue_after_failure(step):
                continue
            break

    return CaseAttemptRuntimeResult(
        step_results=current_case_step_results,
        artifacts=current_case_artifacts,
        failed=case_failed,
        failure_message=failure_message,
        failure_category=failure_category,
        failed_step_no=failed_step_no,
        failed_step_name=failed_step_name,
        failed_step_result=failed_step_result,
    )


def _suite_requires_network_evidence(suite: ParsedTestSuite) -> bool:
    return any(step.step_type == "assert" and step.assert_key in NETWORK_ASSERT_KEYS for step in suite.steps)


def _build_suite_run_settings(suite: ParsedTestSuite) -> SuiteRunSettings:
    config_map = {
        row.get("config_key", "").strip(): row.get("config_value", "").strip()
        for row in suite.run_config_rows
        if row.get("config_key", "").strip()
    }
    target_env = config_map.get("target_env", "").strip()
    include_tags = frozenset(_normalize_csv_values(config_map.get("include_tags", "")))
    return SuiteRunSettings(
        target_env=target_env,
        include_tags=include_tags,
        retry_failed_cases=_is_enabled(config_map.get("retry_failed_cases", "")),
    )


def _select_runnable_cases(
    cases: list[CaseRecord],
    config: AppConfig,
    run_settings: SuiteRunSettings,
) -> list[CaseRecord]:
    selected_cases: list[CaseRecord] = []
    requested_browser = config.browser.strip().lower()
    requested_env = run_settings.target_env.strip().lower()
    for item in cases:
        if item.status.strip().lower() != "active":
            continue
        if item.automation_flag.strip().upper() != "Y":
            continue
        if run_settings.include_tags:
            case_tags = {tag.strip().lower() for tag in item.tags if tag.strip()}
            if not case_tags.intersection(run_settings.include_tags):
                continue
        if requested_env:
            allowed_envs = {value.strip().lower() for value in item.env_scope if value.strip()}
            if allowed_envs and requested_env not in allowed_envs:
                continue
        allowed_browsers = {value.strip().lower() for value in item.browser_scope if value.strip()}
        if allowed_browsers and requested_browser not in allowed_browsers:
            continue
        selected_cases.append(item)
    return selected_cases


def _order_cases_for_execution(cases: list[CaseRecord]) -> list[CaseRecord]:
    case_map = {case.case_id: case for case in cases}
    ordered_cases: list[CaseRecord] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(case: CaseRecord) -> None:
        if case.case_id in visited:
            return
        if case.case_id in visiting:
            raise ValueError(f"Circular depends_on_case detected at {case.case_id}")
        visiting.add(case.case_id)
        dependency_case_id = case.depends_on_case.strip()
        if dependency_case_id and dependency_case_id in case_map:
            visit(case_map[dependency_case_id])
        visiting.remove(case.case_id)
        visited.add(case.case_id)
        ordered_cases.append(case)

    for case in cases:
        visit(case)

    return ordered_cases


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
                step_result_id=_build_step_result_id(run_id, case_id, step.step_no, 1),
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
                attempt_no=1,
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


def _should_continue_after_failure(step: StepRecord) -> bool:
    return _is_enabled(step.continue_on_fail)


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
    attempt_no: int = 1,
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
        attempt_no=attempt_no,
    )


def _build_pass_case_result(run_id: str, case: CaseRecord, retry_count: int) -> CaseResult:
    actual_summary = "所有动作通过，未填写的断言占位已标记为跳过"
    if retry_count:
        actual_summary = f"所有动作通过，失败后已重试 {retry_count} 次"
    return CaseResult(
        case_result_id=f"CR_{run_id}_{case.case_id}",
        run_id=run_id,
        case_id=case.case_id,
        case_name=case.case_name,
        module=case.module,
        sub_module=case.sub_module,
        priority=case.priority,
        status="PASSED",
        failure_category="",
        expected_summary=case.expected_result_summary,
        actual_summary=actual_summary,
        retry_count=retry_count,
    )


def _build_failed_case_result(
    run_id: str,
    case: CaseRecord,
    failure_category: str,
    failure_message: str,
    failed_step_no: int,
    failed_step_name: str,
    failed_step_result: StepResult | None,
    artifact_ids: list[str],
    retry_count: int,
    actual_summary: str | None = None,
) -> CaseResult:
    resolved_actual_summary = actual_summary or f"步骤失败: {failed_step_name}"
    if retry_count:
        resolved_actual_summary = f"{resolved_actual_summary}；已重试 {retry_count} 次"
    return CaseResult(
        case_result_id=f"CR_{run_id}_{case.case_id}",
        run_id=run_id,
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
        actual_summary=resolved_actual_summary,
        bug_candidate=_is_bug_candidate(failure_category),
        dedup_key=_build_dedup_key(failed_step_result, failure_category),
        artifact_ids=artifact_ids,
        suspected_layer=_infer_layer(failure_category),
        retry_count=retry_count,
    )


def _build_blocked_case_result(
    run_id: str,
    case: CaseRecord,
    dependency_case_id: str,
    block_reason: str,
) -> CaseResult:
    return CaseResult(
        case_result_id=f"CR_{run_id}_{case.case_id}",
        run_id=run_id,
        case_id=case.case_id,
        case_name=case.case_name,
        module=case.module,
        sub_module=case.sub_module,
        priority=case.priority,
        status="BLOCKED",
        failure_category="DEPENDENCY_BLOCKED",
        expected_summary=case.expected_result_summary,
        actual_summary=f"依赖用例阻断: {dependency_case_id}",
        failure_message=block_reason,
        blocked_by_case_id=dependency_case_id,
    )


def _resolve_case_block_reason(
    case: CaseRecord,
    case_results_by_id: dict[str, CaseResult],
    runnable_case_ids: set[str],
) -> tuple[str, str | None]:
    dependency_case_id = case.depends_on_case.strip()
    if not dependency_case_id:
        return "", None
    if dependency_case_id not in runnable_case_ids:
        return dependency_case_id, f"依赖用例未被选中或不可执行: {dependency_case_id}"
    dependency_result = case_results_by_id.get(dependency_case_id)
    if dependency_result is None:
        return dependency_case_id, f"依赖用例尚未执行完成: {dependency_case_id}"
    if dependency_result.status != "PASSED":
        return dependency_case_id, f"依赖用例未通过: {dependency_case_id} ({dependency_result.status})"
    return dependency_case_id, None


def _resolve_case_attempt_limit(case: CaseRecord, run_settings: SuiteRunSettings) -> int:
    if not run_settings.retry_failed_cases:
        return 1
    retry_numbers = re.findall(r"\d+", case.retry_policy)
    if retry_numbers:
        return max(1, int(retry_numbers[-1]) + 1)
    return 2


def _build_step_result_id(run_id: str, case_id: str, step_no: int, attempt_no: int) -> str:
    base_id = f"SR_{run_id}_{case_id}_{step_no:02d}"
    if attempt_no <= 1:
        return base_id
    return f"{base_id}_A{attempt_no:02d}"


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


def _build_dedup_key(step_result: StepResult | None, failure_category: str) -> str:
    if step_result is None:
        return failure_category.lower()
    target = step_result.target or "no_target"
    page_url = step_result.page_url or "unknown_page"
    action_or_assert = step_result.action_key or step_result.assert_key or "unknown"
    return f"{failure_category.lower()}|{page_url}|{target}|{action_or_assert}"


def _normalize_csv_values(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    return [item.strip().lower() for item in raw_value.split(",") if item.strip()]


def _is_enabled(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"y", "yes", "true", "1"}
