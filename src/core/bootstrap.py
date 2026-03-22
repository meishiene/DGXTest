from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.results.models import AppConfig


@dataclass(slots=True)
class RunContext:
    run_id: str
    root_dir: Path
    artifacts_dir: Path
    screenshots_dir: Path
    html_snapshots_dir: Path
    console_logs_dir: Path
    network_logs_dir: Path
    videos_dir: Path
    ai_bugs_dir: Path
    manifest_path: Path


def prepare_run_context(config: AppConfig) -> RunContext:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_id = config.run_id or f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    root_dir = Path(config.output_root) / f"{timestamp}_{run_id}"

    artifacts_dir = root_dir / "artifacts"
    screenshots_dir = artifacts_dir / "screenshots"
    html_snapshots_dir = artifacts_dir / "html_snapshots"
    console_logs_dir = artifacts_dir / "console_logs"
    network_logs_dir = artifacts_dir / "network_logs"
    videos_dir = artifacts_dir / "videos"
    ai_bugs_dir = root_dir / "ai_bugs"

    for path in [
        root_dir,
        artifacts_dir,
        screenshots_dir,
        html_snapshots_dir,
        console_logs_dir,
        network_logs_dir,
        videos_dir,
        ai_bugs_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    return RunContext(
        run_id=run_id,
        root_dir=root_dir,
        artifacts_dir=artifacts_dir,
        screenshots_dir=screenshots_dir,
        html_snapshots_dir=html_snapshots_dir,
        console_logs_dir=console_logs_dir,
        network_logs_dir=network_logs_dir,
        videos_dir=videos_dir,
        ai_bugs_dir=ai_bugs_dir,
        manifest_path=root_dir / "run_manifest.json",
    )
