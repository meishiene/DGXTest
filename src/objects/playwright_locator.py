from __future__ import annotations

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from src.objects.resolver import LocatorCandidate, ObjectRepositoryResolver, ResolvedObject


def resolve_locator(
    page: Page,
    resolver: ObjectRepositoryResolver,
    object_key: str,
    timeout_ms: int,
) -> tuple[Locator, ResolvedObject]:
    last_error: Exception | None = None
    for candidate in resolver.get_locator_candidates(object_key):
        try:
            locator = _build_locator(page, candidate)
            locator.wait_for(state="attached", timeout=timeout_ms)
            resolved = resolver.build_resolved_object(
                object_key=object_key,
                locator_type=candidate.locator_type,
                locator_value=candidate.locator_value,
            )
            return locator, resolved
        except Exception as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    raise ValueError(f"对象没有可用定位器: {object_key}")


def _build_locator(page: Page, candidate: LocatorCandidate) -> Locator:
    locator_type = candidate.locator_type.lower()
    locator_value = candidate.locator_value

    if locator_type == "testid":
        return page.get_by_test_id(locator_value)
    if locator_type == "id":
        return page.locator(f"#{locator_value}")
    if locator_type == "name":
        return page.locator(f"[name='{locator_value}']")
    if locator_type == "css":
        return page.locator(locator_value)
    if locator_type == "xpath":
        return page.locator(f"xpath={locator_value}")
    if locator_type == "text":
        return page.get_by_text(locator_value, exact=True)
    if locator_type == "partial_text":
        return page.get_by_text(locator_value)

    raise ValueError(f"暂不支持的定位方式: {candidate.locator_type}")
