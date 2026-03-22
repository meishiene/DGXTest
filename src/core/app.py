from __future__ import annotations

from pathlib import Path

from src.bugs.bug_analyzer import build_bug_records
from src.core.bootstrap import prepare_run_context
from src.parser.config_loader import load_run_config
from src.parser.excel_parser import parse_object_repository, parse_test_workbook
from src.reports.report_generator import generate_output_artifacts
from src.results.manifest_writer import write_manifest
from src.results.models import RunManifest
from src.runner.playwright_runner import execute_run
from src.validator.config_validator import validate_run_config
from src.validator.excel_validator import validate_parsed_workbooks


def run_application(config_path: Path, force_dry_run: bool = False) -> int:
    config = load_run_config(config_path)
    if force_dry_run:
        config.dry_run = True

    validate_run_config(config)
    suite = parse_test_workbook(Path(config.test_workbook_path))
    repository = parse_object_repository(Path(config.object_repository_path))
    validate_parsed_workbooks(suite, repository)

    run_context = prepare_run_context(config)
    run_info, case_results, step_results, artifacts = execute_run(config, run_context, suite, repository)
    bugs, bug_case_links = build_bug_records(case_results, step_results, artifacts)
    run_info.execution_summary.bug_count = len(bugs)

    generation_outputs = generate_output_artifacts(
        config=config,
        run_context=run_context,
        run_info=run_info,
        case_results=case_results,
        step_results=step_results,
        artifacts=artifacts,
        bugs=bugs,
        bug_case_links=bug_case_links,
    )

    manifest = RunManifest(
        run_info=run_info,
        execution_summary=run_info.execution_summary,
        case_results=case_results,
        step_results=step_results,
        artifacts=artifacts,
        bugs=bugs,
        bug_case_links=bug_case_links,
        generation_outputs=generation_outputs,
    )
    write_manifest(run_context.manifest_path, manifest)

    print("运行完成")
    print(f"run_id: {run_info.run_id}")
    print(f"解析用例数: {len(suite.cases)}")
    print(f"解析步骤数: {len(suite.steps)}")
    print(f"解析对象数: {len(repository.objects)}")
    print(f"输出目录: {run_context.root_dir}")
    print(f"manifest: {run_context.manifest_path}")
    print(f"test_report: {generation_outputs.test_report_html}")

    return 0
