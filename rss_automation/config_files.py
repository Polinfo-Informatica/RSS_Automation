"""Readers for RSS_Config text files."""

from __future__ import annotations

from pathlib import Path

from rss_automation.constants import RESERVED_CONFIG_FILES
from rss_automation.models import CategoryRule, FeedSource, MatchPattern


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


def normalize_feed_name(value: str) -> str:
    """Normalize configured feed names for matching."""

    return value.strip().casefold()


def parse_feed_source(line: str, index: int) -> FeedSource | None:
    """Parse one rss.txt line into a named feed source."""

    name = f"feed{index}"
    url = line.strip()

    for separator in ("=", "|"):
        if separator in line:
            possible_name, possible_url = line.split(separator, 1)
            if possible_url.strip().lower().startswith(("http://", "https://")):
                name = possible_name.strip()
                url = possible_url.strip()
                break

    if not url.lower().startswith(("http://", "https://")):
        return None

    return FeedSource(name=normalize_feed_name(name), url=url)


def read_rss_sources(config_folder: Path, rss_file_name: str) -> list[FeedSource]:
    """Read valid HTTP(S) RSS feed sources from the configured RSS list."""

    sources: list[FeedSource] = []
    for index, line in enumerate(read_clean_lines(config_folder / rss_file_name), start=1):
        source = parse_feed_source(line, index)
        if source is not None:
            sources.append(source)

    return sources


def read_rss_urls(config_folder: Path, rss_file_name: str) -> list[str]:
    """Read valid HTTP(S) RSS URLs from the configured RSS list."""

    return [source.url for source in read_rss_sources(config_folder, rss_file_name)]


def read_exclusions(config_folder: Path, exclude_file_name: str) -> list[str]:
    """Read global exclusion terms from the configured exclusion file."""

    return read_clean_lines(config_folder / exclude_file_name)


def parse_feed_directive(line: str) -> tuple[str, ...] | None:
    """Parse @feed directives in category files."""

    lowered = line.casefold()
    if lowered in {"@all", "@any"}:
        return ()

    for prefix in ("@feed ", "@feeds "):
        if lowered.startswith(prefix):
            raw_names = line[len(prefix) :]
            return tuple(normalize_feed_name(name) for name in raw_names.replace(";", ",").split(",") if name.strip())

    return None


def parse_match_patterns(lines: list[str]) -> tuple[MatchPattern, ...]:
    """Parse category file lines into optionally feed-scoped match patterns."""

    active_feeds: tuple[str, ...] = ()
    patterns: list[MatchPattern] = []

    for line in lines:
        directive = parse_feed_directive(line)
        if directive is not None:
            active_feeds = directive
            continue

        patterns.append(MatchPattern(text=line, feed_names=active_feeds))

    return tuple(patterns)


def read_categories(config_folder: Path) -> list[CategoryRule]:
    """Treat every non-reserved .txt file as a category file."""

    rules: list[CategoryRule] = []

    for path in sorted(config_folder.glob("*.txt")):
        if path.name.lower() in RESERVED_CONFIG_FILES:
            continue

        lines = read_clean_lines(path)
        match_patterns = parse_match_patterns(lines)
        patterns = tuple(pattern.text for pattern in match_patterns)
        if not patterns:
            continue

        rules.append(
            CategoryRule(category=path.stem, source_file=path, patterns=patterns, match_patterns=match_patterns)
        )

    return rules
