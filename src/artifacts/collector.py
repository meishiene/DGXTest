from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from src.core.bootstrap import RunContext
from src.results.models import ArtifactRecord


_TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAusB9Y9q24wAAAAASUVORK5CYII="
)


def _write_placeholder_png(path: Path) -> None:
    path.write_bytes(base64.b64decode(_TINY_PNG))


def create_dry_run_failure_artifacts(
    run_context: RunContext,
    run_id: str,
    case_id: str,
    step_result_id: str,
    bug_id: str = "",
) -> list[ArtifactRecord]:
    screenshot_path = run_context.screenshots_dir / f"{case_id}_failure.png"
    dom_path = run_context.html_snapshots_dir / f"{case_id}_failure.html"
    console_path = run_context.console_logs_dir / f"{case_id}_failure.log"
    network_path = run_context.network_logs_dir / f"{case_id}_failure.har"

    _write_placeholder_png(screenshot_path)
    dom_path.write_text(
        "<html><body><h1>Dry Run Failure Snapshot</h1><button>登录</button></body></html>",
        encoding="utf-8",
    )
    console_path.write_text(
        "TypeError: Cannot read properties of undefined (reading 'trim')",
        encoding="utf-8",
    )
    network_path.write_text('{"log": {"entries": []}}', encoding="utf-8")

    return [
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_SCREENSHOT",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="screenshot",
            file_path=str(screenshot_path),
            description="dry-run 失败截图",
        ),
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_DOM",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="dom_snapshot",
            file_path=str(dom_path),
            description="dry-run DOM 快照",
        ),
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_CONSOLE",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="console_log",
            file_path=str(console_path),
            description="dry-run 控制台日志",
        ),
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_NETWORK",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="network_log",
            file_path=str(network_path),
            description="dry-run 网络日志",
        ),
    ]


def capture_playwright_failure_artifacts(
    run_context: RunContext,
    run_id: str,
    case_id: str,
    step_result_id: str,
    page: Any,
    bug_id: str = "",
) -> list[ArtifactRecord]:
    screenshot_path = run_context.screenshots_dir / f"{case_id}_failure.png"
    dom_path = run_context.html_snapshots_dir / f"{case_id}_failure.html"

    page.screenshot(path=str(screenshot_path), full_page=True)
    dom_path.write_text(page.content(), encoding="utf-8")

    return [
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_SCREENSHOT",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="screenshot",
            file_path=str(screenshot_path),
            description="真实执行失败截图",
        ),
        ArtifactRecord(
            artifact_id=f"ART_{case_id}_DOM",
            run_id=run_id,
            case_id=case_id,
            step_result_id=step_result_id,
            bug_id=bug_id,
            artifact_type="dom_snapshot",
            file_path=str(dom_path),
            description="真实执行 DOM 快照",
        ),
    ]
