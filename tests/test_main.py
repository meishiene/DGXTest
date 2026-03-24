from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from src import main as main_module


def test_main_returns_run_application_exit_code(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "build_arg_parser",
        lambda: _FakeParser(Namespace(config=Path("configs/run_config.json"), dry_run=False)),
    )
    monkeypatch.setattr(main_module, "run_application", lambda config_path, force_dry_run: 0)

    assert main_module.main() == 0


def test_main_prints_user_friendly_error_for_known_failures(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        main_module,
        "build_arg_parser",
        lambda: _FakeParser(Namespace(config=Path("configs/missing.json"), dry_run=False)),
    )

    def _raise_known_error(*, config_path: Path, force_dry_run: bool) -> int:
        raise ValueError("base_url 必须是站点根地址")

    monkeypatch.setattr(main_module, "run_application", _raise_known_error)

    exit_code = main_module.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "运行失败: base_url 必须是站点根地址" in captured.err


class _FakeParser:
    def __init__(self, namespace: Namespace) -> None:
        self._namespace = namespace

    def parse_args(self) -> Namespace:
        return self._namespace
