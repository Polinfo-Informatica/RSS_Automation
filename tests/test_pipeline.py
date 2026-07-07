from __future__ import annotations

import logging
from collections import Counter

from pytest import LogCaptureFixture
from rss_automation.models import RssItem
from rss_automation.pipeline import choose_download, log_duplicate_summary


def test_choose_download_always_uses_torrent_when_both_exist() -> None:
    item = RssItem("feed", "title", "id", "alternate-link", "torrent-link", "raw")

    selected = choose_download(item, "alternate")

    assert selected is not None
    assert selected.kind == "torrent"
    assert selected.value == "torrent-link"


def test_choose_download_skips_items_without_torrent_url() -> None:
    item = RssItem("feed", "title", "id", "alternate-link", None, "raw")

    assert choose_download(item, "alternate") is None


def test_choose_download_returns_none_when_no_link_exists() -> None:
    item = RssItem("feed", "title", "id", None, None, None)

    assert choose_download(item, "torrent") is None


def test_log_duplicate_summary_logs_one_line(caplog: LogCaptureFixture) -> None:
    duplicates = Counter({"anime": 25})

    with caplog.at_level(logging.INFO):
        log_duplicate_summary(duplicates)

    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Duplicate skipped: 25 total (anime: 25)"


def test_log_duplicate_summary_skips_empty_counter(caplog: LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        log_duplicate_summary(Counter())

    assert caplog.records == []
