@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ==============================================
echo   Menjalankan Dashboard Web RSA vs RSA-CRT...
echo ==============================================
python -m streamlit run app.py
pause
