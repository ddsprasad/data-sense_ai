@echo off
echo ========================================
echo DataSense Backend Setup Script
echo ========================================
echo.

REM Check if Python 3.10 is available
echo Checking for Python 3.10...
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 is not installed!
    echo.
    echo Please install Python 3.10.4 from:
    echo https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python 3.10 found!
echo.

REM Remove old broken virtual environment
echo Removing old virtual environment if it exists...
if exist "env" (
    rmdir /s /q env
    echo Old environment removed.
)
if exist "venv" (
    rmdir /s /q venv
    echo Old venv removed.
)
echo.

REM Create new virtual environment
echo Creating new virtual environment with Python 3.10...
py -3.10 -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

REM Activate virtual environment and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Installing dependencies from requirements.txt...
echo This may take several minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some packages failed to install.
    echo Trying with --prefer-binary option...
    echo.
    pip install --prefer-binary -r requirements.txt
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the backend server, run:
echo   venv\Scripts\activate
echo   uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
pause
