@echo off
setlocal
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.3.0_End_to_End_Autonomous_Delivery_Runner.ps1"
echo.
echo Runner finished. Press any key to close this window.
pause >nul
endlocal
