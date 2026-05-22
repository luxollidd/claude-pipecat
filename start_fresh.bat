@echo off
cd /d "%~dp0"
if exist "state\session.json" del "state\session.json"
.venv\Scripts\python.exe src\agent\companion.py
pause
