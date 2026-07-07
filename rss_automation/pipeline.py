"""Main RSS automation pipeline."""

from __future__ import annotations

import logging
import time
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from rss_automation.archive_7z import archive_log_folder, warn_archive_failure
from rss_automation.config_backup import backup_config_folder
from rss_automation.config_files import read_categories, read_exclusions, read_rss_sources
from rss_automation.duplicate_tracker import append_processed, load_processed, processed_key
from rss_automation.logging_config import (
    log_run_footer,
    log_run_header,
    setup_logging,
    shutdown_logging,
)
from rss_automation.matching import matching_categories
from rss_automation.models import CategoryRule, FeedSource, RssItem, RunStats, SelectedDownload
from rss_automation.output_writers import download_torrent_file, save_magnet
from rss_automation.rss_reader import parse_feed
from rss_automation.settings import get_project_root, load_settings, resolve_settings_path, setup_folders
from rss_automation.url_tools import redact_text, redact_url


def choose_download(item: RssItem, preference: str = "torrent") -> SelectedDownload | None:
    """Choose torrent or magnet output, preferring .torrent for Tixati imports."""

    preference = preference.lower().strip()

    if item.magnet and item.torrent_url:
        if preference == "magnet":
            return SelectedDownload("magnet", item.magnet)
        return SelectedDownload("torrent", item.torrent_url)

    if item.torrent_url:
        return SelectedDownload("torrent", item.torrent_url)
    if item.magnet:
        return SelectedDownload("magnet", item.magnet)

    return None


def read_feed_with_retries(source: FeedSource, settings: dict[str, Any]) -> list[RssItem]:
    """Read one RSS feed with configurable retry attempts."""

    attempts = int(settings["feed_retry_attempts"])
    retry_delay_seconds = int(settings["feed_retry_delay_seconds"])
    timeout = int(settings["download_timeout_seconds"])
    user_agent = str(settings["request_user_agent"])

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return parse_feed(source.url, timeout, user_agent, source.name)
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts:
                break

            logging.warning(
                "RSS feed read failed [%s], attempt %s of %s | %s: %s",
                source.name,
                attempt,
                attempts,
                type(exc).__name__,
                redact_text(str(exc)),
            )

            if retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)

    assert last_exc is not None
    raise last_exc


def log_duplicate_summary(duplicates_by_category: Counter[str]) -> None:
    """Log one duplicate summary instead of one line per skipped item."""

    total = duplicates_by_category.total()
    if total == 0:
        return

    details = ", ".join(f"{category}: {count}" for category, count in sorted(duplicates_by_category.items()))
    logging.info("Duplicate skipped: %s total (%s)", total, details)


def process_items(
    items: Sequence[RssItem],
    categories: Sequence[CategoryRule],
    exclusions: Sequence[str],
    paths: dict[str, Path],
    settings: dict[str, Any],
) -> RunStats:
    """Match RSS items, save selected Tixati import files, and update processed.txt."""

    processed_path = paths["config"] / str(settings["processed_file"])
    processed = load_processed(processed_path)

    matched_count = 0
    saved_count = 0
    skipped_count = 0
    duplicates_by_category: Counter[str] = Counter()

    for item in items:
        matches = matching_categories(item, categories, exclusions, settings, item.feed_name)
        if not matches:
            continue

        selected = choose_download(item, str(settings["prefer_download_type"]))
        if not selected:
            logging.info("Matched but no magnet/torrent found: %s", item.title)
            skipped_count += 1
            continue

        for category, _pattern in matches:
            matched_count += 1
            key = processed_key(item, selected, category)

            if bool(settings["skip_duplicates"]) and key in processed:
                duplicates_by_category[category] += 1
                skipped_count += 1
                continue

            try:
                if selected.kind == "magnet":
                    saved_path = save_magnet(item, selected, category, paths["torrent"], settings)
                else:
                    saved_path = download_torrent_file(item, selected, category, paths["torrent"], settings)

                if not bool(settings["dry_run"]):
                    append_processed(processed_path, key)
                    processed.add(key)

                saved_count += 1
                logging.info("Saved %s: [%s] %s -> %s", selected.kind, category, item.title, saved_path)
            except Exception as exc:
                logging.error(
                    "Failed to save [%s] %s | %s: %s", category, item.title, type(exc).__name__, redact_text(str(exc))
                )
                skipped_count += 1

    log_duplicate_summary(duplicates_by_category)
    return RunStats(items_read=len(items), matched=matched_count, saved=saved_count, skipped=skipped_count)


def run_once(settings_path: Path) -> int:
    """Execute one complete RSS scan."""

    project_root = get_project_root()
    settings_file = resolve_settings_path(settings_path, project_root)
    settings = load_settings(settings_file, project_root)
    paths = setup_folders(settings)

    max_log_executions = int(settings.get("max_log_executions", 100))
    archive_command = str(settings.get("archive_7z_command", ""))
    run_started_at = datetime.now()
    start_perf = time.perf_counter()
    log_context = setup_logging(paths["log"], run_started_at)

    exit_code = 0
    stats = RunStats()

    try:
        log_run_header(run_started_at, project_root, settings_file, log_context)

        if bool(settings["backup_config_on_run"]):
            try:
                backup_config_folder(
                    paths["config"],
                    paths["config_backup"],
                    run_started_at,
                    int(settings["max_config_backups"]),
                    archive_command=archive_command,
                )
            except Exception as exc:
                warn_archive_failure("config backups", exc)

        rss_sources = read_rss_sources(paths["config"], str(settings["rss_file"]))
        exclusions = read_exclusions(paths["config"], str(settings["exclude_file"]))
        categories = read_categories(paths["config"])

        if not rss_sources:
            logging.error("No RSS URLs found. Edit %s", paths["config"] / str(settings["rss_file"]))
            exit_code = 2
            return exit_code

        if not categories:
            logging.error("No category TXT files with patterns found in %s", paths["config"])
            exit_code = 2
            return exit_code

        logging.info("Config folder: %s", paths["config"])
        logging.info("Config backup archive folder: %s", paths["config_backup"])
        logging.info("Log archive folder: %s", paths["log"])
        logging.info("RSS feeds: %s", len(rss_sources))
        logging.info("Feed retry attempts: %s", settings["feed_retry_attempts"])
        logging.info("Categories: %s", ", ".join(rule.category for rule in categories))
        logging.info("Exclusions: %s", len(exclusions))
        logging.info("Download preference: %s", settings["prefer_download_type"])
        logging.info("Tixati import output: %s", paths["torrent"])

        all_items: list[RssItem] = []
        failed_feeds = 0
        for source in rss_sources:
            try:
                all_items.extend(read_feed_with_retries(source, settings))
            except Exception as exc:
                failed_feeds += 1
                logging.error(
                    "Failed to read feed [%s] %s after %s attempt(s) | %s: %s",
                    source.name,
                    redact_url(source.url),
                    settings["feed_retry_attempts"],
                    type(exc).__name__,
                    redact_text(str(exc)),
                )

        if failed_feeds == len(rss_sources):
            logging.error("All configured RSS feeds failed.")
            exit_code = 2
            return exit_code

        stats = process_items(all_items, categories, exclusions, paths, settings)
        exit_code = 0
        return exit_code
    except Exception:
        exit_code = 1
        logging.exception("Unexpected fatal error during execution.")
        return exit_code
    finally:
        log_run_footer(start_perf, stats, exit_code)
        shutdown_logging()
        try:
            archive_log_folder(paths["log"], max_log_executions, command=archive_command)
        except Exception as exc:
            warn_archive_failure("logs", exc)
