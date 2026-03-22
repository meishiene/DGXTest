from __future__ import annotations

import argparse
from pathlib import Path

from src.core.app import run_application


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DGX Web 自动化测试骨架入口")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/run_config.json"),
        help="运行配置文件路径",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="强制使用 dry-run 模式执行，不打开真实浏览器",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    return run_application(config_path=args.config, force_dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
