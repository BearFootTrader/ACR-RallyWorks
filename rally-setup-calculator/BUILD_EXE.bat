@echo off
title Building Rally Setup Calculator Executable
echo ===============================================
echo  Building Rally Car Setup Calculator
echo  Standalone Executable
echo ===============================================
echo.

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Building executable...
echo.

cd /d "%~dp0"

pyinstaller --onefile --windowed ^
    --name "Rally Setup Calculator" ^
    --add-data "src;src" ^
    run.py

echo.
echo ===============================================
if exist "dist\Rally Setup Calculator.exe" (
    echo BUILD SUCCESSFUL!
    echo Executable located at: dist\Rally Setup Calculator.exe
) else (
    echo BUILD FAILED - Check errors above
)
echo ===============================================
pause
