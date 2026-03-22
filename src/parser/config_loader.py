from __future__ import annotations

import json
from pathlib import Path

from src.results.models import AppConfig


def load_run_config(config_path: Path) -> AppConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"运行配置不存在: {config_path}")

    raw_data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    return AppConfig(**raw_data)
