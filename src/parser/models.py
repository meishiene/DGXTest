from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CaseRecord:
    case_id: str
    case_name: str
    module: str
    sub_module: str
    feature_name: str
    priority: str
    test_level: str
    tags: list[str]
    status: str
    automation_flag: str
    data_set_id: str
    preconditions: str
    expected_result_summary: str
    owner: str
    env_scope: list[str]
    browser_scope: list[str]
    can_parallel: str
    retry_policy: str = ""
    require_login: str = ""
    depends_on_case: str = ""
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class StepRecord:
    case_id: str
    step_no: int
    step_type: str
    step_name: str
    action_key: str
    assert_key: str
    page_name: str
    target: str
    target_type: str
    value: str
    value_type: str
    expected: str
    expected_type: str
    match_type: str
    wait: str
    timeout: int
    continue_on_fail: str
    screenshot_on_fail: str
    ai_locator_hint: str
    remark: str
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TestDataRecord:
    data_set_id: str
    data_name: str
    module: str
    env: str
    payload: dict[str, str]
    remark: str


@dataclass(slots=True)
class DictionaryRecord:
    dict_type: str
    dict_value: str
    dict_label: str
    enabled: str
    remark: str


@dataclass(slots=True)
class PageRecord:
    page_name: str
    module: str
    sub_module: str
    route: str
    page_title: str
    load_wait_strategy: str
    load_timeout_sec: int
    frontend_hint: str
    api_group_hint: str
    status: str
    remark: str


@dataclass(slots=True)
class ObjectRecord:
    object_key: str
    object_name: str
    page_name: str
    module: str
    sub_module: str
    object_type: str
    locator_primary_type: str
    locator_primary_value: str
    locator_backup_1_type: str
    locator_backup_1_value: str
    locator_backup_2_type: str
    locator_backup_2_value: str
    default_wait: str
    default_timeout_sec: int
    ai_component_hint: str
    frontend_file_hint: str
    api_hint: str
    enabled: str
    remark: str


@dataclass(slots=True)
class ParsedTestSuite:
    cases: list[CaseRecord]
    steps: list[StepRecord]
    test_data: list[TestDataRecord]
    run_config_rows: list[dict[str, str]]
    dictionaries: list[DictionaryRecord]


@dataclass(slots=True)
class ParsedObjectRepository:
    pages: list[PageRecord]
    objects: list[ObjectRecord]
