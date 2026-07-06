# Development

## Recommended IDE

PyCharm 2026.1.4 or newer is recommended because it supports Python 3.14, pytest, Ruff, mypy, virtual environments, and Git integration cleanly.

## Python interpreter

Use a local virtual environment at the repository root:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

In PyCharm, set the project interpreter to:

```text
.venv\Scripts\python.exe
```

## Quality checks

Run the full local check script:

```powershell
.\scripts\check.ps1
```

Or run tools individually:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy rss_automation tests
python -m pytest
```

## Formatting

The project standard formatter is Ruff format. Black remains available as a secondary formatter, but use Ruff first for consistency.

```powershell
python -m ruff format .
```

## Pre-commit

Install hooks once per clone:

```powershell
python -m pre_commit install
```

Run all hooks manually:

```powershell
python -m pre_commit run --all-files
```

## Runtime data

Runtime data is intentionally outside the repository. By default, the program creates:

```text
<Windows Downloads>\RSS_Automation\RSS_Config
<Windows Downloads>\RSS_Automation\RSS_Magnet
<Windows Downloads>\RSS_Automation\RSS_Torrent
<Windows Downloads>\RSS_Automation\Logs
```

Do not commit runtime folders, logs, downloaded files, or private RSS tokens.
