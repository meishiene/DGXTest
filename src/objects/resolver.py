from __future__ import annotations

from dataclasses import dataclass

from src.parser.models import ObjectRecord, ParsedObjectRepository


@dataclass(slots=True)
class ResolvedObject:
    object_key: str
    object_name: str
    page_name: str
    object_type: str
    locator_type: str
    locator_value: str
    component_hint: str
    frontend_file_hint: str
    api_hint: str
    default_wait: str
    default_timeout_sec: int


@dataclass(slots=True)
class LocatorCandidate:
    locator_type: str
    locator_value: str


class ObjectRepositoryResolver:
    def __init__(self, repository: ParsedObjectRepository) -> None:
        self._object_map = {item.object_key: item for item in repository.objects}

    def has_object(self, object_key: str) -> bool:
        return object_key in self._object_map

    def get_object(self, object_key: str) -> ObjectRecord:
        if object_key not in self._object_map:
            raise KeyError(f"对象不存在: {object_key}")
        return self._object_map[object_key]

    def get_locator_candidates(self, object_key: str) -> list[LocatorCandidate]:
        record = self.get_object(object_key)
        candidates: list[LocatorCandidate] = []
        for locator_type, locator_value in [
            (record.locator_primary_type, record.locator_primary_value),
            (record.locator_backup_1_type, record.locator_backup_1_value),
            (record.locator_backup_2_type, record.locator_backup_2_value),
        ]:
            if locator_type and locator_value:
                candidates.append(LocatorCandidate(locator_type=locator_type, locator_value=locator_value))
        return candidates

    def build_resolved_object(
        self,
        object_key: str,
        locator_type: str,
        locator_value: str,
    ) -> ResolvedObject:
        record = self.get_object(object_key)
        return ResolvedObject(
            object_key=record.object_key,
            object_name=record.object_name,
            page_name=record.page_name,
            object_type=record.object_type,
            locator_type=locator_type,
            locator_value=locator_value,
            component_hint=record.ai_component_hint,
            frontend_file_hint=record.frontend_file_hint,
            api_hint=record.api_hint,
            default_wait=record.default_wait,
            default_timeout_sec=record.default_timeout_sec,
        )
