@echo off
echo ========================================
echo Starting DataSense Backend Server
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Virtual environment activated.
echo.
echo Starting server on http://localhost:8000
echo API documentation will be available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Start uvicorn server with increased timeout for long-running LLM queries
REM --timeout-keep-alive: How long to wait for requests on a Keep-Alive connection (default: 5)
REM --timeout-graceful-shutdown: Max wait time for graceful shutdown (default: None)
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 300
