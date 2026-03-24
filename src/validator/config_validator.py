from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from src.results.models import AppConfig


SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
PLACEHOLDER_HOST_MARKERS = ("example.com", "your-prod-host")


def validate_run_config(config: AppConfig, workspace_root: Path | None = None) -> None:
    workspace_root = workspace_root or Path.cwd()

    if not config.project_name.strip():
        raise ValueError("project_name 不能为空")
    if not config.suite_name.strip():
        raise ValueError("suite_name 不能为空")
    if not config.output_root.strip():
        raise ValueError("output_root 不能为空")
    if not config.trigger_by.strip():
        raise ValueError("trigger_by 不能为空")

    _validate_output_root(config.output_root, workspace_root)
    _validate_base_url(config.base_url, config.dry_run)

    if not config.dry_run and config.demo_failure:
        raise ValueError("正式运行时 demo_failure 必须为 false")
    if config.browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"browser 不支持: {config.browser}")
    if config.timeout_ms <= 0:
        raise ValueError("timeout_ms 必须大于 0")
    if not config.test_workbook_path.strip():
        raise ValueError("test_workbook_path 不能为空")
    if not config.object_repository_path.strip():
        raise ValueError("object_repository_path 不能为空")

    _validate_existing_path("test_workbook_path", config.test_workbook_path, workspace_root)
    _validate_existing_path("object_repository_path", config.object_repository_path, workspace_root)


def _validate_base_url(base_url: str, dry_run: bool) -> None:
    normalized = base_url.strip()
    if not normalized:
        raise ValueError("base_url 不能为空")

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"base_url 格式不合法: {base_url}")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError(f"base_url 不能包含 query / fragment / params: {base_url}")
    if parsed.path not in {"", "/"}:
        raise ValueError(f"base_url 必须是站点根地址，不应携带业务路径: {base_url}")

    hostname = (parsed.hostname or "").lower()
    if not dry_run and any(marker in hostname for marker in PLACEHOLDER_HOST_MARKERS):
        raise ValueError(
            f"base_url 仍是占位地址，请先替换为真实目标地址: {base_url}"
        )


def _validate_output_root(raw_path: str, workspace_root: Path) -> None:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    if candidate.exists() and candidate.is_file():
        raise ValueError(f"output_root 不能指向文件: {candidate}")


def _validate_existing_path(field_name: str, raw_path: str, workspace_root: Path) -> None:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    if not candidate.exists():
        raise ValueError(f"{field_name} 指向的文件不存在: {candidate}")
    if not candidate.is_file():
        raise ValueError(f"{field_name} 必须指向文件: {candidate}")
