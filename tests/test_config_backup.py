from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from rss_automation.config_backup import backup_config_folder, prune_config_backups


def test_backup_config_folder_copies_files_and_prunes_old_backups(tmp_path: Path) -> None:
    config_folder = tmp_path / "RSS_Config"
    backup_root = tmp_path / "RSS_Config_Backups"
    config_folder.mkdir()
    (config_folder / "rss.txt").write_text("feed\n", encoding="utf-8")
    (config_folder / "anime.txt").write_text("Grand Blue\n", encoding="utf-8")

    old_backup = backup_root / "RSS_Config_2026-01-01_00-00-00"
    old_backup.mkdir(parents=True)
    (old_backup / "rss.txt").write_text("old\n", encoding="utf-8")

    backup_path = backup_config_folder(
        config_folder,
        backup_root,
        datetime(2026, 7, 7, 4, 30, 0),
        max_backups=1,
    )

    assert backup_path is not None
    assert backup_path.name == "RSS_Config_2026-07-07_04-30-00"
    assert (backup_path / "rss.txt").read_text(encoding="utf-8") == "feed\n"
    assert (backup_path / "anime.txt").read_text(encoding="utf-8") == "Grand Blue\n"
    assert not old_backup.exists()


def test_prune_config_backups_keeps_newest_by_mtime(tmp_path: Path) -> None:
    backup_root = tmp_path / "RSS_Config_Backups"
    backup_root.mkdir()
    now = datetime.now().timestamp()

    for index in range(3):
        backup = backup_root / f"RSS_Config_2026-01-0{index + 1}_00-00-00"
        backup.mkdir()
        timestamp = now + timedelta(minutes=index).total_seconds()
        backup.touch()
        backup.chmod(0o700)
        import os

        os.utime(backup, (timestamp, timestamp))

    prune_config_backups(backup_root, max_backups=2)

    remaining = sorted(path.name for path in backup_root.iterdir())
    assert remaining == ["RSS_Config_2026-01-02_00-00-00", "RSS_Config_2026-01-03_00-00-00"]
