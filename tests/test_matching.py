from __future__ import annotations

from pathlib import Path

from rss_automation.matching import matching_categories, title_is_excluded, title_matches_pattern
from rss_automation.models import CategoryRule, MatchPattern


def test_contains_matching_is_case_insensitive_by_default() -> None:
    assert title_matches_pattern("[Group] Mushoku Tensei - 01", "mushoku tensei", "contains", False)


def test_exact_matching_requires_equal_normalized_title() -> None:
    assert title_matches_pattern("BLEACH", "bleach", "exact", False)
    assert not title_matches_pattern("BLEACH - 01", "bleach", "exact", False)


def test_regex_matching_accepts_valid_regular_expression() -> None:
    assert title_matches_pattern("Episode 012", r"Episode \d{3}", "regex", False)


def test_exclusions_match_substrings() -> None:
    assert title_is_excluded("Show Name Batch 1080p", ["batch"], False)


def test_matching_categories_skips_excluded_titles() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name",))]
    settings = {"case_sensitive": False, "match_mode": "contains"}

    assert matching_categories("Show Name Batch", categories, ["Batch"], settings) == []


def test_matching_categories_returns_category_and_pattern() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name",))]
    settings = {"case_sensitive": False, "match_mode": "contains"}

    assert matching_categories("Show Name - 01", categories, [], settings) == [("anime", "Show Name")]


def test_matching_categories_respects_feed_scoped_patterns() -> None:
    categories = [
        CategoryRule(
            "anime",
            Path("anime.txt"),
            ("Feed One Show", "Any Feed Show"),
            (
                MatchPattern("Feed One Show", ("feed-one",)),
                MatchPattern("Any Feed Show"),
            ),
        )
    ]
    settings = {"case_sensitive": False, "match_mode": "contains"}

    assert matching_categories("Feed One Show - 01", categories, [], settings, "other-feed") == []
    assert matching_categories("Feed One Show - 01", categories, [], settings, "feed-one") == [("anime", "Feed One Show")]
    assert matching_categories("Any Feed Show - 01", categories, [], settings, "other-feed") == [("anime", "Any Feed Show")]
