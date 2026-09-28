@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install --upgrade pyinstaller
  py -3 build_exe.py
) else (
  python -m pip install --upgrade pyinstaller
  python build_exe.py
)
pause
