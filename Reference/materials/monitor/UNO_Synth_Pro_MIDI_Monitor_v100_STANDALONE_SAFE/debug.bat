@echo off
cd /d "%~dp0"
echo UNO Synth Pro MIDI Monitor - debug console
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 uno_midi_monitor_winapi.py
) else (
  python uno_midi_monitor_winapi.py
)
echo.
echo Exit code: %errorlevel%
pause
