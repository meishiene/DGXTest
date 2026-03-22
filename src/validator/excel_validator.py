from __future__ import annotations

from src.parser.models import ParsedObjectRepository, ParsedTestSuite


ACTION_KEYS = {
    "open_page",
    "refresh_page",
    "click",
    "hover",
    "scroll_to",
    "input_text",
    "clear_and_input",
    "input_password",
    "select_option",
    "check",
    "uncheck",
    "press_key",
    "upload_file",
    "wait_element",
    "wait_url",
    "switch_frame",
}
ASSERT_KEYS = {
    "assert_url_contains",
    "assert_url_equals",
    "assert_element_visible",
    "assert_element_hidden",
    "assert_element_enabled",
    "assert_text_equals",
    "assert_text_contains",
    "assert_value_equals",
    "assert_toast_contains",
    "assert_count_equals",
    "assert_api_called",
    "assert_api_status",
}


def validate_parsed_workbooks(
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> None:
    case_ids = {item.case_id for item in suite.cases}
    if len(case_ids) != len(suite.cases):
        raise ValueError("Case_Index 中存在重复的 case_id")

    object_keys = {item.object_key for item in repository.objects}
    if len(object_keys) != len(repository.objects):
        raise ValueError("Element_Objects 中存在重复的 object_key")

    data_set_ids = {item.data_set_id for item in suite.test_data}
    step_keys: set[tuple[str, int]] = set()

    for case in suite.cases:
        if case.data_set_id and case.data_set_id not in data_set_ids:
            raise ValueError(f"case_id={case.case_id} 引用了不存在的 data_set_id={case.data_set_id}")

    for step in suite.steps:
        if step.case_id not in case_ids:
            raise ValueError(f"Case_Steps 引用了不存在的 case_id={step.case_id}")

        step_key = (step.case_id, step.step_no)
        if step_key in step_keys:
            raise ValueError(f"Case_Steps 中存在重复步骤: {step.case_id}#{step.step_no}")
        step_keys.add(step_key)

        if step.step_type not in {"action", "assert"}:
            raise ValueError(f"无效的 step_type: {step.case_id}#{step.step_no} -> {step.step_type}")

        if step.step_type == "action" and step.action_key and step.action_key not in ACTION_KEYS:
            raise ValueError(f"不支持的 action_key: {step.case_id}#{step.step_no} -> {step.action_key}")
        if step.step_type == "assert" and step.assert_key and step.assert_key not in ASSERT_KEYS:
            raise ValueError(f"不支持的 assert_key: {step.case_id}#{step.step_no} -> {step.assert_key}")

        if _requires_object_target(step.action_key, step.assert_key, step.target_type, step.target):
            if step.target not in object_keys:
                raise ValueError(f"步骤 target 无法在对象库中解析: {step.case_id}#{step.step_no} -> {step.target}")

    case_has_step = {item.case_id: False for item in suite.cases}
    for step in suite.steps:
        case_has_step[step.case_id] = True
    missing_steps = [case_id for case_id, has_step in case_has_step.items() if not has_step]
    if missing_steps:
        raise ValueError(f"以下用例没有步骤: {missing_steps}")


def _requires_object_target(action_key: str, assert_key: str, target_type: str, target: str) -> bool:
    if not target:
        return False
    if target_type in {"route", "url", "api"}:
        return False
    if action_key == "open_page":
        return False
    return True
