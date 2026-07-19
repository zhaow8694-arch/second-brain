@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_AIMart_v0.2_Autonomous_Fixed.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause > nul
