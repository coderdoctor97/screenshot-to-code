@echo off
setlocal
cd /d "%~dp0"
title Screenshot-to-Code - Launcher

echo ===============================================
echo  Screenshot-to-Code - Starting app
echo ===============================================
echo.

REM --- Sanity checks ---
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found. Run this file from the repo root.
    pause
    exit /b 1
)
if not exist "frontend\package.json" (
    echo [ERROR] frontend\package.json not found. Run this file from the repo root.
    pause
    exit /b 1
)

if not exist "backend\.env" (
    echo [WARN] backend\.env not found. The app will start, but generation needs
    echo        LLM credentials: either create backend\.env ^(see setup.bat^)
    echo        or set them in the app Settings dialog ^(gear icon^).
    echo.
)

if not exist "frontend\node_modules" (
    echo [WARN] frontend\node_modules missing. Run setup.bat first.
    echo.
)
cd /d "%~dp0backend"
call poetry env info -p >nul 2>nul
if errorlevel 1 (
    echo [WARN] Backend Poetry venv not found. Run setup.bat first.
    echo.
)
cd /d "%~dp0"

REM --- Start backend ---
echo Starting backend on http://127.0.0.1:7001 ...
start "screenshot-to-code backend" cmd /k "cd /d ""%~dp0backend"" && poetry run uvicorn main:app --reload --port 7001"

REM --- Start frontend ---
echo Starting frontend on http://localhost:5173 ...
start "screenshot-to-code frontend" cmd /k "cd /d ""%~dp0frontend"" && pnpm dev"

echo.
echo Waiting for servers to come up...
timeout /t 6 /nobreak >nul

echo Opening http://localhost:5173 ...
start "" "http://localhost:5173"

echo.
echo ===============================================
echo  Both servers launched in separate windows.
echo  - Backend:  http://127.0.0.1:7001
echo  - Frontend: http://localhost:5173
echo  Close those windows to stop the app.
echo ===============================================
pause
endlocal
