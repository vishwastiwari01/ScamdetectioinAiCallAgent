@echo off
echo ========================================
echo   STARTING AI HONEYPOT SERVER
echo ========================================
echo.

REM Add user Python to PATH
set PYTHONPATH=%APPDATA%\Python\Python312\site-packages;%PYTHONPATH%
set PATH=%APPDATA%\Python\Python312\Scripts;%PATH%

echo Checking Python environment...
python check_python_env.py

echo.
echo Starting server...
echo Server will be at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run using Python module to ensure packages are found
python -m uvicorn simple_fastapi_honeypot:app --host 0.0.0.0 --port 8000

pause
