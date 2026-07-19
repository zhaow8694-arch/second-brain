@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.3.1_Hotfix_And_Recovery_V2.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause > nul
