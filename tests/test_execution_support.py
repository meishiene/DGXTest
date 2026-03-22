from pathlib import Path

from src.core.bootstrap import prepare_run_context
from src.parser.excel_parser import parse_object_repository, parse_test_workbook
from src.parser.template_generator import generate_excel_templates
from src.results.models import AppConfig
from src.runner.playwright_runner import execute_run


def test_object_repository_and_data_resolver(tmp_path: Path) -> None:
    test_workbook = tmp_path / "test_suite_template.xlsx"
    object_workbook = tmp_path / "object_repository_template.xlsx"
    generate_excel_templates(test_workbook, object_workbook)

    suite = parse_test_workbook(test_workbook)
    repository = parse_object_repository(object_workbook)

    placeholder_steps = [step for step in suite.steps if step.step_type == "assert" and not step.assert_key]
    assert len(placeholder_steps) == 5
    assert placeholder_steps[0].step_name == "Assert project workspace opened (placeholder)"


def test_dry_run_skips_placeholder_assertions(tmp_path: Path) -> None:
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

    assert len(case_results) == 1
    skipped_steps = [step for step in step_results if step.status == "SKIPPED"]
    assert len(skipped_steps) == 2
    assert all(step.actual == "Assertion placeholder left empty in Excel" for step in skipped_steps)
