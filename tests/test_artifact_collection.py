import json
from pathlib import Path
from types import SimpleNamespace

from src.artifacts.collector import (
    PlaywrightRuntimeEvidence,
    capture_playwright_failure_artifacts,
    create_dry_run_failure_artifacts,
)
from src.core.bootstrap import prepare_run_context
from src.results.models import AppConfig


def test_capture_playwright_failure_artifacts_includes_console_and_network_logs(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="artifact_capture",
        trigger_by="tester",
        base_url="https://example.com",
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    page = _FakeArtifactPage()
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.attach(page)

    page.emit(
        "console",
        SimpleNamespace(
            type="error",
            text="Uncaught TypeError: boom",
            location={"url": "https://example.com/app.js", "lineNumber": 12, "columnNumber": 8},
        ),
    )
    page.emit("pageerror", RuntimeError("ReferenceError: state is not defined"))
    page.emit(
        "request",
        SimpleNamespace(method="POST", url="https://example.com/api/run", resource_type="xhr"),
    )
    page.emit(
        "response",
        SimpleNamespace(
            request=SimpleNamespace(method="POST", resource_type="xhr"),
            url="https://example.com/api/run",
            status=500,
            status_text="Internal Server Error",
            ok=False,
        ),
    )

    artifacts = capture_playwright_failure_artifacts(
        run_context=run_context,
        run_id=run_context.run_id,
        case_id="CASE_FAIL",
        step_result_id="SR_RUN_CASE_FAIL_01",
        page=page,
        runtime_evidence=runtime_evidence,
    )

    assert [artifact.artifact_type for artifact in artifacts] == [
        "screenshot",
        "dom_snapshot",
        "console_log",
        "network_log",
    ]
    assert all("SR_RUN_CASE_FAIL_01" in artifact.file_path for artifact in artifacts)
    assert page.screenshot_calls == [(artifacts[0].file_path, True)]

    console_content = Path(artifacts[2].file_path).read_text(encoding="utf-8")
    assert "Uncaught TypeError: boom" in console_content
    assert "ReferenceError: state is not defined" in console_content

    network_payload = json.loads(Path(artifacts[3].file_path).read_text(encoding="utf-8"))
    entries = network_payload["log"]["entries"]
    assert entries[0]["event"] == "request"
    assert entries[1]["event"] == "response"
    assert entries[1]["status"] == 500


def test_failure_artifact_capture_respects_capture_flags(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="artifact_capture",
        trigger_by="tester",
        base_url="https://example.com",
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)
    page = _FakeArtifactPage()
    runtime_evidence = PlaywrightRuntimeEvidence()
    runtime_evidence.attach(page)

    artifacts = capture_playwright_failure_artifacts(
        run_context=run_context,
        run_id=run_context.run_id,
        case_id="CASE_FAIL",
        step_result_id="SR_RUN_CASE_FAIL_02",
        page=page,
        runtime_evidence=runtime_evidence,
        capture_screenshot=False,
        capture_dom_snapshot=True,
        capture_console_log=False,
        capture_network_log=True,
    )

    assert [artifact.artifact_type for artifact in artifacts] == ["dom_snapshot", "network_log"]
    assert page.screenshot_calls == []


def test_create_dry_run_failure_artifacts_uses_step_result_id_for_unique_paths(tmp_path: Path) -> None:
    config = AppConfig(
        project_name="DGX Web Auto Test",
        suite_name="artifact_capture",
        trigger_by="tester",
        base_url="https://example.com",
        output_root=str(tmp_path / "outputs"),
    )
    run_context = prepare_run_context(config)

    first_attempt_artifacts = create_dry_run_failure_artifacts(
        run_context=run_context,
        run_id=run_context.run_id,
        case_id="CASE_FAIL",
        step_result_id="SR_RUN_CASE_FAIL_01",
    )
    second_attempt_artifacts = create_dry_run_failure_artifacts(
        run_context=run_context,
        run_id=run_context.run_id,
        case_id="CASE_FAIL",
        step_result_id="SR_RUN_CASE_FAIL_01_A02",
    )

    assert {artifact.file_path for artifact in first_attempt_artifacts}.isdisjoint(
        {artifact.file_path for artifact in second_attempt_artifacts}
    )
    assert {artifact.artifact_id for artifact in first_attempt_artifacts}.isdisjoint(
        {artifact.artifact_id for artifact in second_attempt_artifacts}
    )


def test_runtime_evidence_allows_playwright_internal_handler_binding() -> None:
    runtime_evidence = PlaywrightRuntimeEvidence()
    setattr(runtime_evidence, "_pw_impl_instance__handle_console_message", object())
    assert hasattr(runtime_evidence, "_pw_impl_instance__handle_console_message")

class _FakeArtifactPage:
    def __init__(self) -> None:
        self.url = "https://example.com/failure"
        self._handlers: dict[str, list] = {}
        self.screenshot_calls: list[tuple[str, bool]] = []

    def on(self, event_name: str, handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def emit(self, event_name: str, payload) -> None:
        for handler in self._handlers.get(event_name, []):
            handler(payload)

    def screenshot(self, path: str, full_page: bool) -> None:
        self.screenshot_calls.append((path, full_page))
        Path(path).write_bytes(b"fake-png")

    def content(self) -> str:
        return "<html><body>failure snapshot</body></html>"
