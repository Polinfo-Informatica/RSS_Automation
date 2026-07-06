"""RSS feed download and link extraction helpers."""

from __future__ import annotations

import logging
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

import feedparser
import requests

from rss_automation.constants import MAGNET_RE, TORRENT_RE
from rss_automation.models import RssItem
from rss_automation.url_tools import redact_url


def find_magnet_in_text(*parts: object) -> str | None:
    """Search arbitrary RSS fields for the first magnet link."""

    for part in parts:
        if not part:
            continue

        match = MAGNET_RE.search(str(part))
        if match:
            return match.group(0).rstrip("),.;]")

    return None


def find_torrent_url_in_text(*parts: object) -> str | None:
    """Search arbitrary RSS fields for the first torrent URL."""

    for part in parts:
        if not part:
            continue

        match = TORRENT_RE.search(str(part))
        if match:
            return match.group(0).rstrip("),.;]")

    return None


def text_from_entry_value(value: object) -> str:
    """Convert a feedparser value into searchable text."""

    if not value:
        return ""

    if isinstance(value, dict):
        return " ".join(text_from_entry_value(part) for part in value.values()).strip()

    if isinstance(value, (list, tuple)):
        return " ".join(text_from_entry_value(part) for part in value).strip()

    return str(value).strip()


def compact_text_parts(parts: list[object]) -> str:
    """Compact arbitrary values into one searchable string."""

    compacted: list[str] = []
    for part in parts:
        text = text_from_entry_value(part)
        if text:
            compacted.append(text)

    return " ".join(compacted).strip()


def extract_entry_description(entry: Any) -> str:
    """Extract searchable description text from common RSS fields."""

    return compact_text_parts(
        [
            getattr(entry, "summary", None),
            getattr(entry, "description", None),
            getattr(entry, "subtitle", None),
            getattr(entry, "content", None),
        ]
    )


def filename_from_url(value: str | None) -> str:
    """Extract a filename-like value from a URL path."""

    if not value:
        return ""

    path = urlsplit(value).path
    name = PurePosixPath(unquote(path)).name
    return name.strip()


def extend_link_candidates(candidates: list[object], link_obj: object) -> None:
    """Add filename-like link metadata to a candidate list."""

    if isinstance(link_obj, dict):
        href = link_obj.get("href") or link_obj.get("url")
        candidates.extend(
            [
                link_obj.get("title"),
                link_obj.get("filename"),
                href,
                filename_from_url(str(href)) if href else "",
            ]
        )
        return

    href = getattr(link_obj, "href", None) or getattr(link_obj, "url", None)
    candidates.extend(
        [
            getattr(link_obj, "title", None),
            getattr(link_obj, "filename", None),
            href,
            filename_from_url(str(href)) if href else "",
        ]
    )


def extract_link_filename(entry: Any, raw_link: str | None, torrent_url: str | None) -> str:
    """Extract filename-like text from RSS link/enclosure metadata."""

    candidates: list[object] = [
        getattr(entry, "filename", None),
        getattr(entry, "file_name", None),
        getattr(entry, "media_title", None),
        filename_from_url(torrent_url),
        filename_from_url(raw_link),
    ]

    for link_obj in getattr(entry, "links", []) or []:
        extend_link_candidates(candidates, link_obj)

    for enclosure in getattr(entry, "enclosures", []) or []:
        extend_link_candidates(candidates, enclosure)

    return compact_text_parts(candidates)


def extract_links(entry: Any) -> tuple[str | None, str | None, str | None]:
    """Extract magnet and torrent links from a feedparser entry."""

    raw_link = getattr(entry, "link", None)
    candidates: list[object] = [
        raw_link,
        getattr(entry, "id", None),
        getattr(entry, "summary", None),
        getattr(entry, "description", None),
    ]

    # Different RSS feeds expose link data in different fields.
    for attr_name in ("content", "links", "enclosures"):
        value = getattr(entry, attr_name, None)
        if value:
            candidates.append(value)

    magnet = find_magnet_in_text(*candidates)
    torrent = find_torrent_url_in_text(*candidates)

    # Structured link objects may identify torrent links by MIME type.
    for link_obj in getattr(entry, "links", []) or []:
        href = link_obj.get("href") if isinstance(link_obj, dict) else getattr(link_obj, "href", None)
        link_type = link_obj.get("type") if isinstance(link_obj, dict) else getattr(link_obj, "type", None)

        if not href:
            continue

        href_text = str(href)
        if not magnet and href_text.lower().startswith("magnet:"):
            magnet = href_text
        if not torrent and (href_text.lower().endswith(".torrent") or "bittorrent" in str(link_type).lower()):
            torrent = href_text

    if not torrent and raw_link and str(raw_link).lower().endswith(".torrent"):
        torrent = str(raw_link)

    return magnet, torrent, str(raw_link) if raw_link else None


def parse_feed(feed_url: str, timeout: int, user_agent: str, feed_name: str = "") -> list[RssItem]:
    """Download and parse one RSS feed into normalized RSS items."""

    headers = {"User-Agent": user_agent}
    safe_feed_url = redact_url(feed_url)
    source_label = f" [{feed_name}]" if feed_name else ""
    logging.info("Reading RSS feed%s: %s", source_label, safe_feed_url)

    response = requests.get(feed_url, timeout=timeout, headers=headers)
    response.raise_for_status()

    parsed = feedparser.parse(response.content)
    if parsed.bozo:
        logging.warning("Feed parser warning for %s: %s", safe_feed_url, parsed.bozo_exception)

    items: list[RssItem] = []
    for entry in parsed.entries:
        title = str(getattr(entry, "title", "")).strip()
        if not title:
            continue

        magnet, torrent, raw_link = extract_links(entry)
        identifier = str(getattr(entry, "id", "") or getattr(entry, "guid", "") or raw_link or title).strip()
        description = extract_entry_description(entry)
        file_name = extract_link_filename(entry, raw_link, torrent)

        items.append(
            RssItem(
                feed_url=feed_url,
                title=title,
                identifier=identifier,
                magnet=magnet,
                torrent_url=torrent,
                raw_link=raw_link,
                feed_name=feed_name,
                file_name=file_name,
                description=description,
            )
        )

    return items
