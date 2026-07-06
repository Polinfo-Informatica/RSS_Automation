# RSS Automation

Version: `v1.0.0.1.a`

Project-relative RSS helper for Tixati. It reads RSS feeds, matches item titles against category `.txt` files, applies global exclusions, then saves either `.magnet` files or `.torrent` files into flat output folders.

## Requirements

- Python 3.14 64-bit
- Windows 10/11
- Tixati configured to watch the output folders

## Project layout

```text
RSS_Automation.py
settings.json
requirements.txt
requirements-dev.txt
pyproject.toml
rss_automation\
RSS_Config\rss.txt
RSS_Config\exclude.txt
RSS_Config\anime.txt
RSS_Magnet\
RSS_Torrent\
Logs\
```

There are **no subfolders** inside `RSS_Magnet` or `RSS_Torrent`.

## Install

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For development tools:

```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Configure

The default paths are project-relative:

```json
"config_folder": "${project_root}\\RSS_Config",
"magnet_output_folder": "${project_root}\\RSS_Magnet",
"torrent_output_folder": "${project_root}\\RSS_Torrent",
"log_folder": "${project_root}\\Logs"
```

Important options:

```json
"prefer_download_type": "magnet"
```

Valid values:

```text
magnet
torrent
```

If an RSS item has both magnet and torrent, this setting decides which one is used. If the item only has one type, the script uses whatever exists.

```json
"match_mode": "contains"
```

Valid values:

```text
contains
exact
regex
```

## RSS feeds

Edit:

```text
RSS_Config\rss.txt
```

Put one RSS feed URL per line.

## Categories

Every `.txt` file in `RSS_Config` is treated as a category except:

```text
rss.txt
exclude.txt
processed.txt
```

Example:

```text
RSS_Config\anime.txt
```

```text
One Piece
BLEACH
Mushoku Tensei
```

The category name is the file name without `.txt`.

## Exclusions

Edit:

```text
RSS_Config\exclude.txt
```

Example:

```text
Batch
OVA
Dual Audio
```

Any RSS title containing one of those terms is ignored.

## Run once

```bat
python RSS_Automation.py
```

## Run continuously

```bat
python RSS_Automation.py --loop
```

The loop interval is controlled by:

```json
"scan_interval_seconds": 300
```

## Logs

Every execution writes to:

```text
Logs\RSS_Automation.log
Logs\RSS_Automation_YYYY-MM-DD_HH-MM-SS.log
```

Retention is controlled by:

```json
"max_log_executions": 100
```

## Duplicate prevention

The script stores processed item keys in:

```text
RSS_Config\processed.txt
```

This prevents repeated outputs from the same RSS entries.

## Code quality

Run:

```bat
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format .
.venv\Scripts\python.exe -m black .
```

VS Code tasks are also available under:

```text
Terminal -> Run Task...
```

## Tixati usage

Configure Tixati to watch:

```text
RSS_Magnet
RSS_Torrent
```

The script only feeds Tixati. Tixati handles the actual downloading.
