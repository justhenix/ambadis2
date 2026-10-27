@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo ========================================================
echo   Membuka Dashboard Web Interaktif RSA vs RSA-CRT...
echo ========================================================

:: 1. Coba perintah 'py' (Python Launcher resmi Windows)
where py >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo Menggunakan launcher Python: py
    py server.py
    goto end
)

:: 2. Coba perintah 'python'
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo Menggunakan perintah: python
    python server.py
    goto end
)

:: 3. Coba path direktori Python di LocalAppData
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    echo Menjalankan dari direktori Python313...
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" server.py
    goto end
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%D\python.exe" (
        echo Menjalankan dari %%D\python.exe...
        "%%D\python.exe" server.py
        goto end
    )
)

echo.
echo [ERROR] Python tidak ditemukan di laptop ini!
echo Pastikan Python sudah terinstall dari python.org.
echo.

:end
pause
