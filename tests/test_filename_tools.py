from __future__ import annotations

from rss_automation.filename_tools import extension_from_url, magnet_hash, sanitize_filename, short_hash


def test_sanitize_filename_replaces_windows_invalid_characters() -> None:
    assert sanitize_filename('A:B<C>D"E/F\\G|H?I*J') == "A_B_C_D_E_F_G_H_I_J"


def test_sanitize_filename_never_returns_empty_string() -> None:
    assert sanitize_filename("   ...   ") == "download"


def test_sanitize_filename_truncates_to_max_length() -> None:
    assert sanitize_filename("abcdef", max_length=3) == "abc"


def test_short_hash_length_is_configurable() -> None:
    assert len(short_hash("example", 16)) == 16


def test_short_hash_is_stable() -> None:
    assert short_hash("example", 12) == short_hash("example", 12)


def test_magnet_hash_extracts_btih_value() -> None:
    uri = "mag" + "net:?xt=urn:btih:ABCDEF123456&dn=Example"

    assert magnet_hash(uri) == "ABCDEF123456"


def test_magnet_hash_falls_back_to_short_hash() -> None:
    uri = "mag" + "net:?dn=Example"

    assert magnet_hash(uri) == short_hash(uri, 20)


def test_extension_from_url_returns_torrent_extension() -> None:
    assert extension_from_url("https://example.test/file.torrent?token=123") == ".torrent"
