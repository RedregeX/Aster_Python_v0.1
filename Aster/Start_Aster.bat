@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 goto setup_error
)
if not exist ".venv\aster-ready" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_error
    type nul > ".venv\aster-ready"
)
".venv\Scripts\python.exe" run.py %*
if errorlevel 1 pause
exit /b
:setup_error
echo.
echo Setup failed. Install Python 3.11 or 3.12 from python.org.
echo Enable 'Add python.exe to PATH', then run this file again.
pause
exit /b 1
