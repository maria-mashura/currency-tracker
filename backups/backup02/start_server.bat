@echo off
echo Please wait........

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F >nul 2>&1

echo Starting........
cd /d "C:\Users\GuestUser\Documents\BA\Currency_project\Currency_tracker"

call venv\Scripts\activate

python main.py

pause
