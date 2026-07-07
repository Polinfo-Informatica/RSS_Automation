"""Main RSS automation pipeline."""

from __future__ import annotations

import logging
import time
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from rss_automation.config_files import read_categories, read_exclusions, read_rss_sources
from rss_automation.duplicate_tracker import append_processed, load_processed, processed_key
from rss_automation.logging_config import (
    log_run_footer,
    log_run_header,
    prune_master_log,
    prune_timestamped_logs,
    setup_logging,
    shutdown_logging,
)
from rss_automation.matching import matching_categories
from rss_automation.models import CategoryRule, RssItem, RunStats, SelectedDownload
from rss_automation.output_writers import download_torrent_file
from rss_automation.rss_reader import parse_feed
from rss_automation.settings import get_project_root, load_settings, resolve_settings_path, setup_folders
from rss_automation.url_tools import redact_text, redact_url


def choose_download(item: RssItem, preference: str = "torrent") -> SelectedDownload | None:
    """Choose only a .torrent URL for Tixati watched-folder automation."""

    if item.torrent_url:
        return SelectedDownload("torrent", item.torrent_url)

    return None


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
    """Match RSS items, save selected torrent files, and update processed.txt."""

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

        selected = choose_download(item)
        if not selected:
            logging.info("Matched but no .torrent URL found: %s", item.title)
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
                saved_path = download_torrent_file(item, selected, category, paths["torrent"], settings)

                if not bool(settings["dry_run"]):
                    append_processed(processed_path, key)
                    processed.add(key)

                saved_count += 1
                logging.info("Saved torrent: [%s] %s -> %s", category, item.title, saved_path)
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
    run_started_at = datetime.now()
    start_perf = time.perf_counter()
    log_context = setup_logging(paths["log"], run_started_at)

    exit_code = 0
    stats = RunStats()

    try:
        log_run_header(run_started_at, project_root, settings_file, log_context)

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
        logging.info("RSS feeds: %s", len(rss_sources))
        logging.info("Categories: %s", ", ".join(rule.category for rule in categories))
        logging.info("Exclusions: %s", len(exclusions))
        logging.info("Download output mode: torrent-only")
        logging.info("Torrent output: %s", paths["torrent"])

        all_items: list[RssItem] = []
        failed_feeds = 0
        for source in rss_sources:
            try:
                all_items.extend(
                    parse_feed(
                        source.url,
                        int(settings["download_timeout_seconds"]),
                        str(settings["request_user_agent"]),
                        source.name,
                    )
                )
            except Exception as exc:
                failed_feeds += 1
                logging.error(
                    "Failed to read feed [%s] %s | %s: %s",
                    source.name,
                    redact_url(source.url),
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
        prune_timestamped_logs(paths["log"], max_log_executions)
        prune_master_log(log_context.master_log_path, max_log_executions)
