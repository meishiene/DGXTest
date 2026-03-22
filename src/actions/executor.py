from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.sync_api import Page

from src.objects.playwright_locator import resolve_locator
from src.objects.resolver import ObjectRepositoryResolver, ResolvedObject
from src.parser.models import StepRecord
from src.utils.data_resolver import CaseExecutionData


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

        if action_key in {"click", "clear_and_input", "input_password", "input_text", "check", "uncheck"}:
            locator, resolved_object = resolve_locator(
                page=page,
                resolver=self._resolver,
                object_key=step.target,
                timeout_ms=timeout_ms,
            )
            effective_timeout = step.timeout * 1000 if step.timeout else timeout_ms
            wait_state = _normalize_wait_state(step.wait or resolved_object.default_wait)
            if wait_state:
                locator.wait_for(state=wait_state, timeout=effective_timeout)

            if action_key == "click":
                locator.click(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="clicked")

            if action_key == "check":
                locator.check(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="checked")

            if action_key == "uncheck":
                locator.uncheck(timeout=effective_timeout)
                return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value="unchecked")

            resolved_value = case_data.resolve_text(step.value)
            if action_key in {"clear_and_input", "input_password"}:
                locator.fill(resolved_value, timeout=effective_timeout)
            else:
                locator.type(resolved_value, timeout=effective_timeout)
            return ActionExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=resolved_value)

        raise ValueError(f"当前骨架暂不支持的 action_key: {action_key}")


def _build_target_url(base_url: str, target: str) -> str:
    if target.startswith("http://") or target.startswith("https://"):
        return target
    return base_url.rstrip("/") + "/" + target.lstrip("/")


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

