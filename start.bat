@echo off
cd /d "%~dp0"
echo Compiling Backend...
gcc -o backend/scheduler.exe backend/scheduler.c
if %errorlevel% neq 0 (
    echo Compilation failed!
    pause
    exit /b
)
echo Starting Application...
python -m streamlit run frontend/app.py
pause
