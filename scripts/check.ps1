$ErrorActionPreference = "Stop"

Write-Host "Running Ruff check..."
python -m ruff check .

Write-Host "Running Ruff format check..."
python -m ruff format --check .

Write-Host "Running mypy..."
python -m mypy rss_automation

Write-Host "Running pytest..."
python -m pytest

Write-Host "All checks completed."
