"""Title matching and exclusion logic."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from rss_automation.config_files import normalize_feed_name
from rss_automation.models import CategoryRule, MatchPattern, RssItem

PHRASE_SEPARATOR_RE = re.compile(r"[\s._\[\](){}<>!?,:;\"“”‘’]")


def normalize_text(text: str, case_sensitive: bool) -> str:
    """Normalize text for configured case-sensitive or insensitive matching."""

    return text if case_sensitive else text.casefold()


def normalize_exact_phrase_text(text: str, case_sensitive: bool) -> str:
    """Normalize separator characters while preserving separator count."""

    normalized = normalize_text(text, case_sensitive)
    return PHRASE_SEPARATOR_RE.sub(" ", normalized).strip()


def text_contains_exact_phrase(text: str, phrase: str, case_sensitive: bool) -> bool:
    """Return True when text contains phrase on exact token boundaries."""

    phrase_cmp = normalize_exact_phrase_text(phrase, case_sensitive)
    if not phrase_cmp:
        return False

    text_cmp = normalize_exact_phrase_text(text, case_sensitive)
    return f" {phrase_cmp} " in f" {text_cmp} "


def search_texts_from_item(item: RssItem) -> tuple[str, ...]:
    """Return RSS item fields that should be considered for matching and exclusions."""

    return tuple(text for text in (item.title, item.file_name, item.description) if text)


def normalize_search_texts(search_texts: str | RssItem | Sequence[str]) -> tuple[str, ...]:
    """Normalize one or more searchable text fields into a tuple."""

    if isinstance(search_texts, RssItem):
        return search_texts_from_item(search_texts)
    if isinstance(search_texts, str):
        return (search_texts,)

    return tuple(text for text in search_texts if text)


def title_is_excluded(title: str, exclusions: Sequence[str], case_sensitive: bool) -> bool:
    """Return True when a title contains any exact exclusion phrase."""

    return fields_are_excluded(title, exclusions, case_sensitive)


def fields_are_excluded(search_texts: str | RssItem | Sequence[str], exclusions: Sequence[str], case_sensitive: bool) -> bool:
    """Return True when any searchable field contains an exact exclusion phrase."""

    fields = normalize_search_texts(search_texts)
    return any(text_contains_exact_phrase(field, exclusion, case_sensitive) for field in fields for exclusion in exclusions)


def title_matches_pattern(title: str, pattern: str, match_mode: str, case_sensitive: bool) -> bool:
    """Match one RSS title against one configured pattern."""

    return fields_match_pattern(title, pattern, match_mode, case_sensitive)


def fields_match_pattern(
    search_texts: str | RssItem | Sequence[str], pattern: str, match_mode: str, case_sensitive: bool
) -> bool:
    """Match one configured pattern exactly against any searchable field."""

    if not pattern:
        return False

    fields = normalize_search_texts(search_texts)

    # match_mode is kept for settings compatibility, but all supported modes now use
    # boundary-aware exact phrase matching. Raw substring and regex matching are not used.
    if match_mode.lower().strip() not in {"literal", "contains"}:
        return False

    return any(text_contains_exact_phrase(field, pattern, case_sensitive) for field in fields)


def pattern_applies_to_feed(pattern: MatchPattern, feed_name: str) -> bool:
    """Return True when a scoped pattern can run against the current feed."""

    if not pattern.feed_names:
        return True

    return normalize_feed_name(feed_name) in pattern.feed_names


def iter_match_patterns(rule: CategoryRule) -> tuple[MatchPattern, ...]:
    """Return parsed match patterns, preserving compatibility with old rule objects."""

    if rule.match_patterns:
        return rule.match_patterns

    return tuple(MatchPattern(text=pattern) for pattern in rule.patterns)


def matching_categories(
    search_texts: str | RssItem | Sequence[str],
    categories: Sequence[CategoryRule],
    exclusions: Sequence[str],
    settings: dict[str, Any],
    feed_name: str = "",
) -> list[tuple[str, str]]:
    """Return category/pattern pairs matching searchable fields after exclusions."""

    case_sensitive = bool(settings["case_sensitive"])
    if fields_are_excluded(search_texts, exclusions, case_sensitive):
        return []

    matches: list[tuple[str, str]] = []
    match_mode = str(settings["match_mode"]).lower().strip()

    for rule in categories:
        for pattern in iter_match_patterns(rule):
            if not pattern_applies_to_feed(pattern, feed_name):
                continue
            if fields_match_pattern(search_texts, pattern.text, match_mode, case_sensitive):
                matches.append((rule.category, pattern.text))
                break

    return matches
