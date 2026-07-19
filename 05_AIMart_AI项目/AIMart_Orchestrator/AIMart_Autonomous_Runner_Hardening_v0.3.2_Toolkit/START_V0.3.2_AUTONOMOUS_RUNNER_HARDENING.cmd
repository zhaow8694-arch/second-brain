@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Start_AIMart_v0.3.2_Autonomous_Runner_Hardening.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
