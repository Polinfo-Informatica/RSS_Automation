from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rss_automation.config_backup import backup_config_folder, config_backup_exists_for_date


def test_backup_config_folder_archives_snapshot_and_removes_legacy_backups(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_folder = tmp_path / "RSS_Config"
    backup_root = tmp_path / "RSS_Config_Backups"
    config_folder.mkdir()
    (config_folder / "rss.txt").write_text("feed\n", encoding="utf-8")
    (config_folder / "anime.txt").write_text("Grand Blue\n", encoding="utf-8")

    old_backup = backup_root / "RSS_Config_2026-01-01_00-00-00"
    old_backup.mkdir(parents=True)
    (old_backup / "rss.txt").write_text("old\n", encoding="utf-8")

    archived_batches: list[tuple[Path, Path, list[str], str]] = []

    def fake_update_7z_archive(
        archive_path: Path,
        source_root: Path,
        relative_paths: list[Path],
        command: str = "",
    ) -> None:
        archive_path.write_text("archive\n", encoding="utf-8")
        archived_batches.append(
            (
                archive_path,
                source_root,
                sorted(str(path).replace("\\", "/") for path in relative_paths),
                command,
            )
        )

    pruned: list[tuple[Path, int, str]] = []

    def fake_prune_config_backup_archive(archive_path: Path, max_backups: int, command: str = "") -> None:
        pruned.append((archive_path, max_backups, command))

    monkeypatch.setattr("rss_automation.config_backup.config_snapshot_names", lambda archive, root, command="": set())
    monkeypatch.setattr("rss_automation.config_backup.update_7z_archive", fake_update_7z_archive)
    monkeypatch.setattr("rss_automation.archive_7z.update_7z_archive", fake_update_7z_archive)
    monkeypatch.setattr("rss_automation.config_backup.prune_config_backup_archive", fake_prune_config_backup_archive)

    archive_path = backup_config_folder(
        config_folder,
        backup_root,
        datetime(2026, 7, 7, 4, 30, 0),
        max_backups=1,
        archive_command="7z",
    )

    assert archive_path == backup_root / "RSS_Config_Backups.7z"
    assert archive_path.is_file()
    assert not old_backup.exists()
    assert archived_batches[0][2] == ["RSS_Config_2026-01-01_00-00-00/rss.txt"]
    assert archived_batches[1][2] == [
        "RSS_Config_2026-07-07_04-30-00/anime.txt",
        "RSS_Config_2026-07-07_04-30-00/rss.txt",
    ]
    assert archived_batches[1][3] == "7z"
    assert pruned == [(backup_root / "RSS_Config_Backups.7z", 1, "7z")]


def test_backup_config_folder_skips_when_daily_backup_exists(tmp_path: Path, monkeypatch) -> None:
    config_folder = tmp_path / "RSS_Config"
    backup_root = tmp_path / "RSS_Config_Backups"
    archive_path = backup_root / "RSS_Config_Backups.7z"
    config_folder.mkdir()
    backup_root.mkdir()
    archive_path.write_text("archive\n", encoding="utf-8")
    (config_folder / "rss.txt").write_text("feed\n", encoding="utf-8")
    calls = 0
    pruned: list[tuple[Path, int, str]] = []

    monkeypatch.setattr(
        "rss_automation.config_backup.config_snapshot_names",
        lambda archive, root, command="": {"RSS_Config_2026-07-07_01-00-00"},
    )

    def fake_update_7z_archive(*args, **kwargs) -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr("rss_automation.config_backup.update_7z_archive", fake_update_7z_archive)
    monkeypatch.setattr(
        "rss_automation.config_backup.prune_config_backup_archive",
        lambda archive, max_backups, command="": pruned.append((archive, max_backups, command)),
    )

    result = backup_config_folder(
        config_folder,
        backup_root,
        datetime(2026, 7, 7, 4, 30, 0),
        max_backups=1,
        archive_command="7z",
    )

    assert result == archive_path
    assert calls == 0
    assert pruned == [(archive_path, 1, "7z")]


def test_backup_config_folder_force_ignores_daily_backup(tmp_path: Path, monkeypatch) -> None:
    config_folder = tmp_path / "RSS_Config"
    backup_root = tmp_path / "RSS_Config_Backups"
    config_folder.mkdir()
    backup_root.mkdir()
    (config_folder / "rss.txt").write_text("feed\n", encoding="utf-8")
    calls = 0
    pruned: list[tuple[Path, int, str]] = []

    monkeypatch.setattr(
        "rss_automation.config_backup.config_snapshot_names",
        lambda archive, root, command="": {"RSS_Config_2026-07-07_01-00-00"},
    )

    def fake_update_7z_archive(
        archive_path: Path, source_root: Path, relative_paths: list[Path], command: str = ""
    ) -> None:
        nonlocal calls
        calls += 1
        archive_path.write_text("archive\n", encoding="utf-8")

    monkeypatch.setattr("rss_automation.config_backup.update_7z_archive", fake_update_7z_archive)
    monkeypatch.setattr(
        "rss_automation.config_backup.prune_config_backup_archive",
        lambda archive, max_backups, command="": pruned.append((archive, max_backups, command)),
    )

    result = backup_config_folder(
        config_folder,
        backup_root,
        datetime(2026, 7, 7, 4, 30, 0),
        max_backups=1,
        archive_command="7z",
        force=True,
    )

    assert result == backup_root / "RSS_Config_Backups.7z"
    assert calls == 1
    assert pruned == [(backup_root / "RSS_Config_Backups.7z", 1, "7z")]


def test_config_backup_exists_for_date_matches_snapshot_date(tmp_path: Path, monkeypatch) -> None:
    backup_root = tmp_path / "RSS_Config_Backups"
    archive_path = backup_root / "RSS_Config_Backups.7z"
    monkeypatch.setattr(
        "rss_automation.config_backup.config_snapshot_names",
        lambda archive, root, command="": {"RSS_Config_2026-07-07_01-00-00"},
    )

    assert config_backup_exists_for_date(archive_path, backup_root, datetime(2026, 7, 7, 4, 30, 0))
    assert not config_backup_exists_for_date(archive_path, backup_root, datetime(2026, 7, 8, 4, 30, 0))


def test_backup_config_folder_returns_none_when_config_missing(tmp_path: Path) -> None:
    archive_path = backup_config_folder(
        tmp_path / "missing",
        tmp_path / "RSS_Config_Backups",
        datetime(2026, 7, 7, 4, 30, 0),
        max_backups=1,
    )

    assert archive_path is None
