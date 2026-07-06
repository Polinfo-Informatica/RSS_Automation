$ErrorActionPreference = "Stop"

python -m pip install -r requirements-dev.txt
python -m PyInstaller --onefile --name RSS_Automation RSS_Automation.py

Write-Host "Created dist\\RSS_Automation.exe"
