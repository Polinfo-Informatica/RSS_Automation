from __future__ import annotations

from pathlib import Path

from rss_automation.matching import (
    fields_are_excluded,
    fields_match_pattern,
    matching_categories,
    title_is_excluded,
    title_matches_pattern,
)
from rss_automation.models import CategoryRule, MatchPattern, RssItem


def test_literal_matching_is_case_insensitive_by_default() -> None:
    assert title_matches_pattern("[Group] Mushoku Tensei - 01", "mushoku tensei", "literal", False)


def test_contains_remains_alias_for_exact_phrase_matching() -> None:
    assert title_matches_pattern("[Group] Mushoku Tensei - 01", "mushoku tensei", "contains", False)


def test_exact_phrase_matching_does_not_match_inside_words() -> None:
    assert not title_matches_pattern("Mairimashita! Iruma-kun", "ITA", "literal", False)
    assert not title_matches_pattern("Natteita", "ITA", "literal", False)
    assert not title_matches_pattern("GrandBlue Season 3 - 01", "Grand Blue", "literal", False)


def test_exact_phrase_matching_treats_common_archive_separators_as_spaces() -> None:
    assert title_matches_pattern("[Grand Blue] Season 3 - 01", "Grand Blue", "literal", False)
    assert title_matches_pattern("Grand.Blue.Season.3", "Grand Blue", "literal", False)
    assert title_matches_pattern("Grand_Blue_Season_3", "Grand Blue", "literal", False)
    assert title_matches_pattern("[ITA] Grand Blue", "ITA", "literal", False)


def test_exact_phrase_matching_requires_matching_phrase_words() -> None:
    assert title_matches_pattern("Grand Blue Season 3 - 01", "Grand Blue", "literal", False)
    assert not title_matches_pattern("Grand Blue Season 3 - 01", "Grand  Blue", "literal", False)


def test_regex_and_raw_exact_modes_are_not_supported_for_matching() -> None:
    assert not title_matches_pattern("Episode 012", r"Episode \d{3}", "regex", False)
    assert not title_matches_pattern("BLEACH", "bleach", "exact", False)


def test_fields_match_pattern_matches_filename_or_description() -> None:
    item = RssItem(
        "feed",
        "Unrelated Title",
        "id",
        None,
        "tor",
        "raw",
        file_name="Grand.Blue.Season.3.-.01.torrent",
        description="Crunchyroll release",
    )

    assert fields_match_pattern(item, "grand blue", "literal", False)
    assert fields_match_pattern(item, "crunchyroll release", "literal", False)
    assert not fields_match_pattern(item, "Grand  Blue", "literal", False)


def test_exclusions_match_exact_phrases() -> None:
    assert title_is_excluded("Show Name Batch 1080p", ["batch"], False)
    assert title_is_excluded("Show Name Batch 1080p", ["NAME batch"], False)
    assert title_is_excluded("Show.Name.Batch.1080p", ["Name Batch"], False)
    assert title_is_excluded("[ITA] Show Name", ["ITA"], False)
    assert not title_is_excluded("ShowNameBatch 1080p", ["Name Batch"], False)
    assert not title_is_excluded("Mairimashita! Iruma-kun", ["ITA"], False)
    assert not title_is_excluded("Natteita", ["ITA"], False)
    assert not title_is_excluded("Show Name Batch 1080p", ["Name  Batch"], False)


def test_fields_are_excluded_checks_filename_or_description() -> None:
    item = RssItem(
        "feed",
        "Clean Title",
        "id",
        None,
        "tor",
        "raw",
        file_name="Show.Name.Batch.torrent",
        description="Encoded test release",
    )

    assert fields_are_excluded(item, ["name batch"], False)
    assert fields_are_excluded(item, ["test release"], False)
    assert not fields_are_excluded(item, ["Name  Batch"], False)


def test_matching_categories_skips_excluded_titles() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name",))]
    settings = {"case_sensitive": False, "match_mode": "literal"}

    assert matching_categories("Show Name Batch", categories, ["Batch"], settings) == []


def test_matching_categories_matches_item_filename_or_description() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name", "Special Release"))]
    settings = {"case_sensitive": False, "match_mode": "literal"}
    item = RssItem(
        "feed",
        "Unrelated Title",
        "id",
        None,
        "tor",
        "raw",
        file_name="Show.Name.-.01.torrent",
        description="Special Release metadata",
    )

    assert matching_categories(item, categories, [], settings) == [("anime", "Show Name")]


def test_matching_categories_excludes_item_by_filename_or_description() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name",))]
    settings = {"case_sensitive": False, "match_mode": "literal"}
    item = RssItem(
        "feed",
        "Clean Title",
        "id",
        None,
        "tor",
        "raw",
        file_name="Show Name - 01.torrent",
        description="Batch release metadata",
    )

    assert matching_categories(item, categories, ["batch release"], settings) == []


def test_matching_categories_returns_category_and_pattern() -> None:
    categories = [CategoryRule("anime", Path("anime.txt"), ("Show Name",))]
    settings = {"case_sensitive": False, "match_mode": "literal"}

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
    settings = {"case_sensitive": False, "match_mode": "literal"}

    assert matching_categories("Feed One Show - 01", categories, [], settings, "other-feed") == []
    assert matching_categories("Feed One Show - 01", categories, [], settings, "feed-one") == [
        ("anime", "Feed One Show")
    ]
    assert matching_categories("Any Feed Show - 01", categories, [], settings, "other-feed") == [
        ("anime", "Any Feed Show")
    ]
