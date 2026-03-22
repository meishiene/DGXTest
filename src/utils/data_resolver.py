from __future__ import annotations

import re
from dataclasses import dataclass

from src.parser.models import CaseRecord, ParsedTestSuite, TestDataRecord


_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass(slots=True)
class CaseExecutionData:
    values: dict[str, str]

    def resolve_text(self, value: str) -> str:
        if not value:
            return ""

        def replace(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            return self.values.get(key, "")

        return _PATTERN.sub(replace, value)


class DataResolver:
    def __init__(self, suite: ParsedTestSuite) -> None:
        self._data_map = {item.data_set_id: item for item in suite.test_data}

    def build_case_data(self, case: CaseRecord) -> CaseExecutionData:
        if not case.data_set_id:
            return CaseExecutionData(values={})
        record = self._data_map.get(case.data_set_id)
        if record is None:
            return CaseExecutionData(values={})
        return CaseExecutionData(values=record.payload)
