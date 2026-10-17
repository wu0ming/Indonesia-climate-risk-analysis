@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" climate_risk.py gui
) else (
  python climate_risk.py gui
)
if errorlevel 1 pause
