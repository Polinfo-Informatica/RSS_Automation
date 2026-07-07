from __future__ import annotations

import subprocess
from pathlib import Path

from rss_automation import archive_7z


def test_update_7z_archive_runs_update_with_relative_paths(tmp_path: Path, monkeypatch) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    archive_path = tmp_path / "archives" / "runtime.7z"
    calls: list[tuple[list[str], Path | None]] = []

    monkeypatch.setattr(archive_7z, "find_7z_command", lambda command="": "7z")

    def fake_run(
        args: list[str],
        cwd: Path | None,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((args, cwd))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(archive_7z.subprocess, "run", fake_run)

    archive_7z.update_7z_archive(
        archive_path,
        source_root,
        [Path("RSS_Config_2026-07-07_04-30-00/rss.txt"), Path("RSS_Config_2026-07-07_04-30-00/anime.txt")],
    )

    assert calls == [
        (
            [
                "7z",
                "u",
                str(archive_path),
                "-mx=9",
                "-y",
                "RSS_Config_2026-07-07_04-30-00/rss.txt",
                "RSS_Config_2026-07-07_04-30-00/anime.txt",
            ],
            source_root,
        )
    ]


def test_list_7z_archive_paths_parses_technical_listing(tmp_path: Path, monkeypatch) -> None:
    archive_path = tmp_path / "RSS_Config_Backups.7z"
    archive_path.write_text("archive\n", encoding="utf-8")

    def fake_run_7z(
        arguments: list[str],
        command: str = "",
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        assert arguments == ["l", "-slt", str(archive_path)]
        assert cwd is None
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=(
                f"Path = {archive_path}\n"
                "Path = RSS_Config_2026-07-07_04-30-00/rss.txt\n"
                "Path = RSS_Config_2026-07-07_04-30-00/anime.txt\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(archive_7z, "run_7z", fake_run_7z)

    assert archive_7z.list_7z_archive_paths(archive_path) == [
        "RSS_Config_2026-07-07_04-30-00/rss.txt",
        "RSS_Config_2026-07-07_04-30-00/anime.txt",
    ]


def test_archive_log_folder_archives_logs_and_removes_plain_files(tmp_path: Path, monkeypatch) -> None:
    log_folder = tmp_path / "Logs"
    log_folder.mkdir()
    master_log = log_folder / "RSS_Automation.log"
    run_log = log_folder / "RSS_Automation_2026-07-07_04-30-00.log"
    master_log.write_text("master\n", encoding="utf-8")
    run_log.write_text("run\n", encoding="utf-8")
    archived: list[list[str]] = []

    def fake_update_7z_archive(
        archive_path: Path,
        source_root: Path,
        relative_paths: list[Path],
        command: str = "",
    ) -> None:
        assert source_root == log_folder
        assert command == "7z"
        archive_path.write_text("archive\n", encoding="utf-8")
        archived.append(sorted(str(path).replace("\\", "/") for path in relative_paths))

    pruned: list[tuple[Path, int, str]] = []

    def fake_prune_log_archive(archive_path: Path, max_log_executions: int, command: str = "") -> None:
        pruned.append((archive_path, max_log_executions, command))

    monkeypatch.setattr(archive_7z, "update_7z_archive", fake_update_7z_archive)
    monkeypatch.setattr(archive_7z, "prune_log_archive", fake_prune_log_archive)

    archive_path = archive_7z.archive_log_folder(log_folder, max_log_executions=100, command="7z")

    assert archive_path == log_folder / "RSS_Automation_Logs.7z"
    assert archived == [["RSS_Automation.log", "RSS_Automation_2026-07-07_04-30-00.log"]]
    assert pruned == [(log_folder / "RSS_Automation_Logs.7z", 100, "7z")]
    assert sorted(path.name for path in log_folder.iterdir()) == ["RSS_Automation_Logs.7z"]


def test_prune_config_backup_archive_deletes_old_snapshot_members(tmp_path: Path, monkeypatch) -> None:
    archive_path = tmp_path / "RSS_Config_Backups.7z"
    archive_path.write_text("archive\n", encoding="utf-8")
    deleted: list[list[str]] = []

    monkeypatch.setattr(
        archive_7z,
        "list_7z_archive_paths",
        lambda archive, command="": [
            "RSS_Config_2026-01-01_00-00-00/rss.txt",
            "RSS_Config_2026-01-02_00-00-00/rss.txt",
            "RSS_Config_2026-01-03_00-00-00/rss.txt",
        ],
    )
    monkeypatch.setattr(
        archive_7z,
        "delete_7z_archive_paths",
        lambda archive, paths, command="": deleted.append(list(paths)),
    )

    archive_7z.prune_config_backup_archive(archive_path, max_backups=2, command="7z")

    assert deleted == [["RSS_Config_2026-01-01_00-00-00/rss.txt"]]
