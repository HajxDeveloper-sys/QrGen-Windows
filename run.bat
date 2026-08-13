@echo off
setlocal
cd /d "%~dp0"

if exist "venv\Scripts\pythonw.exe" (
    start "QR Code Generator" /D "%~dp0" "venv\Scripts\pythonw.exe" "main.py"
) else if exist "venv\Scripts\python.exe" (
    start "QR Code Generator" /D "%~dp0" "venv\Scripts\python.exe" "main.py"
) else (
    echo [ERROR] The app has not been set up yet. Run install.bat first.
    pause
)

endlocal
