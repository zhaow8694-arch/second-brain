@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.2.2_Autonomous_Completion_Gate_Runner_V5.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
