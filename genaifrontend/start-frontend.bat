@echo off
echo ========================================
echo Starting DataSense Frontend Server
echo ========================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo ERROR: Dependencies not installed!
    echo Please run setup-frontend.bat first.
    echo.
    pause
    exit /b 1
)

echo Starting development server...
echo.
echo The app will be available at http://localhost:4200
echo Press Ctrl+C to stop the server.
echo.

npm start
