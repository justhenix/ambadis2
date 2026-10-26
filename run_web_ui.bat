@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ========================================================
echo   Membuka Dashboard Web Interaktif RSA vs RSA-CRT...
echo ========================================================
python server.py
pause
