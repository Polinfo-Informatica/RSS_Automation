"""Filename sanitization and stable hash helpers."""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qs, unquote, urlparse

from rss_automation.constants import INVALID_FILENAME_CHARS_RE, MULTISPACE_RE


def sanitize_filename(value: str, max_length: int = 160) -> str:
    """Convert arbitrary RSS text into a safe Windows filename segment."""

    cleaned = unquote(value).strip()
    cleaned = INVALID_FILENAME_CHARS_RE.sub("_", cleaned)
    cleaned = MULTISPACE_RE.sub(" ", cleaned).strip(" .")

    if not cleaned:
        cleaned = "download"

    return cleaned[:max_length].rstrip(" .")


def short_hash(value: str, length: int = 12) -> str:
    """Return a short stable SHA-1 digest."""

    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:length]


def magnet_hash(magnet: str) -> str:
    """Extract BTIH from a magnet URI, or hash the whole URI as fallback."""

    parsed = urlparse(magnet)
    query = parse_qs(parsed.query)

    for xt_value in query.get("xt", []):
        if xt_value.lower().startswith("urn:btih:"):
            return sanitize_filename(xt_value.split(":")[-1], 80)

    return short_hash(magnet, 20)


def extension_from_url(url: str) -> str:
    """Return the extension used when saving a torrent payload."""

    return ".torrent"
