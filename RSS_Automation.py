#!/usr/bin/env python3
"""
RSS Automation v0.0.1.a

Reads RSS feeds, matches titles against category TXT files, applies global exclusions,
and saves either magnet links or .torrent files for Tixati to consume.

Default layout:
    D:\Root\Downloads\RSS_Config\rss.txt
    D:\Root\Downloads\RSS_Config\exclude.txt
    D:\Root\Downloads\RSS_Config\anime.txt
    D:\Root\Downloads\RSS_Magnet\
    D:\Root\Downloads\RSS_Torrent\
    D:\Root\Downloads\Logs\

Important:
    No category subfolders are created inside RSS_Magnet or RSS_Torrent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qs, unquote, urlparse

import feedparser
import requests

APP_VERSION = "v0.0.1.a"
DEFAULT_SETTINGS = {
    "root_folder": "D:\\Root\\Downloads",
    "config_folder": "D:\\Root\\Downloads\\RSS_Config",
    "magnet_output_folder": "D:\\Root\\Downloads\\RSS_Magnet",
    "torrent_output_folder": "D:\\Root\\Downloads\\RSS_Torrent",
    "log_folder": "D:\\Root\\Downloads\\Logs",
    "rss_file": "rss.txt",
    "exclude_file": "exclude.txt",
    "processed_file": "processed.txt",
    "prefer_download_type": "magnet",
    "match_mode": "contains",
    "case_sensitive": False,
    "skip_duplicates": True,
    "download_timeout_seconds": 30,
    "request_user_agent": "RSS_Automation/0.0.1.a",
    "write_magnet_format": "title_and_magnet",
    "dry_run": False,
}
RESERVED_CONFIG_FILES = {"rss.txt", "exclude.txt", "processed.txt"}
MAGNET_RE = re.compile(r"magnet:\?[^\s\"'<>]+", re.IGNORECASE)
TORRENT_RE = re.compile(r"https?://[^\s\"'<>]+?\.torrent(?:\?[^\s\"'<>]*)?", re.IGNORECASE)
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass(frozen=True)
class CategoryRule:
    category: str
    source_file: Path
    patterns: Tuple[str, ...]


@dataclass(frozen=True)
class RssItem:
    feed_url: str
    title: str
    identifier: str
    magnet: Optional[str]
    torrent_url: Optional[str]
    raw_link: Optional[str]


@dataclass(frozen=True)
class SelectedDownload:
    kind: str
    value: str


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        settings_path.write_text(json.dumps(DEFAULT_SETTINGS, indent=4, ensure_ascii=False), encoding="utf-8")
        return dict(DEFAULT_SETTINGS)

    with settings_path.open("r", encoding="utf-8-sig") as f:
        loaded = json.load(f)

    settings = dict(DEFAULT_SETTINGS)
    settings.update(loaded)
    validate_settings(settings)
    return settings


def validate_settings(settings: dict) -> None:
    prefer = str(settings.get("prefer_download_type", "magnet")).lower().strip()
    if prefer not in {"magnet", "torrent"}:
        raise ValueError('settings.json: "prefer_download_type" must be "magnet" or "torrent".')

    match_mode = str(settings.get("match_mode", "contains")).lower().strip()
    if match_mode not in {"contains", "exact", "regex"}:
        raise ValueError('settings.json: "match_mode" must be "contains", "exact", or "regex".')

    magnet_format = str(settings.get("write_magnet_format", "title_and_magnet")).lower().strip()
    if magnet_format not in {"magnet_only", "title_and_magnet"}:
        raise ValueError('settings.json: "write_magnet_format" must be "magnet_only" or "title_and_magnet".')


def setup_folders(settings: dict) -> Dict[str, Path]:
    paths = {
        "root": Path(settings["root_folder"]),
        "config": Path(settings["config_folder"]),
        "magnet": Path(settings["magnet_output_folder"]),
        "torrent": Path(settings["torrent_output_folder"]),
        "log": Path(settings["log_folder"]),
    }

    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    rss_file = paths["config"] / settings["rss_file"]
    exclude_file = paths["config"] / settings["exclude_file"]
    if not rss_file.exists():
        rss_file.write_text("# Put one RSS feed URL per line.\n", encoding="utf-8")
    if not exclude_file.exists():
        exclude_file.write_text("# Put one exclusion keyword per line.\n", encoding="utf-8")

    sample_category = paths["config"] / "anime.txt"
    if not sample_category.exists():
        sample_category.write_text("# Put one title/pattern per line.\n# Example:\n# One Piece\n", encoding="utf-8")

    return paths


def setup_logging(log_folder: Path) -> None:
    log_file = log_folder / "RSS_Automation.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def read_clean_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    lines: List[str] = []
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)
    return lines


def read_rss_urls(config_folder: Path, rss_file_name: str) -> List[str]:
    path = config_folder / rss_file_name
    urls = read_clean_lines(path)
    valid = [u for u in urls if u.lower().startswith(("http://", "https://"))]
    skipped = len(urls) - len(valid)
    if skipped:
        logging.warning("Ignored %s invalid RSS line(s) in %s", skipped, path)
    return valid


def read_exclusions(config_folder: Path, exclude_file_name: str) -> List[str]:
    return read_clean_lines(config_folder / exclude_file_name)


def read_categories(config_folder: Path) -> List[CategoryRule]:
    rules: List[CategoryRule] = []
    for path in sorted(config_folder.glob("*.txt")):
        if path.name.lower() in RESERVED_CONFIG_FILES:
            continue
        patterns = tuple(read_clean_lines(path))
        if not patterns:
            continue
        rules.append(CategoryRule(category=path.stem, source_file=path, patterns=patterns))
    return rules


def normalize_text(text: str, case_sensitive: bool) -> str:
    return text if case_sensitive else text.casefold()


def title_is_excluded(title: str, exclusions: Sequence[str], case_sensitive: bool) -> bool:
    title_cmp = normalize_text(title, case_sensitive)
    for exclusion in exclusions:
        exclusion_cmp = normalize_text(exclusion, case_sensitive)
        if exclusion_cmp and exclusion_cmp in title_cmp:
            return True
    return False


def title_matches_pattern(title: str, pattern: str, match_mode: str, case_sensitive: bool) -> bool:
    if not pattern:
        return False

    if match_mode == "regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return re.search(pattern, title, flags) is not None
        except re.error as exc:
            logging.warning("Invalid regex ignored: %r | %s", pattern, exc)
            return False

    title_cmp = normalize_text(title, case_sensitive)
    pattern_cmp = normalize_text(pattern, case_sensitive)

    if match_mode == "exact":
        return title_cmp == pattern_cmp

    return pattern_cmp in title_cmp


def matching_categories(title: str, categories: Sequence[CategoryRule], exclusions: Sequence[str], settings: dict) -> List[Tuple[str, str]]:
    if title_is_excluded(title, exclusions, bool(settings["case_sensitive"])):
        return []

    matches: List[Tuple[str, str]] = []
    match_mode = str(settings["match_mode"]).lower().strip()
    case_sensitive = bool(settings["case_sensitive"])

    for rule in categories:
        for pattern in rule.patterns:
            if title_matches_pattern(title, pattern, match_mode, case_sensitive):
                matches.append((rule.category, pattern))
                break
    return matches


def sanitize_filename(value: str, max_length: int = 160) -> str:
    value = unquote(value).strip()
    value = INVALID_FILENAME_CHARS.sub("_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    if not value:
        value = "download"
    return value[:max_length].rstrip(" .")


def short_hash(value: str, length: int = 12) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:length]


def magnet_hash(magnet: str) -> str:
    parsed = urlparse(magnet)
    qs = parse_qs(parsed.query)
    xt_values = qs.get("xt", [])
    for xt in xt_values:
        lowered = xt.lower()
        if lowered.startswith("urn:btih:"):
            return sanitize_filename(xt.split(":")[-1], 80)
    return short_hash(magnet, 20)


def extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    if name.lower().endswith(".torrent"):
        return ".torrent"
    return ".torrent"


def unique_path(folder: Path, filename: str) -> Path:
    candidate = folder / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    for i in range(2, 10000):
        alt = folder / f"{stem} ({i}){suffix}"
        if not alt.exists():
            return alt
    raise RuntimeError(f"Could not create unique filename for {candidate}")


def find_magnet_in_text(*parts: object) -> Optional[str]:
    for part in parts:
        if not part:
            continue
        text = str(part)
        match = MAGNET_RE.search(text)
        if match:
            return match.group(0).rstrip("),.;]")
    return None


def find_torrent_url_in_text(*parts: object) -> Optional[str]:
    for part in parts:
        if not part:
            continue
        text = str(part)
        match = TORRENT_RE.search(text)
        if match:
            return match.group(0).rstrip("),.;]")
    return None


def extract_links(entry) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    raw_link = getattr(entry, "link", None)
    candidates: List[object] = [raw_link, getattr(entry, "id", None), getattr(entry, "summary", None), getattr(entry, "description", None)]

    for attr in ("content", "links", "enclosures"):
        value = getattr(entry, attr, None)
        if value:
            candidates.append(value)

    magnet = find_magnet_in_text(*candidates)
    torrent = find_torrent_url_in_text(*candidates)

    links = getattr(entry, "links", []) or []
    for link_obj in links:
        href = link_obj.get("href") if isinstance(link_obj, dict) else getattr(link_obj, "href", None)
        link_type = link_obj.get("type") if isinstance(link_obj, dict) else getattr(link_obj, "type", None)
        if href:
            if not magnet and href.lower().startswith("magnet:"):
                magnet = href
            if not torrent and (href.lower().endswith(".torrent") or "bittorrent" in str(link_type).lower()):
                torrent = href

    if not torrent and raw_link and str(raw_link).lower().endswith(".torrent"):
        torrent = str(raw_link)

    return magnet, torrent, raw_link


def parse_feed(feed_url: str, timeout: int, user_agent: str) -> List[RssItem]:
    headers = {"User-Agent": user_agent}
    logging.info("Reading RSS feed: %s", feed_url)
    response = requests.get(feed_url, timeout=timeout, headers=headers)
    response.raise_for_status()

    parsed = feedparser.parse(response.content)
    if parsed.bozo:
        logging.warning("Feed parser warning for %s: %s", feed_url, parsed.bozo_exception)

    items: List[RssItem] = []
    for entry in parsed.entries:
        title = str(getattr(entry, "title", "")).strip()
        if not title:
            continue
        magnet, torrent, raw_link = extract_links(entry)
        identifier = str(getattr(entry, "id", "") or getattr(entry, "guid", "") or raw_link or title).strip()
        items.append(RssItem(feed_url=feed_url, title=title, identifier=identifier, magnet=magnet, torrent_url=torrent, raw_link=raw_link))
    return items


def choose_download(item: RssItem, preference: str) -> Optional[SelectedDownload]:
    preference = preference.lower().strip()
    if item.magnet and item.torrent_url:
        if preference == "torrent":
            return SelectedDownload("torrent", item.torrent_url)
        return SelectedDownload("magnet", item.magnet)
    if item.magnet:
        return SelectedDownload("magnet", item.magnet)
    if item.torrent_url:
        return SelectedDownload("torrent", item.torrent_url)
    return None


def load_processed(path: Path) -> Set[str]:
    return set(read_clean_lines(path))


def append_processed(path: Path, key: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")


def processed_key(item: RssItem, selected: SelectedDownload, category: str) -> str:
    if selected.kind == "magnet":
        payload = magnet_hash(selected.value)
    else:
        payload = selected.value
    return short_hash(f"{category}|{selected.kind}|{payload}|{item.identifier}", 32)


def save_magnet(item: RssItem, selected: SelectedDownload, category: str, pattern: str, output_folder: Path, settings: dict) -> Path:
    mhash = magnet_hash(selected.value)
    title_part = sanitize_filename(item.title, 130)
    category_part = sanitize_filename(category, 40)
    filename = f"{category_part} - {title_part} - {mhash}.magnet"
    path = output_folder / filename

    if path.exists():
        return path

    if str(settings["write_magnet_format"]).lower().strip() == "magnet_only":
        content = selected.value + "\n"
    else:
        content = (
            f"# Title: {item.title}\n"
            f"# Category: {category}\n"
            f"# Matched: {pattern}\n"
            f"# Feed: {item.feed_url}\n"
            f"# Created: {datetime.now().isoformat(timespec='seconds')}\n"
            f"{selected.value}\n"
        )

    if not bool(settings["dry_run"]):
        path.write_text(content, encoding="utf-8")
    return path


def download_torrent(item: RssItem, selected: SelectedDownload, category: str, pattern: str, output_folder: Path, settings: dict) -> Path:
    title_part = sanitize_filename(item.title, 130)
    category_part = sanitize_filename(category, 40)
    url_hash = short_hash(selected.value, 12)
    filename = f"{category_part} - {title_part} - {url_hash}{extension_from_url(selected.value)}"
    path = output_folder / filename

    if path.exists():
        return path

    if bool(settings["dry_run"]):
        return path

    headers = {"User-Agent": settings["request_user_agent"]}
    response = requests.get(selected.value, timeout=int(settings["download_timeout_seconds"]), headers=headers)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if response.content[:1] != b"d" and "torrent" not in content_type and len(response.content) < 64:
        logging.warning("Downloaded torrent looks suspiciously small: %s", selected.value)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(response.content)
    tmp_path.replace(path)
    return path


def process_items(items: Sequence[RssItem], categories: Sequence[CategoryRule], exclusions: Sequence[str], paths: Dict[str, Path], settings: dict) -> Tuple[int, int, int]:
    processed_path = paths["config"] / settings["processed_file"]
    processed = load_processed(processed_path)

    matched_count = 0
    saved_count = 0
    skipped_count = 0

    for item in items:
        matches = matching_categories(item.title, categories, exclusions, settings)
        if not matches:
            continue

        selected = choose_download(item, str(settings["prefer_download_type"]))
        if not selected:
            logging.info("Matched but no magnet/torrent found: %s", item.title)
            skipped_count += 1
            continue

        for category, pattern in matches:
            matched_count += 1
            key = processed_key(item, selected, category)
            if bool(settings["skip_duplicates"]) and key in processed:
                logging.info("Duplicate skipped: [%s] %s", category, item.title)
                skipped_count += 1
                continue

            try:
                if selected.kind == "magnet":
                    saved_path = save_magnet(item, selected, category, pattern, paths["magnet"], settings)
                else:
                    saved_path = download_torrent(item, selected, category, pattern, paths["torrent"], settings)

                if not bool(settings["dry_run"]):
                    append_processed(processed_path, key)
                    processed.add(key)
                saved_count += 1
                logging.info("Saved %s: [%s] %s -> %s", selected.kind, category, item.title, saved_path)
            except Exception as exc:
                logging.exception("Failed to save [%s] %s | %s", category, item.title, exc)
                skipped_count += 1

    return matched_count, saved_count, skipped_count


def run_once(settings_path: Path) -> int:
    settings = load_settings(settings_path)
    paths = setup_folders(settings)
    setup_logging(paths["log"])

    logging.info("RSS Automation %s started", APP_VERSION)
    logging.info("Settings file: %s", settings_path.resolve())

    rss_urls = read_rss_urls(paths["config"], settings["rss_file"])
    exclusions = read_exclusions(paths["config"], settings["exclude_file"])
    categories = read_categories(paths["config"])

    if not rss_urls:
        logging.error("No RSS URLs found. Edit %s", paths["config"] / settings["rss_file"])
        return 2
    if not categories:
        logging.error("No category TXT files with patterns found in %s", paths["config"])
        return 2

    logging.info("RSS feeds: %s", len(rss_urls))
    logging.info("Categories: %s", ", ".join(rule.category for rule in categories))
    logging.info("Exclusions: %s", len(exclusions))
    logging.info("Preference: %s", settings["prefer_download_type"])
    logging.info("Magnet output: %s", paths["magnet"])
    logging.info("Torrent output: %s", paths["torrent"])

    all_items: List[RssItem] = []
    for feed_url in rss_urls:
        try:
            all_items.extend(parse_feed(feed_url, int(settings["download_timeout_seconds"]), str(settings["request_user_agent"])))
        except Exception as exc:
            logging.exception("Failed to read feed %s | %s", feed_url, exc)

    matched, saved, skipped = process_items(all_items, categories, exclusions, paths, settings)
    logging.info("Finished. RSS items=%s matched=%s saved=%s skipped=%s", len(all_items), matched, saved, skipped)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=f"RSS Automation {APP_VERSION}")
    parser.add_argument("--settings", default="settings.json", help="Path to settings.json. Default: settings.json")
    parser.add_argument("--loop", action="store_true", help="Run continuously using scan_interval_seconds from settings.json.")
    args = parser.parse_args(argv)

    settings_path = Path(args.settings)

    if not args.loop:
        return run_once(settings_path)

    while True:
        try:
            settings = load_settings(settings_path)
            interval = int(settings.get("scan_interval_seconds", 300))
            code = run_once(settings_path)
            if code not in {0, 2}:
                logging.warning("Run finished with code %s", code)
            time.sleep(max(30, interval))
        except KeyboardInterrupt:
            print("Stopped by user.")
            return 0
        except Exception as exc:
            print(f"Fatal loop error: {exc}", file=sys.stderr)
            time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
