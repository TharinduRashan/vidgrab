@echo off
REM ============================================================
REM  VidGrab - Single EXE Build Script
REM  Double-click this file OR run from project root:  build.bat
REM ============================================================
setlocal enabledelayedexpansion

echo.
echo  ==========================================
echo   VidGrab - Build Script
echo  ==========================================
echo.

REM ── 1. Install / upgrade dependencies ────────────────────────────────────
echo [1/4] Installing Python dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo     Done.
echo.

REM ── 2. Clean previous build ───────────────────────────────────────────────
echo [2/4] Cleaning previous build artifacts...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
echo     Done.
echo.

REM ── 3. Build single EXE with PyInstaller ─────────────────────────────────
echo [3/4] Building VidGrab.exe (this takes 1-3 minutes)...
pyinstaller VidGrab.spec --clean --noconfirm
echo.

REM ── 4. Check result ───────────────────────────────────────────────────────
echo [4/4] Checking output...
if exist "dist\VidGrab.exe" (
    echo.
    echo  ==========================================
    echo   BUILD SUCCESSFUL!
    echo.
    echo   File: dist\VidGrab.exe
    echo.
    echo   Share ONLY that single .exe file.
    echo   Users need NO Python or any other
    echo   software installed to run it.
    echo  ==========================================
    echo.
    REM Open the dist folder automatically
    explorer dist
) else (
    echo.
    echo  BUILD FAILED - check errors above.
    echo  Common fixes:
    echo    - Make sure Python is installed
    echo    - Run:  pip install pyinstaller
    echo    - Try running as Administrator
    exit /b 1
)

echo.
pause
