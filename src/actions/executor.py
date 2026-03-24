from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from src.objects.playwright_locator import resolve_locator
from src.objects.resolver import ObjectRepositoryResolver, ResolvedObject
from src.parser.models import StepRecord
from src.utils.data_resolver import CaseExecutionData


SUPPORTED_ACTION_KEYS = frozenset(
    {
        "open_page",
        "click",
        "hover",
        "press_key",
        "clear_and_input",
        "input_password",
        "input_text",
        "check",
        "uncheck",
        "wait_element",
        "wait_url",
        "select_option",
        "upload_file",
    }
)


@dataclass(slots=True)
class ActionExecutionResult:
    page_url: str
    resolved_object: ResolvedObject | None
    actual_value: str


class ActionExecutor:
    def __init__(self, resolver: ObjectRepositoryResolver) -> None:
        self._resolver = resolver

    def execute(
        self,
        page: Page,
        step: StepRecord,
        case_data: CaseExecutionData,
        base_url: str,
        timeout_ms: int,
    ) -> ActionExecutionResult:
        action_key = step.action_key

        if action_key == "open_page":
            target_url = _build_target_url(base_url, step.target)
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            return ActionExecutionResult(page_url=page.url, resolved_object=None, actual_value=page.url)

        if action_key == "wait_url":
            raw_target = step.target or case_data.resolve_text(step.value)
            if not raw_target:
                raise ValueError("wait_url requires target route/url or value")
            target_url = _build_target_url(base_url, raw_target)
            effective_timeout = _resolve_step_timeout_ms(step.timeout, timeout_ms)
            page.wait_for_url(
                target_url,
                wait_until=_normalize_navigation_wait_until(step.wait),
                timeout=effective_timeout,
            )
            return ActionExecutionResult(page_url=page.url, resolved_object=None, actual_value=page.url)

        if action_key == "press_key" and not step.target:
            resolved_value = case_data.resolve_text(step.value)
            if not resolved_value:
                raise ValueError("press_key requires value")
            page.keyboard.press(resolved_value)
            return ActionExecutionResult(page_url=page.url, resolved_object=None, actual_value=resolved_value)

        if action_key in SUPPORTED_ACTION_KEYS - {"open_page", "wait_url"}:
            initial_wait_state = _normalize_wait_state(step.wait)
            locator, resolved_object = resolve_locator(
                page=page,
                resolver=self._resolver,
                object_key=step.target,
                timeout_ms=timeout_ms,
                wait_for_attached=initial_wait_state != "hidden",
            )
            effective_timeout = _resolve_timeout_ms(step.timeout, resolved_object, timeout_ms)
            wait_state = _normalize_wait_state(step.wait or resolved_object.default_wait)
            if wait_state:
                locator.wait_for(state=wait_state, timeout=effective_timeout)

            if action_key == "wait_element":
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=wait_state)

            if action_key == "click":
                self._click_with_fallback(locator, effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="clicked")

            if action_key == "hover":
                locator.hover(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="hovered")

            if action_key == "check":
                locator.check(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="checked")

            if action_key == "uncheck":
                locator.uncheck(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="unchecked")

            resolved_value = case_data.resolve_text(step.value)
            if action_key == "press_key":
                if not resolved_value:
                    raise ValueError("press_key requires value")
                locator.press(resolved_value, timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=resolved_value)

            if action_key == "select_option":
                locator.select_option(value=resolved_value, timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=resolved_value)

            if action_key == "upload_file":
                locator.set_input_files(_resolve_input_files(resolved_value), timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=resolved_value)

            if action_key in {"clear_and_input", "input_password"}:
                locator.fill(resolved_value, timeout=effective_timeout)
            else:
                locator.type(resolved_value, timeout=effective_timeout)
            return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=resolved_value)

        raise ValueError(f"Unsupported action_key in runtime executor: {action_key}")

    @staticmethod
    def _click_with_fallback(locator: Any, timeout_ms: int) -> None:
        try:
            locator.click(timeout=timeout_ms)
        except Exception as exc:
            if not _should_retry_click_with_force(exc):
                raise
            locator.click(timeout=timeout_ms, force=True)


def _should_retry_click_with_force(exc: Exception) -> bool:
    error_text = str(exc).lower()
    fallback_signals = (
        "intercepts pointer events",
        "subtree intercepts pointer events",
        "another element",
        "element is not receiving pointer events",
    )
    return any(signal in error_text for signal in fallback_signals)


def _build_target_url(base_url: str, target: str) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return base_url.rstrip("/") + "/" + target.lstrip("/")


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


def _resolve_step_timeout_ms(step_timeout_sec: int, default_timeout_ms: int) -> int:
    if step_timeout_sec:
        return step_timeout_sec * 1000
    return default_timeout_ms


def _normalize_wait_state(wait_value: str) -> str:
    mapping = {
        "visible": "visible",
        "clickable": "visible",
        "present": "attached",
        "attached": "attached",
        "hidden": "hidden",
        "": "",
    }
    return mapping.get(wait_value, "visible")


def _normalize_navigation_wait_until(wait_value: str) -> str:
    mapping = {
        "": "domcontentloaded",
        "dom_ready": "domcontentloaded",
        "domcontentloaded": "domcontentloaded",
        "load": "load",
        "networkidle": "networkidle",
        "commit": "commit",
    }
    return mapping.get(wait_value.strip().lower(), "domcontentloaded")



def _resolve_input_files(resolved_value: str) -> str | list[str]:
    file_paths = [item.strip() for item in resolved_value.split(",") if item.strip()]
    if len(file_paths) <= 1:
        return file_paths[0] if file_paths else ""
    return file_paths
