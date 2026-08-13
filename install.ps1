$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "QR Code Generator - Setup" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python 3.11 or newer was not found on PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Creating an isolated Python environment..." -ForegroundColor Yellow
    & python -m venv (Join-Path $PSScriptRoot "venv")
}

Write-Host "Installing application dependencies..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Installation did not finish successfully." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host "[SUCCESS] Setup is complete. Starting QR Code Generator..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "run.ps1")) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
