@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.3.1_Hotfix_And_Recovery_V5.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
