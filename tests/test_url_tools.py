from __future__ import annotations

from rss_automation.url_tools import redact_text, redact_url


def test_redact_url_hides_token_query_parameter() -> None:
    redacted = redact_url("https://example.test/feed?res=1080p&token=secret-value&type=torrent")

    assert redacted == "https://example.test/feed?res=1080p&token=REDACTED&type=torrent"
    assert "secret-value" not in redacted


def test_redact_url_hides_case_insensitive_secret_keys() -> None:
    redacted = redact_url("https://example.test/feed?API_KEY=secret-value&name=value")

    assert redacted == "https://example.test/feed?API_KEY=REDACTED&name=value"
    assert "secret-value" not in redacted


def test_redact_url_keeps_url_without_secret_query_unchanged() -> None:
    url = "https://example.test/feed?res=1080p&type=torrent"

    assert redact_url(url) == url


def test_redact_url_keeps_url_without_query_unchanged() -> None:
    url = "https://example.test/feed"

    assert redact_url(url) == url


def test_redact_text_hides_secret_query_parameter_in_exception_text() -> None:
    redacted = redact_text("Max retries exceeded with url: /feed?res=1080p&type=torrent&token=secret-value")

    assert redacted == "Max retries exceeded with url: /feed?res=1080p&type=torrent&token=REDACTED"
    assert "secret-value" not in redacted
