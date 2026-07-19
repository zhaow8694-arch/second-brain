@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start_AIMart_v0.2.2_Completion_Gate_Runner_FIXED_STDIN.ps1"
pause
