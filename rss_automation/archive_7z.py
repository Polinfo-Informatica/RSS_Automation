"""7z archive helpers for compact runtime logs and backups."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from rss_automation.constants import MASTER_LOG_NAME, RUN_LOG_PREFIX, RUN_LOG_SUFFIX

CONFIG_BACKUP_ARCHIVE_NAME = "RSS_Config_Backups.7z"
LOG_ARCHIVE_NAME = "RSS_Automation_Logs.7z"
CONFIG_BACKUP_PREFIX = "RSS_Config_"


def candidate_7z_paths() -> list[Path]:
    """Return common Windows 7-Zip executable paths."""

    candidates: list[Path] = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(env_name)
        if root:
            candidates.append(Path(root) / "7-Zip" / "7z.exe")
    return candidates


def find_7z_command(configured_command: str = "") -> str | None:
    """Find a 7-Zip command from settings, PATH, or common Windows install paths."""

    command = configured_command.strip()
    if command:
        return command

    for command_name in ("7z", "7zz", "7za"):
        found = shutil.which(command_name)
        if found:
            return found

    for candidate in candidate_7z_paths():
        if candidate.exists():
            return str(candidate)

    return None


def run_7z(arguments: Sequence[str], command: str = "", cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run 7-Zip and raise a helpful error if 7-Zip is unavailable or fails."""

    resolved_command = find_7z_command(command)
    if resolved_command is None:
        raise FileNotFoundError(
            "7-Zip executable not found. Install 7-Zip, add 7z.exe to PATH, "
            'or set "archive_7z_command" in settings.json.'
        )

    result = subprocess.run(
        [resolved_command, *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"7-Zip failed with exit code {result.returncode}: {details}")

    return result


def relative_file_paths(root: Path) -> list[Path]:
    """Return all files under root as relative paths."""

    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def archive_path_text(path: Path | str) -> str:
    """Normalize archive member paths to the separator used by 7-Zip listings."""

    return str(path).replace("\\", "/")


def update_7z_archive(archive_path: Path, source_root: Path, relative_paths: Sequence[Path], command: str = "") -> None:
    """Add or update relative files inside a single .7z archive."""

    paths = [archive_path_text(path) for path in relative_paths]
    if not paths:
        return

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    run_7z(["u", str(archive_path), "-mx=9", "-y", *paths], command=command, cwd=source_root)


def list_7z_archive_paths(archive_path: Path, command: str = "") -> list[str]:
    """List paths currently stored in a .7z archive."""

    if not archive_path.exists():
        return []

    result = run_7z(["l", "-slt", str(archive_path)], command=command)
    archive_file_name = archive_path.name.lower()
    paths: list[str] = []

    for line in result.stdout.splitlines():
        if not line.startswith("Path = "):
            continue

        value = line.removeprefix("Path = ").strip()
        if not value:
            continue

        normalized = archive_path_text(value)
        if PurePosixPath(normalized).name.lower() == archive_file_name:
            continue

        paths.append(normalized)

    return paths


def delete_7z_archive_paths(archive_path: Path, paths: Sequence[str], command: str = "") -> None:
    """Delete specific archive members from a .7z archive."""

    if not paths:
        return

    run_7z(["d", str(archive_path), "-y", *paths], command=command)


def config_snapshot_names(archive_path: Path, backup_root: Path, command: str = "") -> set[str]:
    """Return existing config backup snapshot names from the archive and legacy folders."""

    names = {
        path.name
        for path in backup_root.iterdir()
        if path.is_dir() and path.name.startswith(CONFIG_BACKUP_PREFIX)
    }

    for archive_member in list_7z_archive_paths(archive_path, command=command):
        top_level = archive_member.split("/", 1)[0]
        if top_level.startswith(CONFIG_BACKUP_PREFIX):
            names.add(top_level)

    return names


def unique_config_snapshot_name(archive_path: Path, backup_root: Path, desired_name: str, command: str = "") -> str:
    """Return a backup snapshot name that does not already exist."""

    existing = config_snapshot_names(archive_path, backup_root, command=command)
    if desired_name not in existing:
        return desired_name

    suffix = 1
    while f"{desired_name}_{suffix}" in existing:
        suffix += 1
    return f"{desired_name}_{suffix}"


def archive_legacy_backup_directories(backup_root: Path, archive_path: Path, command: str = "") -> None:
    """Move old on-disk backup directories into the single archive, then remove them."""

    legacy_dirs = sorted(
        path for path in backup_root.iterdir() if path.is_dir() and path.name.startswith(CONFIG_BACKUP_PREFIX)
    )
    if not legacy_dirs:
        return

    relative_paths: list[Path] = []
    for legacy_dir in legacy_dirs:
        relative_paths.extend(path.relative_to(backup_root) for path in legacy_dir.rglob("*") if path.is_file())

    update_7z_archive(archive_path, backup_root, relative_paths, command=command)

    for legacy_dir in legacy_dirs:
        shutil.rmtree(legacy_dir)


def prune_config_backup_archive(archive_path: Path, max_backups: int, command: str = "") -> None:
    """Keep only the newest config backup snapshots inside the archive."""

    if max_backups < 1 or not archive_path.exists():
        return

    archive_members = list_7z_archive_paths(archive_path, command=command)
    snapshot_names = sorted(
        {
            member.split("/", 1)[0]
            for member in archive_members
            if member.split("/", 1)[0].startswith(CONFIG_BACKUP_PREFIX)
        }
    )
    old_snapshots = set(snapshot_names[:-max_backups])
    if not old_snapshots:
        return

    delete_members = [
        member for member in archive_members if member.split("/", 1)[0] in old_snapshots
    ]
    delete_7z_archive_paths(archive_path, delete_members, command=command)


def prune_log_archive(archive_path: Path, max_log_executions: int, command: str = "") -> None:
    """Keep only the newest timestamped run logs inside the log archive."""

    if max_log_executions < 1 or not archive_path.exists():
        return

    archive_members = list_7z_archive_paths(archive_path, command=command)
    run_logs = sorted(
        member
        for member in archive_members
        if PurePosixPath(member).name.startswith(RUN_LOG_PREFIX)
        and PurePosixPath(member).name.endswith(RUN_LOG_SUFFIX)
        and PurePosixPath(member).name != MASTER_LOG_NAME
    )
    old_logs = run_logs[:-max_log_executions]
    delete_7z_archive_paths(archive_path, old_logs, command=command)


def archive_log_folder(log_folder: Path, max_log_executions: int, command: str = "") -> Path | None:
    """Move current plain log files into one 7z archive and remove the originals."""

    log_files = sorted(path for path in log_folder.glob("*.log") if path.is_file())
    archive_path = log_folder / LOG_ARCHIVE_NAME

    if not log_files:
        return archive_path if archive_path.exists() else None

    relative_paths = [path.relative_to(log_folder) for path in log_files]
    update_7z_archive(archive_path, log_folder, relative_paths, command=command)
    prune_log_archive(archive_path, max_log_executions, command=command)

    for log_file in log_files:
        log_file.unlink()

    return archive_path


def warn_archive_failure(context: str, exc: Exception) -> None:
    """Report archive failures without hiding the main RSS run result."""

    logging.warning("Could not compact %s into 7z archive | %s: %s", context, type(exc).__name__, exc)
