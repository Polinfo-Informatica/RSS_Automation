from __future__ import annotations

from rss_automation.models import RssItem
from rss_automation.pipeline import choose_download


def test_choose_download_uses_preference_when_both_exist() -> None:
    item = RssItem("feed", "title", "id", "mag", "tor", "raw")

    assert choose_download(item, "magnet").kind == "magnet"
    assert choose_download(item, "torrent").kind == "torrent"


def test_choose_download_falls_back_to_available_value() -> None:
    item = RssItem("feed", "title", "id", None, "tor", "raw")

    selected = choose_download(item, "magnet")

    assert selected is not None
    assert selected.kind == "torrent"
    assert selected.value == "tor"


def test_choose_download_returns_none_when_no_link_exists() -> None:
    item = RssItem("feed", "title", "id", None, None, None)

    assert choose_download(item, "magnet") is None
