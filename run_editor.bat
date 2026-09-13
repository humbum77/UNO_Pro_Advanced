@echo off
cd /d "%~dp0"
python -c "from PIL import Image,ImageDraw,ImageTk" >nul 2>&1
if errorlevel 1 (
  echo Pillow is required for anti-aliased display rendering.
  echo Installing Pillow...
  python -m pip install -r Docs\requirements.txt
  if errorlevel 1 (
    echo Could not install Pillow. Run install_dependencies.bat and try again.
    pause
    exit /b 1
  )
)
python main.py
if errorlevel 1 pause
