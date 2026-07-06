"""Typed data models used by the RSS automation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CategoryRule:
    """A category TXT file and the match patterns loaded from it."""

    category: str
    source_file: Path
    patterns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RssItem:
    """Normalized data extracted from one RSS entry."""

    feed_url: str
    title: str
    identifier: str
    magnet: str | None
    torrent_url: str | None
    raw_link: str | None


@dataclass(frozen=True, slots=True)
class SelectedDownload:
    """The chosen downloadable value for one RSS item."""

    kind: str
    value: str


@dataclass(frozen=True, slots=True)
class LogContext:
    """Resolved log files for one execution."""

    run_started_at: datetime
    master_log_path: Path
    run_log_path: Path


@dataclass(frozen=True, slots=True)
class RunStats:
    """Counters reported in the final run summary."""

    items_read: int = 0
    matched: int = 0
    saved: int = 0
    skipped: int = 0
