@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.2.2_Autonomous_Completion_Gate_Runner.ps1"
pause
