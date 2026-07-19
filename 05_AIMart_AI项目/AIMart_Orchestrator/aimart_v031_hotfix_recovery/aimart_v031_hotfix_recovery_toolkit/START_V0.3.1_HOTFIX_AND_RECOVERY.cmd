@echo off
set SCRIPT_DIR=%~dp0
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Start_AIMart_v0.3.1_Hotfix_And_Recovery.ps1"
pause
