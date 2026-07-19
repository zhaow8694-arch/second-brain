@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.3.1_Recovery_Finalize.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
