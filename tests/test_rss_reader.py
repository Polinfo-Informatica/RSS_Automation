from __future__ import annotations

from types import SimpleNamespace

from rss_automation.rss_reader import extract_entry_description, extract_link_filename, filename_from_url


def test_filename_from_url_decodes_path_name() -> None:
    assert filename_from_url("https://example.test/files/Grand%20Blue%20-%2001.torrent?token=secret") == (
        "Grand Blue - 01.torrent"
    )


def test_extract_entry_description_uses_summary_description_and_content() -> None:
    entry = SimpleNamespace(
        summary="Summary text",
        description="Description text",
        subtitle="Subtitle text",
        content=[{"value": "Content text"}],
    )

    description = extract_entry_description(entry)

    assert "Summary text" in description
    assert "Description text" in description
    assert "Subtitle text" in description
    assert "Content text" in description


def test_extract_link_filename_uses_link_and_enclosure_metadata() -> None:
    entry = SimpleNamespace(
        filename="Explicit Name.torrent",
        file_name="Alternate Name.torrent",
        media_title="Media Title",
        links=[{"title": "Link Title", "href": "https://example.test/Link%20Name.torrent"}],
        enclosures=[{"filename": "Enclosure Name.torrent", "url": "https://example.test/Enclosure%20Url.torrent"}],
    )

    file_name = extract_link_filename(entry, "https://example.test/Raw%20Name.torrent", None)

    assert "Explicit Name.torrent" in file_name
    assert "Alternate Name.torrent" in file_name
    assert "Media Title" in file_name
    assert "Link Name.torrent" in file_name
    assert "Enclosure Name.torrent" in file_name
    assert "Enclosure Url.torrent" in file_name
    assert "Raw Name.torrent" in file_name
