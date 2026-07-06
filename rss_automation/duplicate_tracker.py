"""Duplicate-prevention helpers backed by processed.txt."""

from __future__ import annotations

from pathlib import Path

from rss_automation.config_files import read_clean_lines
from rss_automation.filename_tools import magnet_hash, short_hash
from rss_automation.models import RssItem, SelectedDownload


def load_processed(path: Path) -> set[str]:
    """Load already processed item keys from processed.txt."""

    return set(read_clean_lines(path))


def append_processed(path: Path, key: str) -> None:
    """Append one processed item key to processed.txt."""

    with path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(key + "\n")


def processed_key(item: RssItem, selected: SelectedDownload, category: str) -> str:
    """Build a stable duplicate key for one item, category, and output type."""

    payload = magnet_hash(selected.value) if selected.kind == "magnet" else selected.value
    return short_hash(f"{category}|{selected.kind}|{payload}|{item.identifier}", 32)
