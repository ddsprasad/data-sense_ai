@echo off
echo ========================================
echo DataSense Frontend Setup Script
echo ========================================
echo.

REM Check if Node.js is installed
echo Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed!
    echo.
    echo Please install Node.js 20.9.0 from:
    echo https://nodejs.org/dist/v20.9.0/node-v20.9.0-x64.msi
    echo.
    pause
    exit /b 1
)

echo Node.js found!
node --version
echo.

REM Check npm
echo Checking npm...
npm --version
echo.

REM Install dependencies
echo Installing frontend dependencies...
echo This may take several minutes...
echo.
npm install

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Frontend Setup Complete!
echo ========================================
echo.
echo To start the frontend development server, run:
echo   npm start
echo.
echo The app will be available at http://localhost:4200
echo.
pause
