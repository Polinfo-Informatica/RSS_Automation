"""Logging setup, run headers/footers, and retention pruning."""

from __future__ import annotations

import logging
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

from rss_automation import __version__
from rss_automation.constants import MASTER_LOG_NAME, RUN_END_MARKER, RUN_LOG_PREFIX, RUN_LOG_SUFFIX, RUN_START_MARKER
from rss_automation.models import LogContext, RunStats


def make_run_log_path(log_folder: Path, run_started_at: datetime) -> Path:
    """Create RSS_Automation_YYYY-MM-DD_HH-MM-SS.log for this run."""

    timestamp = run_started_at.strftime("%Y-%m-%d_%H-%M-%S")
    base = log_folder / f"{RUN_LOG_PREFIX}{timestamp}{RUN_LOG_SUFFIX}"
    if not base.exists():
        return base

    # If multiple executions start in the same second, keep filenames unique.
    for index in range(2, 1000):
        candidate = log_folder / f"{RUN_LOG_PREFIX}{timestamp}_{index:03d}{RUN_LOG_SUFFIX}"
        if not candidate.exists():
            return candidate

    raise RuntimeError("Could not create a unique timestamped log filename.")


def setup_logging(log_folder: Path, run_started_at: datetime) -> LogContext:
    """Send the same log output to console, master log, and per-run log."""

    log_folder.mkdir(parents=True, exist_ok=True)
    master_log_path = log_folder / MASTER_LOG_NAME
    run_log_path = make_run_log_path(log_folder, run_started_at)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handlers: list[logging.Handler] = [
        logging.FileHandler(master_log_path, mode="a", encoding="utf-8"),
        logging.FileHandler(run_log_path, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]

    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)
    return LogContext(run_started_at=run_started_at, master_log_path=master_log_path, run_log_path=run_log_path)


def shutdown_logging() -> None:
    """Flush and close handlers so logs can be pruned safely on Windows."""

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.flush()
        handler.close()
        root_logger.removeHandler(handler)


def prune_timestamped_logs(log_folder: Path, max_log_executions: int) -> int:
    """Keep only the newest timestamped execution logs."""

    logs = sorted(
        (
            path
            for path in log_folder.glob(f"{RUN_LOG_PREFIX}*{RUN_LOG_SUFFIX}")
            if path.name != MASTER_LOG_NAME and path.is_file()
        ),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )

    removed = 0
    for old_log in logs[max_log_executions:]:
        try:
            old_log.unlink()
            removed += 1
        except OSError as exc:
            print(f"Warning: could not remove old log {old_log}: {exc}", file=sys.stderr)

    return removed


def prune_master_log(master_log_path: Path, max_log_executions: int) -> None:
    """Keep only the newest execution blocks inside the master log."""

    if not master_log_path.exists():
        return

    try:
        content = master_log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Warning: could not read master log {master_log_path}: {exc}", file=sys.stderr)
        return

    parts = content.split(RUN_START_MARKER)
    preamble = parts[0]
    runs = [RUN_START_MARKER + part for part in parts[1:] if part.strip()]

    if len(runs) <= max_log_executions:
        return

    new_content = "".join(runs[-max_log_executions:])
    if preamble.strip():
        new_content = preamble + new_content

    try:
        master_log_path.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        print(f"Warning: could not prune master log {master_log_path}: {exc}", file=sys.stderr)


def log_run_header(run_started_at: datetime, project_root: Path, settings_file: Path, log_context: LogContext) -> None:
    """Record environment details at the beginning of a run."""

    logging.info(RUN_START_MARKER)
    logging.info("RSS Automation %s started", __version__)
    logging.info("Start: %s", run_started_at.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Project root: %s", project_root)
    logging.info("Settings file: %s", settings_file.resolve())
    logging.info("Master log: %s", log_context.master_log_path)
    logging.info("Run log: %s", log_context.run_log_path)
    logging.info("Python: %s %s", platform.python_version(), platform.architecture()[0])
    logging.info("Executable: %s", sys.executable)
    logging.info("OS: %s", platform.platform())


def log_run_footer(start_perf: float, stats: RunStats, exit_code: int) -> None:
    """Record final counters and elapsed time at the end of a run."""

    elapsed = time.perf_counter() - start_perf
    logging.info("Finished")
    logging.info("RSS items read: %s", stats.items_read)
    logging.info("Matched: %s", stats.matched)
    logging.info("Saved: %s", stats.saved)
    logging.info("Skipped: %s", stats.skipped)
    logging.info("Exit code: %s", exit_code)
    logging.info("Elapsed: %.2f seconds", elapsed)
    logging.info(RUN_END_MARKER)
