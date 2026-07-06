"""RSS feed download and link extraction helpers."""

from __future__ import annotations

import logging
from typing import Any

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


def parse_feed(feed_url: str, timeout: int, user_agent: str) -> list[RssItem]:
    """Download and parse one RSS feed into normalized RSS items."""

    headers = {"User-Agent": user_agent}
    safe_feed_url = redact_url(feed_url)
    logging.info("Reading RSS feed: %s", safe_feed_url)

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

        items.append(
            RssItem(
                feed_url=feed_url,
                title=title,
                identifier=identifier,
                magnet=magnet,
                torrent_url=torrent,
                raw_link=raw_link,
            )
        )

    return items
