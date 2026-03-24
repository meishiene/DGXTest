from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.parser.config_loader import load_run_config
from src.results.models import AppConfig
from src.validator.config_validator import validate_run_config


CONFIGS_DIR = Path("configs")
WORKSPACE_ROOT = Path.cwd()


def test_default_run_config_is_demo_dry_run() -> None:
    config = load_run_config(CONFIGS_DIR / "run_config.json")

    assert config.suite_name == "dgx_demo_dry_run"
    assert config.base_url == "https://dgx.xlook.ai"
    assert config.dry_run is True
    assert config.demo_failure is True


def test_live_demo_config_is_live_and_not_demo_failure() -> None:
    config = load_run_config(CONFIGS_DIR / "live_run_config.example.json")

    assert config.suite_name == "dgx_demo_live_smoke"
    assert config.base_url == "https://dgx.xlook.ai"
    assert config.dry_run is False
    assert config.demo_failure is False
    assert config.capture_console_log is True
    assert config.test_workbook_path == "excels/test_suite_template.xlsx"
    assert config.object_repository_path == "object_repo/object_repository_template.xlsx"


def test_prod_run_config_is_placeholder_live_template() -> None:
    config = load_run_config(CONFIGS_DIR / "prod_run_config.json")

    assert config.suite_name == "dgx_prod_live_smoke"
    assert config.base_url == "https://your-prod-host.example.com"
    assert config.dry_run is False
    assert config.demo_failure is False
    assert config.capture_console_log is True
    assert config.capture_network_log is True
    assert config.test_workbook_path == "excels/test_suite_template.xlsx"
    assert config.object_repository_path == "object_repo/object_repository_template.xlsx"


def test_validate_run_config_rejects_placeholder_live_host() -> None:
    config = load_run_config(CONFIGS_DIR / "prod_run_config.json")

    with pytest.raises(ValueError, match="base_url"):
        validate_run_config(config, workspace_root=WORKSPACE_ROOT)


def test_validate_run_config_allows_placeholder_host_in_forced_dry_run() -> None:
    config = load_run_config(CONFIGS_DIR / "prod_run_config.json")
    config.dry_run = True

    validate_run_config(config, workspace_root=WORKSPACE_ROOT)


def test_load_run_config_rejects_unknown_field(tmp_path: Path) -> None:
    config_path = tmp_path / "broken_config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_name": "DGX Web Auto Test",
                "suite_name": "broken_config",
                "trigger_by": "tester",
                "base_url": "https://dgx.xlook.ai",
                "unexpected_field": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="未知字段"):
        load_run_config(config_path)


def test_load_run_config_rejects_live_config_missing_explicit_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "live_config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_name": "DGX Web Auto Test",
                "suite_name": "live_missing_paths",
                "trigger_by": "tester",
                "base_url": "https://dgx.xlook.ai",
                "dry_run": False,
                "demo_failure": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="正式运行配置必须显式填写"):
        load_run_config(config_path)


def test_validate_run_config_rejects_missing_workbook_path(tmp_path: Path) -> None:
    object_repo = tmp_path / "object_repository_template.xlsx"
    object_repo.write_text("placeholder", encoding="utf-8")
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="broken_paths",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        output_root=str(tmp_path / "outputs"),
        test_workbook_path=str(tmp_path / "missing_suite.xlsx"),
        object_repository_path=str(object_repo),
    )

    with pytest.raises(ValueError, match="test_workbook_path"):
        validate_run_config(config, workspace_root=tmp_path)


def test_validate_run_config_rejects_invalid_base_url(tmp_path: Path) -> None:
    workbook = tmp_path / "test_suite_template.xlsx"
    object_repo = tmp_path / "object_repository_template.xlsx"
    workbook.write_text("placeholder", encoding="utf-8")
    object_repo.write_text("placeholder", encoding="utf-8")
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="broken_url",
        trigger_by="tester",
        base_url="dgx.xlook.ai",
        output_root=str(tmp_path / "outputs"),
        test_workbook_path=str(workbook),
        object_repository_path=str(object_repo),
    )

    with pytest.raises(ValueError, match="base_url"):
        validate_run_config(config, workspace_root=tmp_path)


def test_validate_run_config_rejects_base_url_with_path(tmp_path: Path) -> None:
    workbook = tmp_path / "test_suite_template.xlsx"
    object_repo = tmp_path / "object_repository_template.xlsx"
    workbook.write_text("placeholder", encoding="utf-8")
    object_repo.write_text("placeholder", encoding="utf-8")
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="broken_url_path",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai/dgx/demo",
        output_root=str(tmp_path / "outputs"),
        test_workbook_path=str(workbook),
        object_repository_path=str(object_repo),
    )

    with pytest.raises(ValueError, match="业务路径"):
        validate_run_config(config, workspace_root=tmp_path)


def test_validate_run_config_rejects_demo_failure_in_live_run(tmp_path: Path) -> None:
    workbook = tmp_path / "test_suite_template.xlsx"
    object_repo = tmp_path / "object_repository_template.xlsx"
    workbook.write_text("placeholder", encoding="utf-8")
    object_repo.write_text("placeholder", encoding="utf-8")
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="live_demo_failure",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        dry_run=False,
        demo_failure=True,
        output_root=str(tmp_path / "outputs"),
        test_workbook_path=str(workbook),
        object_repository_path=str(object_repo),
    )

    with pytest.raises(ValueError, match="demo_failure"):
        validate_run_config(config, workspace_root=tmp_path)


def test_validate_run_config_rejects_output_root_pointing_to_file(tmp_path: Path) -> None:
    workbook = tmp_path / "test_suite_template.xlsx"
    object_repo = tmp_path / "object_repository_template.xlsx"
    output_file = tmp_path / "outputs.txt"
    workbook.write_text("placeholder", encoding="utf-8")
    object_repo.write_text("placeholder", encoding="utf-8")
    output_file.write_text("placeholder", encoding="utf-8")
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="broken_output_root",
        trigger_by="tester",
        base_url="https://dgx.xlook.ai",
        output_root=str(output_file),
        test_workbook_path=str(workbook),
        object_repository_path=str(object_repo),
    )

    with pytest.raises(ValueError, match="output_root"):
        validate_run_config(config, workspace_root=tmp_path)
