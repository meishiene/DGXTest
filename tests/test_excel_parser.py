from pathlib import Path

from src.parser.excel_parser import parse_object_repository, parse_test_workbook
from src.parser.template_generator import generate_excel_templates
from src.validator.excel_validator import validate_parsed_workbooks


def test_generate_and_parse_templates(tmp_path: Path) -> None:
    test_workbook = tmp_path / "test_suite_template.xlsx"
    object_workbook = tmp_path / "object_repository_template.xlsx"

    generate_excel_templates(test_workbook, object_workbook)

    suite = parse_test_workbook(test_workbook)
    repository = parse_object_repository(object_workbook)
    validate_parsed_workbooks(suite, repository)

    assert len(suite.cases) == 2
    assert len(suite.steps) == 28
    assert len(suite.test_data) == 1
    assert len(repository.pages) == 2
    assert len(repository.objects) == 14
    assert suite.cases[0].case_id == "DGX_001"
    assert suite.steps[0].step_name == "Open DGX demo landing page"
    assert suite.steps[3].step_type == "assert"
    assert suite.steps[3].assert_key == ""
    assert "placeholder" in suite.steps[3].remark.lower()
    assert repository.objects[0].object_key == "project_card_entry_button"
