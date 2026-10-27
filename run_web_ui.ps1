$env:PYTHONIOENCODING = "utf-8"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Membuka Dashboard Web Interaktif RSA vs RSA-CRT...    " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

if (Get-Command py -ErrorAction SilentlyContinue) {
    py server.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python server.py
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") {
    & "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" server.py
} else {
    Write-Host "[ERROR] Python tidak ditemukan di laptop ini!" -ForegroundColor Red
}
