@echo off
setlocal
cd /d "%~dp0"

title QR Code Generator - Setup
echo.
echo  QR Code Generator - Setup
echo  -------------------------

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 or newer was not found on PATH.
    echo Install Python from https://www.python.org/downloads/ and run this file again.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo Creating an isolated Python environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] The virtual environment could not be created.
        pause
        exit /b 1
    )
)

echo Installing application dependencies...
"venv\Scripts\python.exe" -m pip install --upgrade pip
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Installation did not finish successfully.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Setup is complete. Starting QR Code Generator...
start "" /D "%~dp0" "%~dp0run.bat"
endlocal
