from __future__ import annotations

from collections import Counter

from rss_automation.models import RssItem
from rss_automation.pipeline import choose_download, log_duplicate_summary


def test_choose_download_uses_preference_when_both_exist() -> None:
    item = RssItem("feed", "title", "id", "mag", "tor", "raw")

    magnet_selected = choose_download(item, "magnet")
    torrent_selected = choose_download(item, "torrent")

    assert magnet_selected is not None
    assert torrent_selected is not None
    assert magnet_selected.kind == "magnet"
    assert torrent_selected.kind == "torrent"


def test_choose_download_falls_back_to_available_value() -> None:
    item = RssItem("feed", "title", "id", None, "tor", "raw")

    selected = choose_download(item, "magnet")

    assert selected is not None
    assert selected.kind == "torrent"
    assert selected.value == "tor"


def test_choose_download_returns_none_when_no_link_exists() -> None:
    item = RssItem("feed", "title", "id", None, None, None)

    assert choose_download(item, "magnet") is None


def test_log_duplicate_summary_logs_one_line(caplog) -> None:  # type: ignore[no-untyped-def]
    duplicates = Counter({"anime": 25})

    log_duplicate_summary(duplicates)

    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Duplicate skipped: 25 total (anime: 25)"


def test_log_duplicate_summary_skips_empty_counter(caplog) -> None:  # type: ignore[no-untyped-def]
    log_duplicate_summary(Counter())

    assert caplog.records == []
