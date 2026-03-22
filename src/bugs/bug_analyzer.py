from __future__ import annotations

from collections import defaultdict

from src.results.models import ArtifactRecord, BugCaseLink, BugRecord, CaseResult, StepResult


def build_bug_records(
    case_results: list[CaseResult],
    step_results: list[StepResult],
    artifacts: list[ArtifactRecord],
) -> tuple[list[BugRecord], list[BugCaseLink]]:
    failed_cases = [item for item in case_results if item.status == "FAILED" and item.bug_candidate]
    groups: dict[str, list[CaseResult]] = defaultdict(list)
    for case_result in failed_cases:
        groups[case_result.dedup_key or f"fallback|{case_result.case_id}"].append(case_result)

    bugs: list[BugRecord] = []
    links: list[BugCaseLink] = []

    for index, (dedup_key, grouped_cases) in enumerate(groups.items(), start=1):
        primary_case = grouped_cases[0]
        bug_id = f"BUG-{index:04d}"
        bug = BugRecord(
            bug_id=bug_id,
            run_id=primary_case.run_id,
            title=_build_bug_title(primary_case),
            module=primary_case.module,
            sub_module=primary_case.sub_module,
            severity="S2" if primary_case.priority == "P1" else "S3",
            priority=primary_case.priority,
            status="NEW",
            root_cause_category=primary_case.failure_category or "UNKNOWN",
            suspected_layer=primary_case.suspected_layer or "unknown",
            affected_case_ids=[item.case_id for item in grouped_cases],
            affected_case_count=len(grouped_cases),
            dedup_key=dedup_key,
            expected_result=primary_case.expected_summary,
            actual_result=primary_case.actual_summary,
            failed_step_no=primary_case.failed_step_no,
            failed_step_name=primary_case.failed_step_name,
            artifact_ids=primary_case.artifact_ids,
        )
        bugs.append(bug)

        for item in grouped_cases:
            item.bug_id = bug_id
            links.append(
                BugCaseLink(
                    bug_id=bug_id,
                    run_id=item.run_id,
                    case_id=item.case_id,
                    case_result_id=item.case_result_id,
                    failed_step_no=item.failed_step_no,
                    failed_step_name=item.failed_step_name,
                    is_primary_case=item.case_id == primary_case.case_id,
                )
            )

        for artifact in artifacts:
            if artifact.case_id == primary_case.case_id:
                artifact.bug_id = bug_id

    return bugs, links


def _build_bug_title(case_result: CaseResult) -> str:
    if case_result.failed_step_name:
        return f"{case_result.module} - {case_result.failed_step_name} 执行失败"
    return f"{case_result.module} - {case_result.case_name} 执行失败"
