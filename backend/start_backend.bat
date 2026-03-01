@echo off
echo Starting ASL Sign Language API Backend...
echo.
echo Make sure your Python virtual environment is activated.
echo The API will be available at http://0.0.0.0:8000
echo Flutter app should connect to this machine's local IP address.
echo.
cd /d "%~dp0.."
.venv\Scripts\python.exe -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
pause
