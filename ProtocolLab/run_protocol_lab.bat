@echo off
setlocal
cd /d "%~dp0.."
py -3 -m pip install -r ProtocolLab\requirements.txt
if errorlevel 1 exit /b %errorlevel%
py -3 ProtocolLab\protocol_lab.py
