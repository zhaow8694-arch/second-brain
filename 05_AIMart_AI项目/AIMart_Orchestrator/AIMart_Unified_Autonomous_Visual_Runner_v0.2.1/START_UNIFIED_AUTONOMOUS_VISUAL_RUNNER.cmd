@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_Unified_Visual_Autonomous_Runner.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
