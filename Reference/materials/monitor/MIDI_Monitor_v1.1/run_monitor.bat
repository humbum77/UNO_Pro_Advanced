@echo off
chcp 65001 >nul 2>&1
title UNO Synth Pro MIDI Monitor v1.1 State Read
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3 and enable Add Python to PATH.
  pause
  exit /b 1
)
python -m py_compile uno_midi_monitor_state_read.py
if errorlevel 1 (
  echo [ERROR] Syntax check failed.
  pause
  exit /b 1
)
python uno_midi_monitor_state_read.py
if errorlevel 1 pause
