@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.3.1_Recovery_Finalize_FIXED.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
