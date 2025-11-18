@echo off
REM Start ML service
start "ML Service" cmd /k "cd /d C:\Users\kavya\OneDrive\Desktop\Mini\ml_service && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8001"

REM Start Backend API
start "Backend API" cmd /k "cd /d C:\Users\kavya\OneDrive\Desktop\Mini\backend && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Started ML service and Backend in separate windows.
pause
