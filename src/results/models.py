from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AppConfig:
    project_name: str
    suite_name: str
    trigger_by: str
    base_url: str
    browser: str = "chromium"
    headless: bool = True
    dry_run: bool = True
    demo_failure: bool = True
    output_root: str = "outputs"
    capture_screenshot: bool = True
    capture_dom_snapshot: bool = True
    capture_console_log: bool = True
    capture_network_log: bool = True
    capture_video: bool = False
    generate_bug_report: bool = True
    generate_ai_bug_doc: bool = True
    timeout_ms: int = 10000
    run_id: str = ""
    test_workbook_path: str = "excels/test_suite_template.xlsx"
    object_repository_path: str = "object_repo/object_repository_template.xlsx"


@dataclass(slots=True)
class ExecutionSummary:
    total_cases: int
    passed_cases: int
    failed_cases: int
    blocked_cases: int
    skipped_cases: int
    not_run_cases: int
    bug_count: int = 0

    @classmethod
    def from_case_results(cls, case_results: list["CaseResult"]) -> "ExecutionSummary":
        total_cases = len(case_results)
        passed_cases = sum(1 for item in case_results if item.status == "PASSED")
        failed_cases = sum(1 for item in case_results if item.status == "FAILED")
        blocked_cases = sum(1 for item in case_results if item.status == "BLOCKED")
        skipped_cases = sum(1 for item in case_results if item.status == "SKIPPED")
        not_run_cases = sum(1 for item in case_results if item.status == "NOT_RUN")
        return cls(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            blocked_cases=blocked_cases,
            skipped_cases=skipped_cases,
            not_run_cases=not_run_cases,
        )


@dataclass(slots=True)
class RunInfo:
    run_id: str
    project_name: str
    suite_name: str
    trigger_by: str
    start_time: str
    end_time: str
    duration_sec: int
    environment: str
    base_url: str
    browser: str
    headless: bool
    execution_summary: ExecutionSummary


@dataclass(slots=True)
class StepResult:
    step_result_id: str
    run_id: str
    case_id: str
    step_no: int
    step_type: str
    step_name: str
    status: str
    action_key: str = ""
    assert_key: str = ""
    target: str = ""
    page_name: str = ""
    expected: str = ""
    actual: str = ""
    error_type: str = ""
    error_message: str = ""
    page_url: str = ""
    locator_used_type: str = ""
    locator_used_value: str = ""
    component_hint: str = ""
    frontend_file_hint: str = ""
    api_hint: str = ""


@dataclass(slots=True)
class CaseResult:
    case_result_id: str
    run_id: str
    case_id: str
    case_name: str
    module: str
    sub_module: str
    priority: str
    status: str
    failure_category: str
    expected_summary: str
    actual_summary: str
    failed_step_no: int = 0
    failed_step_name: str = ""
    failure_message: str = ""
    bug_candidate: bool = False
    dedup_key: str = ""
    artifact_ids: list[str] = field(default_factory=list)
    suspected_layer: str = ""
    bug_id: str = ""


@dataclass(slots=True)
class ArtifactRecord:
    artifact_id: str
    run_id: str
    case_id: str
    step_result_id: str
    artifact_type: str
    file_path: str
    description: str = ""
    bug_id: str = ""


@dataclass(slots=True)
class BugRecord:
    bug_id: str
    run_id: str
    title: str
    module: str
    sub_module: str
    severity: str
    priority: str
    status: str
    root_cause_category: str
    suspected_layer: str
    affected_case_ids: list[str]
    affected_case_count: int
    dedup_key: str
    expected_result: str
    actual_result: str
    failed_step_no: int
    failed_step_name: str
    ai_bug_doc_path: str = ""
    artifact_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BugCaseLink:
    bug_id: str
    run_id: str
    case_id: str
    case_result_id: str
    failed_step_no: int
    failed_step_name: str
    is_primary_case: bool


@dataclass(slots=True)
class GenerationOutputs:
    manifest_path: str
    test_report_html: str
    case_results_excel: str
    bug_list_excel: str
    ai_bug_docs_dir: str
    artifacts_dir: str


@dataclass(slots=True)
class RunManifest:
    run_info: RunInfo
    execution_summary: ExecutionSummary
    case_results: list[CaseResult]
    step_results: list[StepResult]
    artifacts: list[ArtifactRecord]
    bugs: list[BugRecord]
    bug_case_links: list[BugCaseLink]
    generation_outputs: GenerationOutputs
