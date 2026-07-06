# RSS Automation

Version: `v0.0.1.a`

Simple RSS helper for Tixati. It reads RSS feeds, matches item titles against category `.txt` files, applies global exclusions, then saves either `.magnet` files or `.torrent` files into flat output folders.

## Default folders

```text
D:\Root\Downloads\RSS_Config
D:\Root\Downloads\RSS_Magnet
D:\Root\Downloads\RSS_Torrent
D:\Root\Downloads\Logs
```

There are **no subfolders** inside `RSS_Magnet` or `RSS_Torrent`.

## Files

```text
RSS_Automation.py
settings.json
requirements.txt
RSS_Config\rss.txt
RSS_Config\exclude.txt
RSS_Config\anime.txt
```

## Install

```bat
pip install -r requirements.txt
```

## Configure

Edit `settings.json` if you want to change folders or behavior.

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

## Duplicate prevention

The script stores processed item keys in:

```text
RSS_Config\processed.txt
```

This prevents repeated downloads from the same RSS entries.

## Tixati usage

Configure Tixati to watch:

```text
D:\Root\Downloads\RSS_Magnet
D:\Root\Downloads\RSS_Torrent
```

The script only feeds Tixati. Tixati handles the actual downloading.
