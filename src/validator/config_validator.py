from __future__ import annotations

from pathlib import Path

from src.results.models import AppConfig


SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}


def validate_run_config(config: AppConfig) -> None:
    if not config.project_name.strip():
        raise ValueError("project_name 不能为空")
    if not config.suite_name.strip():
        raise ValueError("suite_name 不能为空")
    if not config.base_url.strip():
        raise ValueError("base_url 不能为空")
    if config.browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"browser 不支持: {config.browser}")
    if config.timeout_ms <= 0:
        raise ValueError("timeout_ms 必须大于 0")
    if not config.test_workbook_path.strip():
        raise ValueError("test_workbook_path 不能为空")
    if not config.object_repository_path.strip():
        raise ValueError("object_repository_path 不能为空")
