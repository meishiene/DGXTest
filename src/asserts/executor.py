from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from src.objects.playwright_locator import resolve_locator
from src.objects.resolver import ObjectRepositoryResolver, ResolvedObject
from src.parser.models import StepRecord
from src.utils.data_resolver import CaseExecutionData


@dataclass(slots=True)
class AssertExecutionResult:
    page_url: str
    resolved_object: ResolvedObject | None
    actual_value: str


class AssertExecutor:
    def __init__(self, resolver: ObjectRepositoryResolver) -> None:
        self._resolver = resolver

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
                raise AssertionError(f"当前 URL 未包含预期值: expected={expected_value}, actual={page.url}")
            return AssertExecutionResult(page_url=page.url, resolved_object=None, actual_value=page.url)

        if assert_key == "assert_text_contains":
            locator, resolved_object = resolve_locator(
                page=page,
                resolver=self._resolver,
                object_key=step.target,
                timeout_ms=timeout_ms,
            )
            actual_value = locator.text_content(timeout=timeout_ms) or ""
            if expected_value not in actual_value:
                raise AssertionError(f"文本断言失败: expected contains={expected_value}, actual={actual_value}")
            return AssertExecutionResult(page_url=page.url, resolved_object=resolved_object, actual_value=actual_value)

        raise ValueError(f"当前骨架暂不支持的 assert_key: {assert_key}")
