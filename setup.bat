@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title Screenshot-to-Code - Setup

echo ===============================================
echo  Screenshot-to-Code - First time setup
echo ===============================================
echo.

REM --- 1. Check Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://www.python.org/downloads/
    echo         Make sure to tick "Add python.exe to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

REM --- 2. Check Node.js ---
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node 18+ from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo [OK] Node %%v

REM --- 3. Check / install Poetry ---
where poetry >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Poetry not found, installing via pip...
    python -m pip install --upgrade poetry
    if errorlevel 1 (
        echo [ERROR] Failed to install Poetry. Run: python -m pip install poetry
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%v in ('poetry --version 2^>^&1') do echo [OK] %%v

REM --- 4. Check / install pnpm ---
where pnpm >nul 2>nul
if errorlevel 1 (
    echo [SETUP] pnpm not found, installing...
    where corepack >nul 2>nul
    if not errorlevel 1 (
        call corepack enable
        call corepack prepare pnpm@10.32.1 --activate
    ) else (
        call npm install -g pnpm
    )
)
where pnpm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] pnpm still not found. Run: npm install -g pnpm
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('pnpm --version 2^>^&1') do echo [OK] pnpm %%v
echo.

REM --- 5. Backend deps ---
echo [1/4] Installing backend dependencies (poetry install)...
cd /d "%~dp0backend"
call poetry install
if errorlevel 1 (
    echo [ERROR] "poetry install" failed in backend\
    pause
    exit /b 1
)

REM --- 6. Playwright Chromium (screenshot preview tool) ---
echo.
echo [2/4] Installing Playwright Chromium (optional screenshot-preview tool)...
call poetry run playwright install chromium
if errorlevel 1 (
    echo [WARN] Playwright Chromium install failed. The app still works, preview tool will just be skipped.
) else (
    echo [OK] Chromium installed.
)

REM --- 7. Frontend deps ---
echo.
echo [3/4] Installing frontend dependencies (pnpm install)...
cd /d "%~dp0frontend"
call pnpm install
if errorlevel 1 (
    echo [ERROR] "pnpm install" failed in frontend\
    pause
    exit /b 1
)

REM --- 8. Env files ---
echo.
echo [4/4] Checking env files...
cd /d "%~dp0"

if not exist "backend\.env" (
    echo [SETUP] Creating backend\.env template...
    (
        echo # Fill in your LLM credentials, or skip this and use the in-app Settings ^(gear icon^) instead.
        echo CUSTOM_PROVIDER_API_KEY=sk-your-key
        echo CUSTOM_PROVIDER_MODEL=your-model-id
        echo # Optional: CUSTOM_PROVIDER_BASE_URL=https://your-host/v1
        echo # Optional: CUSTOM_PROVIDER_FORMAT=openai
        echo # Strongly recommended for image edit/background-removal features:
        echo # REPLICATE_API_KEY=r8_your-key
        echo # Optional, for asset extraction and video mode:
        echo # GEMINI_API_KEY=your-gemini-key
    ) > "backend\.env"
    echo [OK] Created backend\.env - edit it with your keys.
) else (
    echo [OK] backend\.env already exists, leaving it alone.
)

if not exist "frontend\.env.local" (
    echo [SETUP] Creating frontend\.env.local from .env.example...
    copy /y "frontend\.env.example" "frontend\.env.local" >nul
    echo [OK] Created frontend\.env.local
) else (
    echo [OK] frontend\.env.local already exists, leaving it alone.
)

echo.
echo ===============================================
echo  Setup complete!
echo  1. Edit backend\.env with your API keys
echo     (or configure the Customized Provider in the app Settings)
echo  2. Run start.bat to launch the app
echo ===============================================
pause
endlocal
