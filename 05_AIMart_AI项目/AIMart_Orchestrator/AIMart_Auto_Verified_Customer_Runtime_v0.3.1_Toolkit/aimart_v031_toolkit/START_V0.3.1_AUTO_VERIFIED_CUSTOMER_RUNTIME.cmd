@echo off
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Start_AIMart_v0.3.1_Auto_Verified_Customer_Runtime_Runner.ps1"
pause
