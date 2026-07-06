from __future__ import annotations

from rss_automation.filename_tools import sanitize_filename, short_hash


def test_sanitize_filename_replaces_windows_invalid_characters() -> None:
    assert sanitize_filename('A:B<C>D"E/F\\G|H?I*J') == "A_B_C_D_E_F_G_H_I_J"


def test_sanitize_filename_never_returns_empty_string() -> None:
    assert sanitize_filename("   ...   ") == "download"


def test_short_hash_length_is_configurable() -> None:
    assert len(short_hash("example", 16)) == 16


def test_short_hash_is_stable() -> None:
    assert short_hash("example", 12) == short_hash("example", 12)
