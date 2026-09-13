@echo off
setlocal
set "ROOT=%~dp0..\.."
set "PY=%ROOT%\..\..\..\..\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%ROOT%\Docs\uno_transport_monitor.py"
endlocal
