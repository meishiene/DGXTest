from pathlib import Path
from types import SimpleNamespace

from unittest.mock import ANY, Mock, call, patch

import pytest

from src.actions.executor import ActionExecutor
from src.artifacts.collector import PlaywrightRuntimeEvidence
from src.asserts.executor import AssertExecutor
from src.core.bootstrap import prepare_run_context
from src.objects.resolver import ResolvedObject
from src.parser.excel_parser import parse_object_repository, parse_test_workbook
from src.parser.models import CaseRecord, ParsedObjectRepository, ParsedTestSuite, StepRecord
from src.parser.template_generator import generate_excel_templates
from src.results.models import AppConfig
from src.runner.playwright_runner import _build_suite_run_settings, _select_runnable_cases, execute_run
from src.utils.data_resolver import CaseExecutionData


def test_object_repository_and_data_resolver(tmp_path: Path) -> None:
    test_workbook = tmp_path / "test_suite_template.xlsx"
    object_workbook = tmp_path / "object_repository_template.xlsx"
    generate_excel_templates(test_workbook, object_workbook)

    suite = parse_test_workbook(test_workbook)
    repository = parse_object_repository(object_workbook)

    placeholder_steps = [step for step in suite.steps if step.step_type == "assert" and not step.assert_key]
    assert len(placeholder_steps) == 0

    route_assert = next(step for step in suite.steps if step.case_id == "DGX_001" and step.step_no == 2)
    workspace_assert = next(step for step in suite.steps if step.case_id == "DGX_001" and step.step_no == 5)
    exact_result_assert = next(step for step in suite.steps if step.case_id == "DGX_002" and step.step_no == 23)
    landing_case_steps = [step for step in suite.steps if step.case_id == "DGX_003"]
    assert route_assert.assert_key == "assert_url_equals"
    assert workspace_assert.assert_key == "assert_element_visible"
    assert workspace_assert.target == "set_boundaries_button"
    assert exact_result_assert.assert_key == "assert_text_equals"
    assert any(step.action_key == "wait_element" for step in suite.steps)
    assert any(step.assert_key == "assert_element_hidden" for step in suite.steps)
    assert len(landing_case_steps) == 4
    assert len(repository.objects) == 15


def test_dry_run_no_longer_skips_placeholder_assertions(tmp_path: Path) -> None:
    test_workbook = tmp_path / "test_suite_template.xlsx"
    object_workbook = tmp_path / "object_repository_template.xlsx"
    generate_excel_templates(test_workbook, object_workbook)

    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        output_root=str(tmp_path / "outputs"),
        dry_run=True,
        demo_failure=False,
        test_workbook_path=str(test_workbook),
        object_repository_path=str(object_workbook),
    )
    suite = parse_test_workbook(test_workbook)
    repository = parse_object_repository(object_workbook)
    run_context = prepare_run_context(config)

    _, case_results, step_results, _ = execute_run(config, run_context, suite, repository)

    assert len(case_results) == 3
    skipped_steps = [step for step in step_results if step.status == "SKIPPED"]
    assert len(skipped_steps) == 0
    assert all(step.actual != "Assertion placeholder left empty in Excel" for step in step_results)


def test_build_suite_run_settings_and_case_filters_respect_tags_env_and_browser() -> None:
    suite = ParsedTestSuite(
        cases=[],
        steps=[],
        test_data=[],
        run_config_rows=[
            {"config_key": "target_env", "config_value": "demo"},
            {"config_key": "include_tags", "config_value": "smoke, critical"},
            {"config_key": "retry_failed_cases", "config_value": "Y"},
        ],
        dictionaries=[],
    )
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
    )
    cases = [
        _build_case("CASE_OK", tags=["smoke", "dgx"], env_scope=["demo"], browser_scope=["chromium"]),
        _build_case("CASE_ENV_SKIP", tags=["smoke"], env_scope=["stage"], browser_scope=["chromium"]),
        _build_case("CASE_BROWSER_SKIP", tags=["smoke"], env_scope=["demo"], browser_scope=["firefox"]),
        _build_case("CASE_TAG_SKIP", tags=["regression"], env_scope=["demo"], browser_scope=["chromium"]),
        _build_case("CASE_INACTIVE", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"], status="inactive"),
    ]

    run_settings = _build_suite_run_settings(suite)
    selected = _select_runnable_cases(cases, config, run_settings)

    assert run_settings.target_env == "demo"
    assert run_settings.include_tags == frozenset({"smoke", "critical"})
    assert run_settings.retry_failed_cases is True
    assert [case.case_id for case in selected] == ["CASE_OK"]


def test_click_retries_with_force_when_overlay_intercepts() -> None:
    locator = Mock()
    locator.click.side_effect = [Exception("leaflet-container intercepts pointer events"), None]
    resolved_object = _build_resolved_object()
    step = _build_action_step("click", timeout=5)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
    assert locator.click.call_args_list == [call(timeout=5000), call(timeout=5000, force=True)]
    assert result.actual_value == "clicked"


def test_click_does_not_force_retry_for_other_errors() -> None:
    locator = Mock()
    locator.click.side_effect = Exception("strict mode violation")
    resolved_object = _build_resolved_object()
    step = _build_action_step("click", timeout=5)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        with pytest.raises(Exception, match="strict mode violation"):
            ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    assert locator.click.call_args_list == [call(timeout=5000)]


def test_wait_element_uses_requested_wait_state() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_action_step("wait_element", timeout=5, wait="hidden")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)) as mocked_resolve:
        result = ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    mocked_resolve.assert_called_once_with(
        page=page,
        resolver=ANY,
        object_key="next_button",
        timeout_ms=30000,
        wait_for_attached=False,
    )
    locator.wait_for.assert_called_once_with(state="hidden", timeout=5000)
    assert result.actual_value == "hidden"


def test_hover_waits_until_visible_before_hovering() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_action_step("hover", timeout=5)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
    locator.hover.assert_called_once_with(timeout=5000)
    assert result.actual_value == "hovered"


def test_press_key_uses_resolved_value_on_locator() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_action_step("press_key", timeout=5, value="${submit_key}")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")
    case_data = CaseExecutionData(values={"submit_key": "Enter"})

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = ActionExecutor(Mock()).execute(page, step, case_data, "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
    locator.press.assert_called_once_with("Enter", timeout=5000)
    assert result.actual_value == "Enter"


def test_wait_url_uses_navigation_wait_until_without_object_lookup() -> None:
    page = Mock()
    page.url = "https://dgx.xlook.ai/dgx/ready"
    step = _build_action_step(
        "wait_url",
        timeout=6,
        wait="networkidle",
        value="",
        target="/dgx/ready",
        target_type="route",
    )

    with patch("src.actions.executor.resolve_locator") as mocked_resolve:
        result = ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    mocked_resolve.assert_not_called()
    page.wait_for_url.assert_called_once_with(
        "https://dgx.xlook.ai/dgx/ready",
        wait_until="networkidle",
        timeout=6000,
    )
    assert result.actual_value == "https://dgx.xlook.ai/dgx/ready"



def test_select_option_resolves_case_data_before_selecting() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_action_step("select_option", timeout=5, value="${layer_option}")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")
    case_data = CaseExecutionData(values={"layer_option": "Not Required"})

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = ActionExecutor(Mock()).execute(page, step, case_data, "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
    locator.select_option.assert_called_once_with(value="Not Required", timeout=5000)
    assert result.actual_value == "Not Required"



def test_upload_file_supports_multiple_paths() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_action_step("upload_file", timeout=5, value="C:/tmp/a.dxf, C:/tmp/b.dxf")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.actions.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = ActionExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=5000)
    locator.set_input_files.assert_called_once_with(["C:/tmp/a.dxf", "C:/tmp/b.dxf"], timeout=5000)
    assert result.actual_value == "C:/tmp/a.dxf, C:/tmp/b.dxf"


def test_assert_element_visible_waits_until_visible() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_element_visible", timeout=7)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=7000)
    assert result.actual_value == "visible"


def test_assert_element_hidden_uses_hidden_wait_without_attached_probe() -> None:
    locator = Mock()
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_element_hidden", timeout=7)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)) as mocked_resolve:
        result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    mocked_resolve.assert_called_once_with(
        page=page,
        resolver=ANY,
        object_key="next_button",
        timeout_ms=30000,
        wait_for_attached=False,
    )
    locator.wait_for.assert_called_once_with(state="hidden", timeout=7000)
    assert result.actual_value == "hidden"


def test_assert_element_enabled_waits_and_checks_enabled_state() -> None:
    locator = Mock()
    locator.is_enabled.return_value = True
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_element_enabled", timeout=7)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.wait_for.assert_called_once_with(state="visible", timeout=7000)
    locator.is_enabled.assert_called_once_with(timeout=7000)
    assert result.actual_value == "enabled"


def test_assert_element_enabled_raises_when_disabled() -> None:
    locator = Mock()
    locator.is_enabled.return_value = False
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_element_enabled", timeout=7)
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        with pytest.raises(AssertionError, match="Element is disabled"):
            AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)


def test_assert_count_equals_returns_actual_count() -> None:
    locator = Mock()
    locator.count.return_value = 3
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_count_equals", timeout=7, expected="3")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.count.assert_called_once_with()
    assert result.actual_value == "3"


def test_assert_count_equals_raises_when_count_differs() -> None:
    locator = Mock()
    locator.count.return_value = 2
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_count_equals", timeout=7, expected="3")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        with pytest.raises(AssertionError, match="Count assertion failed"):
            AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)


def test_assert_count_equals_requires_integer_expected_value() -> None:
    locator = Mock()
    locator.count.return_value = 2
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_count_equals", timeout=7, expected="three")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        with pytest.raises(ValueError, match="assert_count_equals requires integer expected value"):
            AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)


def test_assert_api_called_matches_relative_url_and_method() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.network_entries.extend(
        [
            {"event": "request", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "resource_type": "xhr"},
            {"event": "response", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "status": 200},
        ]
    )
    step = _build_assert_step(
        "assert_api_called",
        timeout=7,
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="equals",
    )
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    result = AssertExecutor(Mock(), runtime_evidence=runtime_evidence).execute(
        page,
        step,
        CaseExecutionData(values={}),
        "https://dgx.xlook.ai",
        30000,
    )

    assert result.actual_value == "https://dgx.xlook.ai/api/run"


def test_assert_api_called_raises_when_request_not_observed() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.network_entries.append(
        {"event": "request", "method": "GET", "url": "https://dgx.xlook.ai/api/health", "resource_type": "xhr"}
    )
    step = _build_assert_step(
        "assert_api_called",
        timeout=7,
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="contains",
    )
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with pytest.raises(AssertionError, match="API call assertion failed"):
        AssertExecutor(Mock(), runtime_evidence=runtime_evidence).execute(
            page,
            step,
            CaseExecutionData(values={}),
            "https://dgx.xlook.ai",
            30000,
        )


def test_assert_api_status_matches_relative_url_method_and_status() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.network_entries.extend(
        [
            {"event": "request", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "resource_type": "xhr"},
            {"event": "response", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "status": 201, "status_text": "Created", "ok": True},
        ]
    )
    step = _build_assert_step(
        "assert_api_status",
        timeout=7,
        expected="201",
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="equals",
    )
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    result = AssertExecutor(Mock(), runtime_evidence=runtime_evidence).execute(
        page,
        step,
        CaseExecutionData(values={}),
        "https://dgx.xlook.ai",
        30000,
    )

    assert result.actual_value == "201"


def test_assert_api_status_raises_when_status_differs() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.network_entries.append(
        {"event": "response", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "status": 500, "status_text": "Internal Server Error", "ok": False}
    )
    step = _build_assert_step(
        "assert_api_status",
        timeout=7,
        expected="200",
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="contains",
    )
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with pytest.raises(AssertionError, match="API status assertion failed: expected=200, actual=500"):
        AssertExecutor(Mock(), runtime_evidence=runtime_evidence).execute(
            page,
            step,
            CaseExecutionData(values={}),
            "https://dgx.xlook.ai",
            30000,
        )


def test_assert_api_status_requires_integer_expected_value() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.network_entries.append(
        {"event": "response", "method": "POST", "url": "https://dgx.xlook.ai/api/run", "status": 200, "status_text": "OK", "ok": True}
    )
    step = _build_assert_step(
        "assert_api_status",
        timeout=7,
        expected="ok",
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="contains",
    )
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with pytest.raises(ValueError, match="assert_api_status requires integer expected value"):
        AssertExecutor(Mock(), runtime_evidence=runtime_evidence).execute(
            page,
            step,
            CaseExecutionData(values={}),
            "https://dgx.xlook.ai",
            30000,
        )


def test_assert_url_equals_matches_full_url() -> None:
    step = _build_assert_step("assert_url_equals", timeout=7, expected="https://dgx.xlook.ai/dgx/demo")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    assert result.actual_value == "https://dgx.xlook.ai/dgx/demo"



def test_assert_text_equals_uses_exact_text_match() -> None:
    locator = Mock()
    locator.text_content.return_value = "Park Hyatt Abu Dhabi Hotel"
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_text_equals", timeout=7, expected="Park Hyatt Abu Dhabi Hotel")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)

    locator.text_content.assert_called_once_with(timeout=7000)
    assert result.actual_value == "Park Hyatt Abu Dhabi Hotel"



def test_assert_value_equals_reads_input_value() -> None:
    locator = Mock()
    locator.input_value.return_value = "Park Hyatt Abu Dhabi Hotel"
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_value_equals", timeout=7, expected="${project_result_name}")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")
    case_data = CaseExecutionData(values={"project_result_name": "Park Hyatt Abu Dhabi Hotel"})

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        result = AssertExecutor(Mock()).execute(page, step, case_data, "https://dgx.xlook.ai", 30000)

    locator.input_value.assert_called_once_with(timeout=7000)
    assert result.actual_value == "Park Hyatt Abu Dhabi Hotel"


def test_assert_value_equals_raises_when_value_differs() -> None:
    locator = Mock()
    locator.input_value.return_value = "unexpected"
    resolved_object = _build_resolved_object()
    step = _build_assert_step("assert_value_equals", timeout=7, expected="expected")
    page = SimpleNamespace(url="https://dgx.xlook.ai/dgx/demo")

    with patch("src.asserts.executor.resolve_locator", return_value=(locator, resolved_object)):
        with pytest.raises(AssertionError, match="Value assertion failed"):
            AssertExecutor(Mock()).execute(page, step, CaseExecutionData(values={}), "https://dgx.xlook.ai", 30000)


def _build_action_step(
    action_key: str,
    timeout: int,
    wait: str = "",
    continue_on_fail: str = "N",
    case_id: str = "DGX_002",
    step_no: int = 12,
    value: str = "",
    target: str = "next_button",
    target_type: str = "object",
) -> StepRecord:
    return StepRecord(
        case_id=case_id,
        step_no=step_no,
        step_type="action",
        step_name="Go to next setup step",
        action_key=action_key,
        assert_key="",
        page_name="DGXBoundaryPage",
        target=target,
        target_type=target_type,
        value=value,
        value_type="",
        expected="",
        expected_type="",
        match_type="",
        wait=wait,
        timeout=timeout,
        continue_on_fail=continue_on_fail,
        screenshot_on_fail="Y",
        ai_locator_hint="",
        remark="",
    )


def _build_assert_step(
    assert_key: str,
    timeout: int,
    expected: str = "",
    target: str = "next_button",
    target_type: str = "object",
    value: str = "",
    match_type: str = "equals",
) -> StepRecord:
    return StepRecord(
        case_id="DGX_002",
        step_no=20,
        step_type="assert",
        step_name="Assert boundary state",
        action_key="",
        assert_key=assert_key,
        page_name="DGXBoundaryPage",
        target=target,
        target_type=target_type,
        value=value,
        value_type="",
        expected=expected,
        expected_type="string",
        match_type=match_type,
        wait="",
        timeout=timeout,
        continue_on_fail="N",
        screenshot_on_fail="Y",
        ai_locator_hint="",
        remark="",
    )


def _build_resolved_object() -> ResolvedObject:
    return ResolvedObject(
        object_key="next_button",
        object_name="Next",
        page_name="DGXBoundaryPage",
        object_type="button",
        locator_type="css",
        locator_value=".lc-footer-next",
        component_hint="",
        frontend_file_hint="",
        api_hint="",
        default_wait="visible",
        default_timeout_sec=30,
    )


def test_live_runner_continues_after_failure_when_step_allows_it(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[_build_case("CASE_CONTINUE", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"])],
        steps=[
            _build_action_step("click", timeout=5, continue_on_fail="Y", case_id="CASE_CONTINUE", step_no=1),
            _build_action_step("click", timeout=5, continue_on_fail="N", case_id="CASE_CONTINUE", step_no=2),
        ],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        if step.step_no == 1:
            raise RuntimeError("first step failed")
        return SimpleNamespace(actual_value="clicked", page_url=page.url, resolved_object=None)

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor), \
         patch("src.runner.playwright_runner.AssertExecutor", return_value=Mock()), \
         patch("src.runner.playwright_runner.capture_playwright_failure_artifacts", return_value=[]):
        run_info, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)

    assert run_info.environment == "demo"
    assert artifacts == []
    assert [step.status for step in step_results] == ["FAILED", "PASSED"]
    assert case_results[0].status == "FAILED"
    assert case_results[0].failed_step_no == 1
    assert case_results[0].failed_step_name == "Go to next setup step"
    assert case_results[0].failure_message == "first step failed"
    assert fake_action_executor.execute.call_count == 2


def test_live_runner_retries_failed_case_when_enabled(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[
            _build_case(
                "CASE_RETRY",
                tags=["smoke"],
                env_scope=["demo"],
                browser_scope=["chromium"],
                retry_policy="case_retry_1",
            )
        ],
        steps=[_build_action_step("click", timeout=5, case_id="CASE_RETRY", step_no=1)],
        test_data=[],
        run_config_rows=[
            {"config_key": "target_env", "config_value": "demo"},
            {"config_key": "retry_failed_cases", "config_value": "Y"},
        ],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()
    call_count = {"value": 0}

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        call_count["value"] += 1
        if call_count["value"] == 1:
            raise RuntimeError("first attempt failed")
        return SimpleNamespace(actual_value="clicked", page_url=page.url, resolved_object=None)

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor), \
         patch("src.runner.playwright_runner.AssertExecutor", return_value=Mock()), \
         patch("src.runner.playwright_runner.capture_playwright_failure_artifacts", return_value=[]):
        _, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)

    assert artifacts == []
    assert [step.status for step in step_results] == ["FAILED", "PASSED"]
    assert [step.attempt_no for step in step_results] == [1, 2]
    assert case_results[0].status == "PASSED"
    assert case_results[0].retry_count == 1
    assert fake_action_executor.execute.call_count == 2



def test_live_runner_blocks_case_when_dependency_failed(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[
            _build_case("CASE_PARENT", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"]),
            _build_case(
                "CASE_CHILD",
                tags=["smoke"],
                env_scope=["demo"],
                browser_scope=["chromium"],
                depends_on_case="CASE_PARENT",
            ),
        ],
        steps=[
            _build_action_step("click", timeout=5, case_id="CASE_PARENT", step_no=1),
            _build_action_step("click", timeout=5, case_id="CASE_CHILD", step_no=1),
        ],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        if step.case_id == "CASE_PARENT":
            raise RuntimeError("parent failed")
        return SimpleNamespace(actual_value="clicked", page_url=page.url, resolved_object=None)

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor), \
         patch("src.runner.playwright_runner.AssertExecutor", return_value=Mock()), \
         patch("src.runner.playwright_runner.capture_playwright_failure_artifacts", return_value=[]):
        _, case_results, step_results, _ = execute_run(config, run_context, suite, repository)

    assert [case.case_id for case in case_results] == ["CASE_PARENT", "CASE_CHILD"]
    assert [case.status for case in case_results] == ["FAILED", "BLOCKED"]
    assert case_results[1].blocked_by_case_id == "CASE_PARENT"
    assert "依赖用例未通过" in case_results[1].failure_message
    assert [step.case_id for step in step_results] == ["CASE_PARENT"]
    assert fake_action_executor.execute.call_count == 1



def test_live_runner_orders_dependency_case_before_dependent_case(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[
            _build_case(
                "CASE_CHILD",
                tags=["smoke"],
                env_scope=["demo"],
                browser_scope=["chromium"],
                depends_on_case="CASE_PARENT",
            ),
            _build_case("CASE_PARENT", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"]),
        ],
        steps=[
            _build_action_step("click", timeout=5, case_id="CASE_PARENT", step_no=1),
            _build_action_step("click", timeout=5, case_id="CASE_CHILD", step_no=1),
        ],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()
    fake_action_executor.execute.return_value = SimpleNamespace(actual_value="clicked", page_url="https://dgx.xlook.ai/dgx/demo", resolved_object=None)

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor), \
         patch("src.runner.playwright_runner.AssertExecutor", return_value=Mock()), \
         patch("src.runner.playwright_runner.capture_playwright_failure_artifacts", return_value=[]):
        _, case_results, step_results, _ = execute_run(config, run_context, suite, repository)

    assert [case.case_id for case in case_results] == ["CASE_PARENT", "CASE_CHILD"]
    assert [step.case_id for step in step_results] == ["CASE_PARENT", "CASE_CHILD"]



def test_live_runner_assert_api_called_uses_runtime_network_evidence_even_without_network_artifact_capture(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
        capture_network_log=False,
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[_build_case("CASE_API_ASSERT", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"])],
        steps=[
            _build_action_step("click", timeout=5, case_id="CASE_API_ASSERT", step_no=1),
            _build_assert_step("assert_api_called", timeout=5),
        ],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    suite.steps[1] = _build_assert_step(
        "assert_api_called",
        timeout=5,
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="contains",
    )
    suite.steps[1].case_id = "CASE_API_ASSERT"
    suite.steps[1].step_no = 2
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        page.emit_request("POST", "https://dgx.xlook.ai/api/run")
        return SimpleNamespace(actual_value="clicked", page_url=page.url, resolved_object=None)

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor):
        _, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)

    assert artifacts == []
    assert [step.status for step in step_results] == ["PASSED", "PASSED"]
    assert step_results[1].actual == "https://dgx.xlook.ai/api/run"
    assert case_results[0].status == "PASSED"


def test_live_runner_assert_api_status_uses_runtime_network_evidence_even_without_network_artifact_capture(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
        capture_network_log=False,
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[_build_case("CASE_API_STATUS", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"])],
        steps=[
            _build_action_step("click", timeout=5, case_id="CASE_API_STATUS", step_no=1),
            _build_assert_step("assert_api_status", timeout=5),
        ],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    suite.steps[1] = _build_assert_step(
        "assert_api_status",
        timeout=5,
        expected="201",
        target="/api/run",
        target_type="api",
        value="POST",
        match_type="contains",
    )
    suite.steps[1].case_id = "CASE_API_STATUS"
    suite.steps[1].step_no = 2
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        page.emit_request("POST", "https://dgx.xlook.ai/api/run")
        page.emit_response("POST", "https://dgx.xlook.ai/api/run", 201, "Created", True)
        return SimpleNamespace(actual_value="clicked", page_url=page.url, resolved_object=None)

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()), \
         patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor):
        _, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)

    assert artifacts == []
    assert [step.status for step in step_results] == ["PASSED", "PASSED"]
    assert step_results[1].actual == "201"
    assert case_results[0].status == "PASSED"


def test_live_runner_collects_configured_failure_evidence(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
        capture_screenshot=True,
        capture_dom_snapshot=True,
        capture_console_log=True,
        capture_network_log=False,
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[_build_case("CASE_FAIL", tags=["smoke"], env_scope=["demo"], browser_scope=["chromium"])],
        steps=[_build_action_step("click", timeout=5, case_id="CASE_FAIL", step_no=1)],
        test_data=[],
        run_config_rows=[{"config_key": "target_env", "config_value": "demo"}],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])

    fake_action_executor = Mock()

    def action_side_effect(*, page, step, case_data, base_url, timeout_ms):
        page.emit_console_error("TypeError: live failure")
        page.emit_request("POST", "https://dgx.xlook.ai/api/run")
        raise RuntimeError("case failed")

    fake_action_executor.execute.side_effect = action_side_effect

    with patch("playwright.sync_api.sync_playwright", return_value=_FakePlaywrightContext()),          patch("src.runner.playwright_runner.ActionExecutor", return_value=fake_action_executor),          patch("src.runner.playwright_runner.AssertExecutor", return_value=Mock()):
        _, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)

    assert case_results[0].status == "FAILED"
    assert [step.status for step in step_results] == ["FAILED"]
    assert [artifact.artifact_type for artifact in artifacts] == ["screenshot", "dom_snapshot", "console_log"]
    assert all("SR_" in artifact.artifact_id for artifact in artifacts)
    assert all(Path(artifact.file_path).exists() for artifact in artifacts)


def test_live_runner_opens_headed_chromium_maximized(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=False,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[],
        steps=[],
        test_data=[],
        run_config_rows=[],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])
    fake_playwright = _FakePlaywrightContext()

    with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright):
        execute_run(config, run_context, suite, repository)

    chromium = fake_playwright.playwright.chromium
    assert chromium.launch_calls == [{"headless": False, "args": ["--start-maximized"]}]
    assert chromium.last_browser is not None
    assert chromium.last_browser.new_page_calls == [{"no_viewport": True}]
    assert len(chromium.last_browser._page.evaluate_calls) == 1
    assert "window.resizeTo(window.screen.availWidth, window.screen.availHeight)" in chromium.last_browser._page.evaluate_calls[0]


def test_live_runner_skips_maximize_options_in_headless_mode(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="dgx_demo_suite",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        browser="chromium",
        headless=True,
        dry_run=False,
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    suite = ParsedTestSuite(
        cases=[],
        steps=[],
        test_data=[],
        run_config_rows=[],
        dictionaries=[],
    )
    repository = ParsedObjectRepository(pages=[], objects=[])
    fake_playwright = _FakePlaywrightContext()

    with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright):
        execute_run(config, run_context, suite, repository)

    chromium = fake_playwright.playwright.chromium
    assert chromium.launch_calls == [{"headless": True}]
    assert chromium.last_browser is not None
    assert chromium.last_browser.new_page_calls == [{}]
    assert chromium.last_browser._page.evaluate_calls == []


def _build_case(
    case_id: str,
    tags: list[str],
    env_scope: list[str],
    browser_scope: list[str],
    status: str = "active",
    automation_flag: str = "Y",
    retry_policy: str = "",
    require_login: str = "N",
    depends_on_case: str = "",
) -> CaseRecord:
    return CaseRecord(
        case_id=case_id,
        case_name=f"Case {case_id}",
        module="DGX",
        sub_module="Demo",
        feature_name="Runner Filters",
        priority="P1",
        test_level="smoke",
        tags=tags,
        status=status,
        automation_flag=automation_flag,
        data_set_id="",
        preconditions="",
        expected_result_summary="",
        owner="tester",
        env_scope=env_scope,
        browser_scope=browser_scope,
        can_parallel="Y",
        retry_policy=retry_policy,
        require_login=require_login,
        depends_on_case=depends_on_case,
    )

class _FakeBrowser:
    def __init__(self) -> None:
        self._page = _FakePage()
        self.new_page_calls: list[dict[str, object]] = []

    def new_page(self, **kwargs):
        self.new_page_calls.append(dict(kwargs))
        return self._page

    def close(self) -> None:
        return None


class _FakeBrowserType:
    def __init__(self) -> None:
        self.launch_calls: list[dict[str, object]] = []
        self.last_browser: _FakeBrowser | None = None

    def launch(self, **kwargs):
        self.launch_calls.append(dict(kwargs))
        self.last_browser = _FakeBrowser()
        return self.last_browser


class _FakePlaywright:
    def __init__(self) -> None:
        self.chromium = _FakeBrowserType()
        self.firefox = _FakeBrowserType()
        self.webkit = _FakeBrowserType()


class _FakePlaywrightContext:
    def __init__(self) -> None:
        self.playwright = _FakePlaywright()

    def __enter__(self) -> _FakePlaywright:
        return self.playwright

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakePage:
    def __init__(self) -> None:
        self.url = "https://dgx.xlook.ai/dgx/demo"
        self._handlers: dict[str, list] = {}
        self.evaluate_calls: list[str] = []

    def on(self, event_name: str, handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def emit_console_error(self, message: str) -> None:
        payload = SimpleNamespace(
            type="error",
            text=message,
            location={"url": self.url, "lineNumber": 1, "columnNumber": 1},
        )
        for handler in self._handlers.get("console", []):
            handler(payload)

    def emit_request(self, method: str, url: str) -> None:
        payload = SimpleNamespace(method=method, url=url, resource_type="xhr")
        for handler in self._handlers.get("request", []):
            handler(payload)

    def emit_response(self, method: str, url: str, status: int, status_text: str, ok: bool) -> None:
        payload = SimpleNamespace(
            request=SimpleNamespace(method=method, resource_type="xhr"),
            url=url,
            status=status,
            status_text=status_text,
            ok=ok,
        )
        for handler in self._handlers.get("response", []):
            handler(payload)

    def screenshot(self, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"fake-png")

    def content(self) -> str:
        return "<html><body>live failure</body></html>"

    def evaluate(self, expression: str):
        self.evaluate_calls.append(expression)
        return None





