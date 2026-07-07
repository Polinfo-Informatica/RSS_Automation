"""Project constants and default settings."""

from __future__ import annotations

import re
from typing import Any

from rss_automation import __version__

APP_VERSION = __version__

MASTER_LOG_NAME = "RSS_Automation.log"
RUN_LOG_PREFIX = "RSS_Automation_"
RUN_LOG_SUFFIX = ".log"
RUN_START_MARKER = "==================== RSS_AUTOMATION_RUN_START ===================="
RUN_END_MARKER = "===================== RSS_AUTOMATION_RUN_END ====================="

RESERVED_CONFIG_FILES = frozenset({"rss.txt", "exclude.txt", "processed.txt"})
PATH_SETTING_KEYS = frozenset(
    {
        "root_folder",
        "config_folder",
        "magnet_output_folder",
        "torrent_output_folder",
        "log_folder",
        "config_backup_folder",
    }
)

MAGNET_RE = re.compile(r"magnet:\?[^\s\"'<>]+", re.IGNORECASE)
TORRENT_RE = re.compile(r"https?://[^\s\"'<>]+?\.torrent(?:\?[^\s\"'<>]*)?", re.IGNORECASE)
INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MULTISPACE_RE = re.compile(r"\s+")

DEFAULT_SETTINGS: dict[str, Any] = {
    "root_folder": "${downloads_folder}\\RSS_Automation",
    "config_folder": "${root_folder}\\RSS_Config",
    "magnet_output_folder": "${root_folder}\\RSS_Magnet",
    "torrent_output_folder": "${root_folder}\\RSS_Torrent",
    "log_folder": "${root_folder}\\Logs",
    "config_backup_folder": "${root_folder}\\RSS_Config_Backups",
    "rss_file": "rss.txt",
    "exclude_file": "exclude.txt",
    "processed_file": "processed.txt",
    "prefer_download_type": "torrent",
    "match_mode": "literal",
    "case_sensitive": False,
    "skip_duplicates": True,
    "download_timeout_seconds": 30,
    "feed_retry_attempts": 3,
    "feed_retry_delay_seconds": 10,
    "scan_interval_seconds": 300,
    "request_user_agent": f"RSS_Automation/{APP_VERSION}",
    "write_magnet_format": "title_and_magnet",
    "backup_config_on_run": True,
    "backup_config_once_per_day": True,
    "archive_7z_command": "",
    "max_config_backups": 50,
    "max_log_executions": 100,
    "dry_run": False,
}
