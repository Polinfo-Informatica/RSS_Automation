"""Title matching and exclusion logic."""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from typing import Any

from rss_automation.config_files import normalize_feed_name
from rss_automation.models import CategoryRule, MatchPattern, RssItem


def normalize_text(text: str, case_sensitive: bool) -> str:
    """Normalize text for configured case-sensitive or insensitive matching."""

    return text if case_sensitive else text.casefold()


def text_contains_literal_phrase(text: str, phrase: str, case_sensitive: bool) -> bool:
    """Return True when text contains the exact literal phrase, including spaces."""

    phrase_cmp = normalize_text(phrase, case_sensitive)
    if not phrase_cmp:
        return False

    return phrase_cmp in normalize_text(text, case_sensitive)


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
    """Return True when a title contains any literal exclusion phrase."""

    return fields_are_excluded(title, exclusions, case_sensitive)


def fields_are_excluded(search_texts: str | RssItem | Sequence[str], exclusions: Sequence[str], case_sensitive: bool) -> bool:
    """Return True when any searchable field contains an exclusion phrase."""

    fields = normalize_search_texts(search_texts)
    return any(
        text_contains_literal_phrase(field, exclusion, case_sensitive)
        for field in fields
        for exclusion in exclusions
    )


def title_matches_pattern(title: str, pattern: str, match_mode: str, case_sensitive: bool) -> bool:
    """Match one RSS title against one configured pattern."""

    return fields_match_pattern(title, pattern, match_mode, case_sensitive)


def fields_match_pattern(
    search_texts: str | RssItem | Sequence[str], pattern: str, match_mode: str, case_sensitive: bool
) -> bool:
    """Match one configured pattern against any searchable field."""

    if not pattern:
        return False

    fields = normalize_search_texts(search_texts)
    match_mode = match_mode.lower().strip()

    if match_mode == "regex":
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            return any(re.search(pattern, field, flags) is not None for field in fields)
        except re.error as exc:
            logging.warning("Invalid regex ignored: %r | %s", pattern, exc)
            return False

    pattern_cmp = normalize_text(pattern, case_sensitive)

    if match_mode == "exact":
        return any(normalize_text(field, case_sensitive) == pattern_cmp for field in fields)

    # "literal" is the default. "contains" remains as a backward-compatible alias.
    if match_mode in {"literal", "contains"}:
        return any(text_contains_literal_phrase(field, pattern, case_sensitive) for field in fields)

    return False


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
