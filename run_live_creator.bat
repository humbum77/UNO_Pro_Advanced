@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m live_creator
) else (
  python -m live_creator
)
if errorlevel 1 pause
