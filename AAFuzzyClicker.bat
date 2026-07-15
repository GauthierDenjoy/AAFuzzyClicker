@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "MARKER=%~dp0.installed"

call :findpy
if exist "%MARKER%" goto :launch

echo ============================================
echo    AAFuzzyClicker - first-time setup
echo ============================================
echo.
echo This will install what AAFuzzyClicker needs:
echo    - Python 3           (only if it is missing)
echo    - Python packages    opencv-python, pillow
echo.
choice /c YN /m "Install these now"
if errorlevel 2 (
    echo.
    echo Setup cancelled. Nothing was installed.
    pause
    exit /b
)
echo.

if not defined PY (
    echo Python was not found. Trying to install it with winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo.
        echo winget is not available on this PC.
        echo Please install Python from python.org, then run this file again.
        start "" https://www.python.org/downloads/
        pause
        exit /b
    )
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    call :findpy
)

if not defined PY (
    echo.
    echo Python still not found. Please restart your PC and run this file again.
    pause
    exit /b
)

echo Installing Python packages...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo Package installation failed. See the messages above.
    pause
    exit /b
)

echo installed> "%MARKER%"
echo.
echo Setup complete. Starting AAFuzzyClicker...

:launch
where pyw >nul 2>nul && ( start "" pyw "%~dp0aafuzzyclicker.py" & exit /b )
where pythonw >nul 2>nul && ( start "" pythonw "%~dp0aafuzzyclicker.py" & exit /b )
if defined PY (
    start "" %PY% "%~dp0aafuzzyclicker.py"
) else (
    echo Python was not found. Run this file again to install it.
    pause
)
exit /b

:findpy
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
exit /b
