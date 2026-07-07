"""Writers for torrent outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from rss_automation.filename_tools import extension_from_url, sanitize_filename, short_hash
from rss_automation.models import RssItem, SelectedDownload


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
