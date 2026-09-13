@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 uno_midi_monitor_winapi.py
) else (
  python uno_midi_monitor_winapi.py
)
if errorlevel 1 pause
