@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_AIMart_v0.2_Autonomous_Fixed_V3.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
