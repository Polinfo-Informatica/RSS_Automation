"""Readers for RSS_Config text files."""

from __future__ import annotations

from pathlib import Path

from rss_automation.constants import RESERVED_CONFIG_FILES
from rss_automation.models import CategoryRule


def read_clean_lines(path: Path) -> list[str]:
    """Read non-empty, non-comment UTF-8 lines from a text file."""

    if not path.exists():
        return []

    lines: list[str] = []
    with path.open("r", encoding="utf-8-sig", errors="replace") as file_handle:
        for raw_line in file_handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            lines.append(line)

    return lines


def read_rss_urls(config_folder: Path, rss_file_name: str) -> list[str]:
    """Read valid HTTP(S) RSS URLs from the configured RSS list."""

    urls = read_clean_lines(config_folder / rss_file_name)
    return [url for url in urls if url.lower().startswith(("http://", "https://"))]


def read_exclusions(config_folder: Path, exclude_file_name: str) -> list[str]:
    """Read global exclusion terms from the configured exclusion file."""

    return read_clean_lines(config_folder / exclude_file_name)


def read_categories(config_folder: Path) -> list[CategoryRule]:
    """Treat every non-reserved .txt file as a category file."""

    rules: list[CategoryRule] = []

    for path in sorted(config_folder.glob("*.txt")):
        if path.name.lower() in RESERVED_CONFIG_FILES:
            continue

        patterns = tuple(read_clean_lines(path))
        if not patterns:
            continue

        rules.append(CategoryRule(category=path.stem, source_file=path, patterns=patterns))

    return rules
