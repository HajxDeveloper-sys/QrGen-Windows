Set-Location $PSScriptRoot

$pythonw = Join-Path $PSScriptRoot "venv\Scripts\pythonw.exe"
$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

if (Test-Path $pythonw) {
    Start-Process $pythonw -ArgumentList "main.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
} elseif (Test-Path $python) {
    Start-Process $python -ArgumentList "main.py" -WorkingDirectory $PSScriptRoot
} else {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show("Run install.ps1 or install.bat before starting the app.", "QR Code Generator") | Out-Null
}
