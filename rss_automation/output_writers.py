"""Writers for magnet and torrent outputs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from rss_automation.filename_tools import extension_from_url, magnet_hash, sanitize_filename, short_hash
from rss_automation.models import RssItem, SelectedDownload


def save_magnet(
    item: RssItem,
    selected: SelectedDownload,
    category: str,
    pattern: str,
    output_folder: Path,
    settings: dict[str, Any],
) -> Path:
    """Write one .magnet file directly into the flat magnet output folder."""

    magnet_id = magnet_hash(selected.value)
    title_part = sanitize_filename(item.title, 130)
    category_part = sanitize_filename(category, 40)
    path = output_folder / f"{category_part} - {title_part} - {magnet_id}.magnet"

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


def download_torrent_file(
    item: RssItem,
    selected: SelectedDownload,
    category: str,
    output_folder: Path,
    settings: dict[str, Any],
) -> Path:
    """Download one torrent payload directly into the flat torrent folder."""

    title_part = sanitize_filename(item.title, 130)
    category_part = sanitize_filename(category, 40)
    url_hash = short_hash(selected.value, 12)
    path = output_folder / f"{category_part} - {title_part} - {url_hash}{extension_from_url(selected.value)}"

    if path.exists():
        return path

    if bool(settings["dry_run"]):
        return path

    headers = {"User-Agent": str(settings["request_user_agent"])}
    response = requests.get(selected.value, timeout=int(settings["download_timeout_seconds"]), headers=headers)
    response.raise_for_status()

    # Atomic write: write a temporary file first so file watchers do not see a
    # partially written payload.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(response.content)
    tmp_path.replace(path)

    return path
