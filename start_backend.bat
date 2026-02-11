@echo off
cd /d C:\GERECI\backend
C:\GERECI\venv\Scripts\python.exe -m uvicorn main:app --reload
pause
