@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run Start_Aster.bat first to create the environment.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --name Aster --collect-all glfw --collect-all glcontext --add-data "aster/shaders;aster/shaders" run.py
if errorlevel 1 goto failed
echo.
echo The app is at dist\Aster\Aster.exe. Keep the entire Aster folder together.
pause
exit /b 0
:failed
echo Build failed. See the error above.
pause
exit /b 1
