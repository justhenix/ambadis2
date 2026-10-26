$env:PYTHONIOENCODING = "utf-8"
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Menjalankan Dashboard Web RSA vs RSA-CRT... " -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
python -m streamlit run app.py
