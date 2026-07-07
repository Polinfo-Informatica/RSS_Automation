from __future__ import annotations

import logging
from collections import Counter

import pytest
from pytest import LogCaptureFixture, MonkeyPatch
from rss_automation.models import FeedSource, RssItem
from rss_automation.pipeline import choose_download, log_duplicate_summary, read_feed_with_retries


def test_choose_download_uses_preference_when_both_exist() -> None:
    item = RssItem("feed", "title", "id", "magnet-link", "torrent-link", "raw")

    magnet_selected = choose_download(item, "magnet")
    torrent_selected = choose_download(item, "torrent")

    assert magnet_selected is not None
    assert torrent_selected is not None
    assert magnet_selected.kind == "magnet"
    assert magnet_selected.value == "magnet-link"
    assert torrent_selected.kind == "torrent"
    assert torrent_selected.value == "torrent-link"


def test_choose_download_falls_back_to_magnet_only_items() -> None:
    item = RssItem("feed", "title", "id", "magnet-link", None, "raw")

    selected = choose_download(item, "torrent")

    assert selected is not None
    assert selected.kind == "magnet"
    assert selected.value == "magnet-link"


def test_choose_download_falls_back_to_torrent_only_items() -> None:
    item = RssItem("feed", "title", "id", None, "torrent-link", "raw")

    selected = choose_download(item, "magnet")

    assert selected is not None
    assert selected.kind == "torrent"
    assert selected.value == "torrent-link"


def test_choose_download_returns_none_when_no_link_exists() -> None:
    item = RssItem("feed", "title", "id", None, None, None)

    assert choose_download(item, "torrent") is None


def test_read_feed_with_retries_succeeds_after_transient_failure(monkeypatch: MonkeyPatch) -> None:
    calls = 0
    item = RssItem("feed", "title", "id", "magnet", "torrent", "raw")

    def fake_parse_feed(feed_url: str, timeout: int, user_agent: str, feed_name: str) -> list[RssItem]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary failure")
        assert feed_url == "https://example.test/feed"
        assert timeout == 30
        assert user_agent == "agent"
        assert feed_name == "erai"
        return [item]

    monkeypatch.setattr("rss_automation.pipeline.parse_feed", fake_parse_feed)
    monkeypatch.setattr("rss_automation.pipeline.time.sleep", lambda seconds: None)

    result = read_feed_with_retries(
        FeedSource("erai", "https://example.test/feed"),
        {
            "feed_retry_attempts": 2,
            "feed_retry_delay_seconds": 10,
            "download_timeout_seconds": 30,
            "request_user_agent": "agent",
        },
    )

    assert result == [item]
    assert calls == 2


def test_read_feed_with_retries_raises_after_all_attempts(monkeypatch: MonkeyPatch) -> None:
    calls = 0

    def fake_parse_feed(feed_url: str, timeout: int, user_agent: str, feed_name: str) -> list[RssItem]:
        nonlocal calls
        calls += 1
        raise TimeoutError("temporary failure")

    monkeypatch.setattr("rss_automation.pipeline.parse_feed", fake_parse_feed)
    monkeypatch.setattr("rss_automation.pipeline.time.sleep", lambda seconds: None)

    with pytest.raises(TimeoutError):
        read_feed_with_retries(
            FeedSource("erai", "https://example.test/feed"),
            {
                "feed_retry_attempts": 3,
                "feed_retry_delay_seconds": 10,
                "download_timeout_seconds": 30,
                "request_user_agent": "agent",
            },
        )

    assert calls == 3


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
