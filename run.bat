@echo off
title JobSeeker Command Center Setup
echo =======================================================================
echo              Welcome to JobSeeker Command Center Setup
echo =======================================================================
echo.

REM Check python is installed
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python launcher py was not found on this system.
    echo Please install Python 3.10+ and ensure you add it to PATH.
    echo.
    pause
    exit /b 1
)

REM Check if MongoDB is installed
mongod --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] MongoDB is not installed. Installing MongoDB natively via Winget...
    winget install -e --id MongoDB.Server --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [ERROR] Failed to install MongoDB. Please install it manually.
        pause
        exit /b 1
    )
    echo [INFO] MongoDB installed successfully!
)

REM Ensure MongoDB service is running
echo [INFO] Starting MongoDB service...
net start MongoDB >nul 2>&1

REM Check if virtual environment exists
if not exist ".venv" (
    echo [INFO] Creating local virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
    echo.
)

REM Activate venv and install dependencies
echo [INFO] Activating virtual environment and updating dependencies...
call .venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install required Python libraries.
    pause
    exit /b 1
)
echo [INFO] All requirements verified and installed.
echo.

REM Launch FastAPI in a separate window
echo [INFO] Launching JobSeeker local server...
start "JobSeeker Server" cmd /k "call .venv\Scripts\activate && uvicorn backend.main:app --host 127.0.0.1 --port 8000"

REM Wait for server to bind
echo [INFO] Waiting for server to initialize...
timeout /t 3 /nobreak >nul

REM Launch default web browser
echo [INFO] Opening JobSeeker dashboard in default browser...
start http://127.0.0.1:8000

echo.
echo =======================================================================
echo      JobSeeker Command Center is now running!
echo      Server Port: http://127.0.0.1:8000
echo.
echo      - Keep the JobSeeker Server command window open to keep
echo        the scraper scheduler running in the background.
echo      - Close that server window when you wish to stop the application.
echo =======================================================================
echo.
pause
