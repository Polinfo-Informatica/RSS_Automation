from __future__ import annotations

from pathlib import Path

import pytest
from rss_automation.settings import get_downloads_folder, load_settings, setup_folders, validate_settings


def test_validate_settings_accepts_valid_defaults() -> None:
    validate_settings(
        {
            "prefer_download_type": "magnet",
            "match_mode": "contains",
            "write_magnet_format": "title_and_magnet",
            "max_log_executions": 1,
        }
    )


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("prefer_download_type", "invalid", "prefer_download_type"),
        ("match_mode", "invalid", "match_mode"),
        ("write_magnet_format", "invalid", "write_magnet_format"),
        ("max_log_executions", "invalid", "max_log_executions"),
        ("max_log_executions", 0, "max_log_executions"),
    ],
)
def test_validate_settings_rejects_invalid_values(key: str, value: object, message: str) -> None:
    settings = {
        "prefer_download_type": "magnet",
        "match_mode": "contains",
        "write_magnet_format": "title_and_magnet",
        "max_log_executions": 1,
    }
    settings[key] = value

    with pytest.raises(ValueError, match=message):
        validate_settings(settings)


def test_setup_folders_creates_runtime_structure(tmp_path: Path) -> None:
    root = tmp_path / "runtime"
    settings = {
        "root_folder": str(root),
        "config_folder": str(root / "RSS_Config"),
        "magnet_output_folder": str(root / "RSS_Magnet"),
        "torrent_output_folder": str(root / "RSS_Torrent"),
        "log_folder": str(root / "Logs"),
        "rss_file": "rss.txt",
        "exclude_file": "exclude.txt",
    }

    paths = setup_folders(settings)

    assert paths["root"].is_dir()
    assert paths["config"].is_dir()
    assert paths["magnet"].is_dir()
    assert paths["torrent"].is_dir()
    assert paths["log"].is_dir()
    assert (paths["config"] / "rss.txt").is_file()
    assert (paths["config"] / "exclude.txt").is_file()
    assert (paths["config"] / "anime.txt").is_file()


def test_load_settings_creates_default_file_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    downloads_folder = tmp_path / "Downloads"
    monkeypatch.setattr("rss_automation.settings.get_downloads_folder", lambda: downloads_folder)

    settings = load_settings(Path("settings.json"), project_root)

    assert (project_root / "settings.json").is_file()
    assert Path(settings["root_folder"]) == (downloads_folder / "RSS_Automation").resolve()


def test_get_downloads_folder_falls_back_to_home_downloads(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("rss_automation.settings.sys.platform", "linux")
    monkeypatch.setattr("rss_automation.settings.Path.home", lambda: tmp_path)

    assert get_downloads_folder() == tmp_path / "Downloads"
