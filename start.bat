@echo off
cd /d "%~dp0"

echo [1/2] Checking Backend Compilation...
where gcc >nul 2>nul
if %errorlevel% equ 0 (
    echo Compiling C Backend...
    gcc -o backend/scheduler.exe backend/scheduler.c
    if %errorlevel% neq 0 (
        echo Warning: Compilation failed. Attempting to use Python fallback.
    ) else (
        echo Compilation Successful.
    )
) else (
    echo GCC not found. Using Python backend fallback.
)

echo [2/2] Starting Application...
where python >nul 2>nul
if %errorlevel% equ 0 (
    python -m streamlit run frontend/app.py
) else (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        py -m streamlit run frontend/app.py
    ) else (
        echo Error: Python not found! Please install Python.
        pause
        exit /b
    )
)
pause
