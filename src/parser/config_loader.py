from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from src.results.models import AppConfig


LIVE_REQUIRED_CONFIG_KEYS = frozenset({"test_workbook_path", "object_repository_path"})
APP_CONFIG_FIELD_NAMES = frozenset(field.name for field in fields(AppConfig))


def load_run_config(config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"运行配置不存在: {config_path}")

    raw_data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw_data, dict):
        raise ValueError(f"运行配置顶层必须是 JSON object: {config_path}")

    unknown_keys = sorted(set(raw_data) - APP_CONFIG_FIELD_NAMES)
    if unknown_keys:
        raise ValueError("运行配置存在未知字段: " + ", ".join(unknown_keys))

    try:
        config = AppConfig(**raw_data)
    except TypeError as exc:
        raise ValueError(f"运行配置字段不完整或格式不正确: {config_path}") from exc

    if not config.dry_run:
        missing_live_keys = sorted(key for key in LIVE_REQUIRED_CONFIG_KEYS if key not in raw_data)
        if missing_live_keys:
            raise ValueError(
                "正式运行配置必须显式填写以下字段: " + ", ".join(missing_live_keys)
            )

    return config
