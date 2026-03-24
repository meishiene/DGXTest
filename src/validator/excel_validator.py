from __future__ import annotations

from src.actions.executor import SUPPORTED_ACTION_KEYS
from src.asserts.executor import SUPPORTED_ASSERT_KEYS
from src.parser.models import ParsedObjectRepository, ParsedTestSuite


ACTION_KEYS = SUPPORTED_ACTION_KEYS
ASSERT_KEYS = SUPPORTED_ASSERT_KEYS


def validate_parsed_workbooks(
    suite: ParsedTestSuite,
    repository: ParsedObjectRepository,
) -> None:
    case_ids = {item.case_id for item in suite.cases}
    if len(case_ids) != len(suite.cases):
        raise ValueError("Duplicate case_id found in Case_Index")

    object_keys = {item.object_key for item in repository.objects}
    if len(object_keys) != len(repository.objects):
        raise ValueError("Duplicate object_key found in Element_Objects")

    data_set_ids = {item.data_set_id for item in suite.test_data}
    step_keys: set[tuple[str, int]] = set()

    for case in suite.cases:
        if case.data_set_id and case.data_set_id not in data_set_ids:
            raise ValueError(f"Unknown data_set_id referenced by case {case.case_id}: {case.data_set_id}")
        dependency_case_id = case.depends_on_case.strip()
        if dependency_case_id and dependency_case_id not in case_ids:
            raise ValueError(f"Unknown depends_on_case referenced by case {case.case_id}: {dependency_case_id}")
        if dependency_case_id and dependency_case_id == case.case_id:
            raise ValueError(f"Case cannot depend on itself: {case.case_id}")

    for step in suite.steps:
        if step.case_id not in case_ids:
            raise ValueError(f"Unknown case_id referenced by Case_Steps: {step.case_id}")

        step_key = (step.case_id, step.step_no)
        if step_key in step_keys:
            raise ValueError(f"Duplicate step detected: {step.case_id}#{step.step_no}")
        step_keys.add(step_key)

        if step.step_type not in {"action", "assert"}:
            raise ValueError(f"Invalid step_type at {step.case_id}#{step.step_no}: {step.step_type}")

        if step.step_type == "action" and step.action_key and step.action_key not in ACTION_KEYS:
            raise ValueError(f"Unsupported action_key at {step.case_id}#{step.step_no}: {step.action_key}")
        if step.step_type == "assert" and step.assert_key and step.assert_key not in ASSERT_KEYS:
            raise ValueError(f"Unsupported assert_key at {step.case_id}#{step.step_no}: {step.assert_key}")

        if _requires_object_target(step.action_key, step.assert_key, step.target_type, step.target):
            if step.target not in object_keys:
                raise ValueError(f"Target cannot be resolved from object repository at {step.case_id}#{step.step_no}: {step.target}")

    case_has_step = {item.case_id: False for item in suite.cases}
    for step in suite.steps:
        case_has_step[step.case_id] = True
    missing_steps = [case_id for case_id, has_step in case_has_step.items() if not has_step]
    if missing_steps:
        raise ValueError(f"Cases without steps: {missing_steps}")


def _requires_object_target(action_key: str, assert_key: str, target_type: str, target: str) -> bool:
    if not target:
        return False
    if target_type in {"route", "url", "api"}:
        return False
    if action_key in {"open_page", "wait_url"}:
        return False
    return True
