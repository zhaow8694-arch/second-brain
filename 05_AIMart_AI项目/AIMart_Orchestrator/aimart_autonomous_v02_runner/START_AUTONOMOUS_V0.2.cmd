@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_AIMart_v0.2_Autonomous.ps1"
echo.
echo AIMart autonomous runner finished. Review logs under codex_runs\autonomous_v0_2.
pause
