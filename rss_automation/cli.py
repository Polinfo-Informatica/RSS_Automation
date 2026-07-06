"""Command-line interface for RSS Automation."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from rss_automation import __version__
from rss_automation.pipeline import run_once
from rss_automation.settings import get_project_root, load_settings


def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""

    parser = argparse.ArgumentParser(description=f"RSS Automation {__version__}")
    parser.add_argument(
        "--settings",
        default="settings.json",
        help="Path to settings.json. Relative paths resolve from the project root.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously using scan_interval_seconds from settings.json.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Application entry point used by RSS_Automation.py."""

    args = build_arg_parser().parse_args(argv)
    settings_path = Path(args.settings)

    if not args.loop:
        return run_once(settings_path)

    project_root = get_project_root()
    while True:
        try:
            settings = load_settings(settings_path, project_root)
            interval = int(settings.get("scan_interval_seconds", 300))
            code = run_once(settings_path)

            if code not in {0, 2}:
                logging.warning("Run finished with code %s", code)

            time.sleep(max(30, interval))
        except KeyboardInterrupt:
            print("Stopped by user.")
            return 0
        except Exception as exc:
            print(f"Fatal loop error: {exc}", file=sys.stderr)
            time.sleep(60)
