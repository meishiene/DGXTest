from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from src.artifacts.collector import PlaywrightRuntimeEvidence
from src.objects.playwright_locator import resolve_locator
from src.objects.resolver import ObjectRepositoryResolver, ResolvedObject
from src.parser.models import StepRecord
from src.utils.data_resolver import CaseExecutionData


SUPPORTED_ASSERT_KEYS = frozenset(
    {
        "assert_url_contains",
        "assert_url_equals",
        "assert_text_contains",
        "assert_text_equals",
        "assert_element_visible",
        "assert_element_hidden",
        "assert_element_enabled",
        "assert_count_equals",
        "assert_api_called",
        "assert_api_status",
        "assert_value_equals",
    }
)


@dataclass(slots=True)
class AssertExecutionResult:
    page_url: str
    resolved_object: ResolvedObject | None
    actual_value: str


class AssertExecutor:
    def __init__(self, resolver: ObjectRepositoryResolver, runtime_evidence: PlaywrightRuntimeEvidence | None = None) -> None:
        self._resolver = resolver
        self._runtime_evidence = runtime_evidence

    def execute(
        self,
        page: Page,
        step: StepRecord,
        case_data: CaseExecutionData,
        base_url: str,
        timeout_ms: int,
    ) -> AssertExecutionResult:
        assert_key = step.assert_key
        expected_value = case_data.resolve_text(step.expected)

        if assert_key == "assert_url_contains":
            if expected_value not in page.url:
                raise AssertionError(f"URL assertion failed: expected contains={expected_value}, actual={page.url}")
            return AssertExecutionResult(page_url=page.url, resolved_object=None, actual_value=page.url)

        if assert_key == "assert_url_equals":
            if expected_value != page.url:
                raise AssertionError(f"URL assertion failed: expected={expected_value}, actual={page.url}")
            return AssertExecutionResult(page_url=page.url, resolved_object=None, actual_value=page.url)

        if assert_key in {"assert_text_contains", "assert_text_equals"}:
            locator, resolved_object, effective_timeout = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
            )
            actual_value = locator.text_content(timeout=effective_timeout) or ""
            if assert_key == "assert_text_contains" and expected_value not in actual_value:
                raise AssertionError(f"Text assertion failed: expected contains={expected_value}, actual={actual_value}")
            if assert_key == "assert_text_equals" and expected_value != actual_value:
                raise AssertionError(f"Text assertion failed: expected={expected_value}, actual={actual_value}")
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=actual_value)

        if assert_key == "assert_element_visible":
            locator, resolved_object, effective_timeout = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
            )
            try:
                locator.wait_for(state="visible", timeout=effective_timeout)
            except Exception as exc:
                raise AssertionError(f"Element did not become visible in time: target={step.target}") from exc
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="visible")

        if assert_key == "assert_element_hidden":
            locator, resolved_object, effective_timeout = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
                wait_for_attached=False,
            )
            try:
                locator.wait_for(state="hidden", timeout=effective_timeout)
            except Exception as exc:
                raise AssertionError(f"Element did not become hidden in time: target={step.target}") from exc
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="hidden")

        if assert_key == "assert_element_enabled":
            locator, resolved_object, effective_timeout = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
            )
            try:
                locator.wait_for(state="visible", timeout=effective_timeout)
                is_enabled = locator.is_enabled(timeout=effective_timeout)
            except Exception as exc:
                raise AssertionError(f"Element enablement assertion failed: target={step.target}") from exc
            if not is_enabled:
                raise AssertionError(f"Element is disabled: target={step.target}")
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="enabled")

        if assert_key == "assert_count_equals":
            locator, resolved_object, _ = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
            )
            try:
                expected_count = int(expected_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"assert_count_equals requires integer expected value: {expected_value}") from exc

            actual_count = locator.count()
            if actual_count != expected_count:
                raise AssertionError(f"Count assertion failed: expected={expected_count}, actual={actual_count}")
            return AssertExecutionResult(
                page_url=page.url,
                resolved_object=resolved_object,
                actual_value=str(actual_count),
            )

        if assert_key == "assert_api_called":
            endpoint = case_data.resolve_text(step.target).strip() or expected_value.strip()
            if not endpoint:
                raise ValueError("assert_api_called requires target or expected to define the API URL/path")

            match_type = (step.match_type or "contains").strip().lower() or "contains"
            if match_type not in {"contains", "equals"}:
                raise ValueError(f"assert_api_called supports only contains/equals match_type: {step.match_type}")

            method = case_data.resolve_text(step.value).strip().upper()
            matching_request = _find_matching_request(
                runtime_evidence=self._runtime_evidence,
                endpoint=endpoint,
                method=method,
                match_type=match_type,
                base_url=base_url,
            )
            if matching_request is None:
                observed = _summarize_requests(self._runtime_evidence)
                method_suffix = f", method={method}" if method else ""
                raise AssertionError(
                    f"API call assertion failed: expected {match_type}={endpoint}{method_suffix}, observed={observed}"
                )
            return AssertExecutionResult(
                page_url=page.url,
                resolved_object=None,
                actual_value=str(matching_request.get("url", "")),
            )

        if assert_key == "assert_api_status":
            endpoint = case_data.resolve_text(step.target).strip()
            if not endpoint:
                raise ValueError("assert_api_status requires target to define the API URL/path")

            try:
                expected_status = int(expected_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"assert_api_status requires integer expected value: {expected_value}") from exc

            match_type = (step.match_type or "contains").strip().lower() or "contains"
            if match_type not in {"contains", "equals"}:
                raise ValueError(f"assert_api_status supports only contains/equals match_type: {step.match_type}")

            method = case_data.resolve_text(step.value).strip().upper()
            matching_response = _find_matching_response(
                runtime_evidence=self._runtime_evidence,
                endpoint=endpoint,
                method=method,
                match_type=match_type,
                base_url=base_url,
            )
            if matching_response is None:
                observed = _summarize_responses(self._runtime_evidence)
                method_suffix = f", method={method}" if method else ""
                raise AssertionError(
                    f"API status assertion failed: no matching response for {match_type}={endpoint}{method_suffix}, observed={observed}"
                )

            actual_status = _coerce_status_code(matching_response.get("status", ""))
            if actual_status != expected_status:
                raise AssertionError(
                    f"API status assertion failed: expected={expected_status}, actual={actual_status}, url={matching_response.get('url', '')}"
                )
            return AssertExecutionResult(
                page_url=page.url,
                resolved_object=None,
                actual_value=str(actual_status),
            )

        if assert_key == "assert_value_equals":
            locator, resolved_object, effective_timeout = self._resolve_assert_locator(
                page=page,
                step=step,
                timeout_ms=timeout_ms,
            )
            actual_value = _read_element_value(locator, effective_timeout)
            if actual_value != expected_value:
                raise AssertionError(f"Value assertion failed: expected={expected_value}, actual={actual_value}")
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=actual_value)

        raise ValueError(f"Unsupported assert_key in runtime executor: {assert_key}")

    def _resolve_assert_locator(
        self,
        page: Page,
        step: StepRecord,
        timeout_ms: int,
        wait_for_attached: bool = True,
    ) -> tuple[Any, ResolvedObject, int]:
        locator, resolved_object = resolve_locator(
            page=page,
            resolver=self._resolver,
            object_key=step.target,
            timeout_ms=timeout_ms,
            wait_for_attached=wait_for_attached,
        )
        effective_timeout = _resolve_timeout_ms(step.timeout, resolved_object, timeout_ms)
        return locator, resolved_object, effective_timeout


def _read_element_value(locator: Any, timeout_ms: int) -> str:
    try:
        return locator.input_value(timeout=timeout_ms)
    except Exception:
        value = locator.get_attribute("value", timeout=timeout_ms)
        return value or ""


def _resolve_timeout_ms(
    step_timeout_sec: int,
    resolved_object: ResolvedObject | None,
    default_timeout_ms: int,
) -> int:
    if step_timeout_sec:
        return step_timeout_sec * 1000
    if resolved_object and resolved_object.default_timeout_sec:
        return resolved_object.default_timeout_sec * 1000
    return default_timeout_ms


def _find_matching_request(
    runtime_evidence: PlaywrightRuntimeEvidence | None,
    endpoint: str,
    method: str,
    match_type: str,
    base_url: str,
) -> dict[str, Any] | None:
    for entry in _request_entries(runtime_evidence):
        request_method = str(entry.get("method", "")).strip().upper()
        request_url = str(entry.get("url", "")).strip()
        if method and request_method != method:
            continue
        if _request_url_matches(request_url=request_url, endpoint=endpoint, match_type=match_type, base_url=base_url):
            return entry
    return None


def _request_entries(runtime_evidence: PlaywrightRuntimeEvidence | None) -> list[dict[str, Any]]:
    if runtime_evidence is None:
        return []
    return [entry for entry in runtime_evidence.network_snapshot() if str(entry.get("event", "")).lower() == "request"]


def _request_url_matches(request_url: str, endpoint: str, match_type: str, base_url: str) -> bool:
    candidates = [endpoint]
    if endpoint.startswith("/") and base_url:
        candidates.append(base_url.rstrip("/") + endpoint)
    if match_type == "equals":
        return request_url in candidates
    return any(candidate in request_url for candidate in candidates)


def _summarize_requests(runtime_evidence: PlaywrightRuntimeEvidence | None) -> str:
    requests = _request_entries(runtime_evidence)
    if not requests:
        return "no captured request events"
    preview = "; ".join(
        f"{entry.get('method', '').strip().upper()} {entry.get('url', '')}".strip()
        for entry in requests[:3]
    )
    if len(requests) > 3:
        preview += f"; ... ({len(requests)} total)"
    return preview


def _find_matching_response(
    runtime_evidence: PlaywrightRuntimeEvidence | None,
    endpoint: str,
    method: str,
    match_type: str,
    base_url: str,
) -> dict[str, Any] | None:
    for entry in _response_entries(runtime_evidence):
        response_method = str(entry.get("method", "")).strip().upper()
        response_url = str(entry.get("url", "")).strip()
        if method and response_method != method:
            continue
        if _request_url_matches(request_url=response_url, endpoint=endpoint, match_type=match_type, base_url=base_url):
            return entry
    return None


def _response_entries(runtime_evidence: PlaywrightRuntimeEvidence | None) -> list[dict[str, Any]]:
    if runtime_evidence is None:
        return []
    return [entry for entry in runtime_evidence.network_snapshot() if str(entry.get("event", "")).lower() == "response"]


def _coerce_status_code(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise AssertionError(f"API status assertion failed: response status is invalid: {value}") from exc


def _summarize_responses(runtime_evidence: PlaywrightRuntimeEvidence | None) -> str:
    responses = _response_entries(runtime_evidence)
    if not responses:
        return "no captured response events"
    preview = "; ".join(
        f"{entry.get('method', '').strip().upper()} {entry.get('url', '')} -> {entry.get('status', '')}".strip()
        for entry in responses[:3]
    )
    if len(responses) > 3:
        preview += f"; ... ({len(responses)} total)"
    return preview
