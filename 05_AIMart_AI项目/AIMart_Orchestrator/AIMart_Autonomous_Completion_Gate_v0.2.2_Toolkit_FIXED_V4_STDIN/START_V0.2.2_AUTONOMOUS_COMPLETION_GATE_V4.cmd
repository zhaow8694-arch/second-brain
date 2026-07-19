@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.2.2_Completion_Gate_Runner_V4.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
