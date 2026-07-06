from __future__ import annotations

from pathlib import Path

from rss_automation.duplicate_tracker import append_processed, load_processed, processed_key
from rss_automation.models import RssItem, SelectedDownload


def test_load_processed_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    processed_file = tmp_path / "processed.txt"
    processed_file.write_text("\n# comment\nabc\n\ndef\n", encoding="utf-8")

    assert load_processed(processed_file) == {"abc", "def"}


def test_load_processed_returns_empty_set_for_missing_file(tmp_path: Path) -> None:
    assert load_processed(tmp_path / "missing.txt") == set()


def test_append_processed_adds_key(tmp_path: Path) -> None:
    processed_file = tmp_path / "processed.txt"

    append_processed(processed_file, "abc")
    append_processed(processed_file, "def")

    assert processed_file.read_text(encoding="utf-8") == "abc\ndef\n"


def test_processed_key_is_stable_for_torrent_download() -> None:
    item = RssItem("feed", "title", "item-id", None, "https://example.test/file.torrent", "raw")
    selected = SelectedDownload("torrent", "https://example.test/file.torrent")

    first = processed_key(item, selected, "anime")
    second = processed_key(item, selected, "anime")

    assert first == second
    assert len(first) == 32


def test_processed_key_changes_by_category() -> None:
    item = RssItem("feed", "title", "item-id", None, "https://example.test/file.torrent", "raw")
    selected = SelectedDownload("torrent", "https://example.test/file.torrent")

    assert processed_key(item, selected, "anime") != processed_key(item, selected, "movies")
