"""Runtime configuration backup helpers."""

from __future__ import annotations

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from rss_automation.archive_7z import (
    CONFIG_BACKUP_ARCHIVE_NAME,
    archive_legacy_backup_directories,
    prune_config_backup_archive,
    relative_file_paths,
    unique_config_snapshot_name,
    update_7z_archive,
)


def backup_config_folder(
    config_folder: Path,
    backup_root: Path,
    run_started_at: datetime,
    max_backups: int,
    archive_command: str = "",
) -> Path | None:
    """Create one timestamped RSS_Config snapshot inside the single backup 7z archive."""

    if not config_folder.exists():
        logging.warning("Config backup skipped because config folder does not exist: %s", config_folder)
        return None

    backup_root.mkdir(parents=True, exist_ok=True)
    archive_path = backup_root / CONFIG_BACKUP_ARCHIVE_NAME
    snapshot_name = unique_config_snapshot_name(
        archive_path,
        backup_root,
        run_started_at.strftime("RSS_Config_%Y-%m-%d_%H-%M-%S"),
        command=archive_command,
    )

    with tempfile.TemporaryDirectory(prefix="rss_config_backup_") as temp_name:
        temp_root = Path(temp_name)
        snapshot_root = temp_root / snapshot_name
        shutil.copytree(config_folder, snapshot_root)
        update_7z_archive(
            archive_path,
            temp_root,
            relative_file_paths(temp_root),
            command=archive_command,
        )

    archive_legacy_backup_directories(backup_root, archive_path, command=archive_command)
    prune_config_backup_archive(archive_path, max_backups, command=archive_command)
    logging.info("Config backup archived: %s", archive_path)
    return archive_path
