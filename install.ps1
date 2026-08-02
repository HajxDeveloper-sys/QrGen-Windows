Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
pip install -r requirements.txt
Start-Process powershell.exe -ArgumentList "-File .\run.ps1" -WindowStyle Hidden
Exit
