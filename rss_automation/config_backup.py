"""Runtime configuration backup helpers."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path


def backup_config_folder(
    config_folder: Path, backup_root: Path, run_started_at: datetime, max_backups: int
) -> Path | None:
    """Create a timestamped backup of RSS_Config and prune old backups."""

    if not config_folder.exists():
        logging.warning("Config backup skipped because config folder does not exist: %s", config_folder)
        return None

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / run_started_at.strftime("RSS_Config_%Y-%m-%d_%H-%M-%S")

    if backup_path.exists():
        suffix = 1
        while True:
            candidate = backup_root / f"{backup_path.name}_{suffix}"
            if not candidate.exists():
                backup_path = candidate
                break
            suffix += 1

    shutil.copytree(config_folder, backup_path)

    # copytree preserves source directory metadata. Touch the backup after copy
    # so mtime-based pruning never deletes the newly created backup first.
    backup_path.touch()

    logging.info("Config backup created: %s", backup_path)

    prune_config_backups(backup_root, max_backups)
    return backup_path


def prune_config_backups(backup_root: Path, max_backups: int) -> None:
    """Keep only the newest max_backups RSS_Config backup folders."""

    if max_backups < 1:
        return

    backups = sorted(
        (path for path in backup_root.iterdir() if path.is_dir() and path.name.startswith("RSS_Config_")),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[max_backups:]:
        shutil.rmtree(old_backup)
        logging.info("Old config backup pruned: %s", old_backup)
