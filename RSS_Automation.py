#!/usr/bin/env python3
"""Compatibility launcher for the RSS Automation package.

Keep this file at the project root so existing VS Code tasks, shortcuts, and
manual commands such as `python RSS_Automation.py` continue to work.
"""

from __future__ import annotations

from rss_automation.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
