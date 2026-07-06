"""Title matching and exclusion logic."""

from __future__ import annotations

import logging
import re
from typing import Any, Sequence

from rss_automation.models import CategoryRule


def normalize_text(text: str, case_sensitive: bool) -> str:
    """Normalize text for configured case-sensitive or insensitive matching."""

    return text if case_sensitive else text.casefold()


def title_is_excluded(title: str, exclusions: Sequence[str], case_sensitive: bool) -> bool:
    """Return True when a title contains any configured exclusion term."""

    title_cmp = normalize_text(title, case_sensitive)

    for exclusion in exclusions:
        exclusion_cmp = normalize_text(exclusion, case_sensitive)
        if exclusion_cmp and exclusion_cmp in title_cmp:
            return True

    return False


def title_matches_pattern(title: str, pattern: str, match_mode: str, case_sensitive: bool) -> bool:
    """Match one RSS title against one configured pattern."""

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


def matching_categories(
    title: str,
    categories: Sequence[CategoryRule],
    exclusions: Sequence[str],
    settings: dict[str, Any],
) -> list[tuple[str, str]]:
    """Return category/pattern pairs matching a title after exclusions."""

    case_sensitive = bool(settings["case_sensitive"])
    if title_is_excluded(title, exclusions, case_sensitive):
        return []

    matches: list[tuple[str, str]] = []
    match_mode = str(settings["match_mode"]).lower().strip()

    for rule in categories:
        for pattern in rule.patterns:
            if title_matches_pattern(title, pattern, match_mode, case_sensitive):
                matches.append((rule.category, pattern))
                break

    return matches
