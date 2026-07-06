from __future__ import annotations

from pathlib import Path

from rss_automation.config_files import read_categories, read_clean_lines, read_rss_sources, read_rss_urls


def test_read_clean_lines_ignores_blank_and_comment_lines(tmp_path: Path) -> None:
    config_file = tmp_path / "sample.txt"
    config_file.write_text("# comment\n\nOne\nTwo\n", encoding="utf-8")

    assert read_clean_lines(config_file) == ["One", "Two"]


def test_read_rss_urls_only_returns_http_urls(tmp_path: Path) -> None:
    rss_file = tmp_path / "rss.txt"
    rss_file.write_text("https://example.test/feed.xml\nnot-a-url\nhttp://example.test/feed.xml\n", encoding="utf-8")

    assert read_rss_urls(tmp_path, "rss.txt") == [
        "https://example.test/feed.xml",
        "http://example.test/feed.xml",
    ]


def test_read_rss_sources_supports_named_feeds(tmp_path: Path) -> None:
    rss_file = tmp_path / "rss.txt"
    rss_file.write_text(
        "erai = https://example.test/erai.xml\n"
        "movies | https://example.test/movies.xml\n"
        "https://example.test/default.xml\n",
        encoding="utf-8",
    )

    sources = read_rss_sources(tmp_path, "rss.txt")

    assert [(source.name, source.url) for source in sources] == [
        ("erai", "https://example.test/erai.xml"),
        ("movies", "https://example.test/movies.xml"),
        ("feed3", "https://example.test/default.xml"),
    ]


def test_read_categories_ignores_reserved_files(tmp_path: Path) -> None:
    (tmp_path / "rss.txt").write_text("https://example.test/feed.xml\n", encoding="utf-8")
    (tmp_path / "exclude.txt").write_text("Batch\n", encoding="utf-8")
    (tmp_path / "anime.txt").write_text("Show Name\n", encoding="utf-8")

    categories = read_categories(tmp_path)

    assert len(categories) == 1
    assert categories[0].category == "anime"
    assert categories[0].patterns == ("Show Name",)


def test_read_categories_supports_feed_scoped_patterns(tmp_path: Path) -> None:
    (tmp_path / "anime.txt").write_text(
        "@feed erai\n"
        "Show From Erai\n"
        "@feeds movies, series\n"
        "Shared Show\n"
        "@all\n"
        "Any Feed Show\n",
        encoding="utf-8",
    )

    categories = read_categories(tmp_path)

    assert categories[0].patterns == ("Show From Erai", "Shared Show", "Any Feed Show")
    assert categories[0].match_patterns[0].feed_names == ("erai",)
    assert categories[0].match_patterns[1].feed_names == ("movies", "series")
    assert categories[0].match_patterns[2].feed_names == ()
