from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.bootstrap import RunContext
from src.results.models import ArtifactRecord


_TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAusB9Y9q24wAAAAASUVORK5CYII="
)


@dataclass
class PlaywrightRuntimeEvidence:
    capture_console_log: bool = True
    capture_network_log: bool = True
    console_entries: list[dict[str, Any]] = field(default_factory=list)
    network_entries: list[dict[str, Any]] = field(default_factory=list)
    _attached: bool = False

    def attach(self, page: Any) -> None:
        if self._attached or not hasattr(page, "on"):
            return
        if self.capture_console_log:
            page.on("console", self._handle_console_message)
            page.on("pageerror", self._handle_page_error)
        if self.capture_network_log:
            page.on("request", self._handle_request)
            page.on("response", self._handle_response)
            page.on("requestfailed", self._handle_request_failed)
        self._attached = True

    def reset(self) -> None:
        self.console_entries.clear()
        self.network_entries.clear()

    def console_snapshot(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self.console_entries]

    def network_snapshot(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self.network_entries]

    def _handle_console_message(self, message: Any) -> None:
        location = _safe_read_attr(message, "location", {})
        if callable(location):
            location = location()
        location = location or {}
        self.console_entries.append(
            {
                "type": str(_safe_read_attr(message, "type", "console")),
                "text": str(_safe_read_attr(message, "text", "")),
                "url": str(location.get("url", "")),
                "line": str(location.get("lineNumber", "")),
                "column": str(location.get("columnNumber", "")),
            }
        )

    def _handle_page_error(self, error: Any) -> None:
        self.console_entries.append(
            {
                "type": "pageerror",
                "text": str(error),
                "url": "",
                "line": "",
                "column": "",
            }
        )

    def _handle_request(self, request: Any) -> None:
        self.network_entries.append(
            {
                "event": "request",
                "method": str(_safe_read_attr(request, "method", "")),
                "url": str(_safe_read_attr(request, "url", "")),
                "resource_type": str(_safe_read_attr(request, "resource_type", "")),
            }
        )

    def _handle_response(self, response: Any) -> None:
        request = _safe_read_attr(response, "request", None)
        self.network_entries.append(
            {
                "event": "response",
                "method": str(_safe_read_attr(request, "method", "")),
                "url": str(_safe_read_attr(response, "url", "")),
                "resource_type": str(_safe_read_attr(request, "resource_type", "")),
                "status": _safe_read_attr(response, "status", ""),
                "status_text": str(_safe_read_attr(response, "status_text", "")),
                "ok": bool(_safe_read_attr(response, "ok", False)),
            }
        )

    def _handle_request_failed(self, request: Any) -> None:
        failure = _safe_read_attr(request, "failure", None)
        error_text = ""
        if failure is not None:
            error_text = str(_safe_read_attr(failure, "error_text", ""))
        self.network_entries.append(
            {
                "event": "requestfailed",
                "method": str(_safe_read_attr(request, "method", "")),
                "url": str(_safe_read_attr(request, "url", "")),
                "resource_type": str(_safe_read_attr(request, "resource_type", "")),
                "failure": error_text,
            }
        )


def _safe_read_attr(value: Any, name: str, default: Any) -> Any:
    if value is None:
        return default
    attr = getattr(value, name, default)
    return attr() if callable(attr) else attr


def _write_placeholder_png(path: Path) -> None:
    path.write_bytes(base64.b64decode(_TINY_PNG))


def _build_artifact_stem(step_result_id: str) -> str:
    return step_result_id


def _build_artifact_record(
    *,
    run_id: str,
    case_id: str,
    step_result_id: str,
    artifact_type: str,
    file_path: Path,
    description: str,
    bug_id: str,
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=f"ART_{step_result_id}_{artifact_type.upper()}",
        run_id=run_id,
        case_id=case_id,
        step_result_id=step_result_id,
        bug_id=bug_id,
        artifact_type=artifact_type,
        file_path=str(file_path),
        description=description,
    )


def _write_console_log(path: Path, entries: list[dict[str, Any]]) -> None:
    if not entries:
        path.write_text("No console events captured.", encoding="utf-8")
        return
    lines = []
    for entry in entries:
        location_suffix = ""
        if entry.get("url"):
            location_suffix = f" @ {entry['url']}"
            if entry.get("line"):
                location_suffix += f":{entry['line']}"
                if entry.get("column"):
                    location_suffix += f":{entry['column']}"
        lines.append(f"[{entry.get('type', 'console')}] {entry.get('text', '')}{location_suffix}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_network_log(path: Path, entries: list[dict[str, Any]]) -> None:
    payload = {"log": {"entries": entries}}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_dry_run_failure_artifacts(
    run_context: RunContext,
    run_id: str,
    case_id: str,
    step_result_id: str,
    capture_screenshot: bool = True,
    capture_dom_snapshot: bool = True,
    capture_console_log: bool = True,
    capture_network_log: bool = True,
    bug_id: str = "",
) -> list[ArtifactRecord]:
    artifact_stem = _build_artifact_stem(step_result_id)
    artifacts: list[ArtifactRecord] = []

    if capture_screenshot:
        screenshot_path = run_context.screenshots_dir / f"{artifact_stem}_failure.png"
        _write_placeholder_png(screenshot_path)
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="screenshot",
                file_path=screenshot_path,
                description="dry-run 失败截图",
                bug_id=bug_id,
            )
        )

    if capture_dom_snapshot:
        dom_path = run_context.html_snapshots_dir / f"{artifact_stem}_failure.html"
        dom_path.write_text(
            "<html><body><h1>Dry Run Failure Snapshot</h1><button>登录</button></body></html>",
            encoding="utf-8",
        )
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="dom_snapshot",
                file_path=dom_path,
                description="dry-run DOM 快照",
                bug_id=bug_id,
            )
        )

    if capture_console_log:
        console_path = run_context.console_logs_dir / f"{artifact_stem}_failure.log"
        _write_console_log(
            console_path,
            [
                {
                    "type": "error",
                    "text": "TypeError: Cannot read properties of undefined (reading 'trim')",
                    "url": "",
                    "line": "",
                    "column": "",
                }
            ],
        )
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="console_log",
                file_path=console_path,
                description="dry-run 控制台日志",
                bug_id=bug_id,
            )
        )

    if capture_network_log:
        network_path = run_context.network_logs_dir / f"{artifact_stem}_failure.har"
        _write_network_log(network_path, [])
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="network_log",
                file_path=network_path,
                description="dry-run 网络日志",
                bug_id=bug_id,
            )
        )

    return artifacts


def capture_playwright_failure_artifacts(
    run_context: RunContext,
    run_id: str,
    case_id: str,
    step_result_id: str,
    page: Any,
    runtime_evidence: PlaywrightRuntimeEvidence | None = None,
    capture_screenshot: bool = True,
    capture_dom_snapshot: bool = True,
    capture_console_log: bool = True,
    capture_network_log: bool = True,
    bug_id: str = "",
) -> list[ArtifactRecord]:
    artifact_stem = _build_artifact_stem(step_result_id)
    artifacts: list[ArtifactRecord] = []

    if capture_screenshot:
        screenshot_path = run_context.screenshots_dir / f"{artifact_stem}_failure.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="screenshot",
                file_path=screenshot_path,
                description="真实执行失败截图",
                bug_id=bug_id,
            )
        )

    if capture_dom_snapshot:
        dom_path = run_context.html_snapshots_dir / f"{artifact_stem}_failure.html"
        dom_path.write_text(page.content(), encoding="utf-8")
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="dom_snapshot",
                file_path=dom_path,
                description="真实执行 DOM 快照",
                bug_id=bug_id,
            )
        )

    if capture_console_log:
        console_path = run_context.console_logs_dir / f"{artifact_stem}_failure.log"
        console_entries = runtime_evidence.console_snapshot() if runtime_evidence else []
        _write_console_log(console_path, console_entries)
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="console_log",
                file_path=console_path,
                description="真实执行控制台日志",
                bug_id=bug_id,
            )
        )

    if capture_network_log:
        network_path = run_context.network_logs_dir / f"{artifact_stem}_failure.har"
        network_entries = runtime_evidence.network_snapshot() if runtime_evidence else []
        _write_network_log(network_path, network_entries)
        artifacts.append(
            _build_artifact_record(
                run_id=run_id,
                case_id=case_id,
                step_result_id=step_result_id,
                artifact_type="network_log",
                file_path=network_path,
                description="真实执行网络日志",
                bug_id=bug_id,
            )
        )

    return artifacts
