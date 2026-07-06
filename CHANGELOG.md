# Changelog

All notable changes to RSS Automation are documented here.

## v1.1.0.0

### Added

- Detects the current Windows Downloads known folder.
- Creates the runtime folder structure under `Downloads\RSS_Automation` by default.
- Supports path tokens: `${downloads_folder}`, `${root_folder}`, and `${project_root}`.
- Adds mypy, pytest coverage, pre-commit, and helper scripts.
- Adds development documentation and roadmap.

### Changed

- Runtime folders are no longer intended to live inside the source repository.
- Default settings now separate source code from user data.

## v1.0.0.1

### Added

- Modular Python package layout.
- Ruff configuration.
- Pytest test suite.
- Type-hinted helper modules.

## v1.0.0.0

### Added

- RSS feed parsing.
- Category matching from TXT files.
- Global exclusion file.
- Magnet and torrent output support.
- Duplicate prevention.
- Per-run and master logging.
- Log retention.
