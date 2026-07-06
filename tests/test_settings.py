from __future__ import annotations

from pathlib import Path

from rss_automation.settings import resolve_configured_paths, resolve_path_value, resolve_settings_path


def test_resolve_settings_path_uses_project_root_for_relative_paths(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    settings_path = Path("settings.json")

    assert resolve_settings_path(settings_path, project_root) == project_root / "settings.json"


def test_resolve_settings_path_keeps_absolute_paths(tmp_path: Path) -> None:
    absolute = tmp_path / "custom-settings.json"

    assert resolve_settings_path(absolute, tmp_path / "project") == absolute


def test_resolve_path_value_expands_project_root_token(tmp_path: Path) -> None:
    project_root = tmp_path / "project"

    resolved = resolve_path_value("${project_root}\\RSS_Config", project_root, tmp_path / "Downloads")

    assert Path(resolved) == (project_root / "RSS_Config").resolve()


def test_resolve_path_value_expands_downloads_folder_token(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    downloads_folder = tmp_path / "Downloads"

    resolved = resolve_path_value("${downloads_folder}\\RSS_Automation", project_root, downloads_folder)

    assert Path(resolved) == (downloads_folder / "RSS_Automation").resolve()


def test_resolve_configured_paths_expands_root_folder_token(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    downloads_folder = tmp_path / "Downloads"
    monkeypatch.setattr("rss_automation.settings.get_downloads_folder", lambda: downloads_folder)

    resolved = resolve_configured_paths(
        {
            "root_folder": "${downloads_folder}\\RSS_Automation",
            "config_folder": "${root_folder}\\RSS_Config",
            "magnet_output_folder": "${root_folder}\\RSS_Magnet",
            "torrent_output_folder": "${root_folder}\\RSS_Torrent",
            "log_folder": "${root_folder}\\Logs",
        },
        project_root,
    )

    assert Path(resolved["root_folder"]) == (downloads_folder / "RSS_Automation").resolve()
    assert Path(resolved["config_folder"]) == (downloads_folder / "RSS_Automation" / "RSS_Config").resolve()


def test_resolve_path_value_resolves_relative_paths_from_project_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project"

    resolved = resolve_path_value("RSS_Config", project_root, tmp_path / "Downloads")

    assert Path(resolved) == (project_root / "RSS_Config").resolve()
