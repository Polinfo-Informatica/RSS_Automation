"""Writers for Tixati import outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from rss_automation.filename_tools import extension_from_url, magnet_hash, sanitize_filename, short_hash
from rss_automation.models import RssItem, SelectedDownload


def save_magnet(
    item: RssItem,
    selected: SelectedDownload,
    category: str,
    output_folder: Path,
    settings: dict[str, Any],
) -> Path:
    """Write one .magnet file directly into the watched import folder."""

    magnet_id = magnet_hash(selected.value)
    title_part = sanitize_filename(item.title, 130)
    category_part = sanitize_filename(category, 40)
    path = output_folder / f"{category_part} - {title_part} - {magnet_id}.magnet"

    if path.exists():
        return path

    if bool(settings["dry_run"]):
        return path

    # Tixati can load .magnet files from the watched Meta-Info folder when
    # "Load magnet links from .magnet, .url and .desktop files" is enabled.
    # Keep the file content minimal for maximum parser compatibility.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(selected.value + "\n", encoding="utf-8")
    tmp_path.replace(path)

    return path


def download_torrent_file(
    item: RssItem,
    selected: SelectedDownload,
    category: str,
    output_folder: Path,
    settings: dict[str, Any],
) -> Path:
    """Download one torrent payload directly into the watched import folder."""

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
