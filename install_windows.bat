@echo off
REM Windows Installation Helper for Movement Detection System
REM This script guides users through installing dependencies on Windows
REM Author: Movement Detection Security System

echo.
echo ========================================================
echo     Movement Detection System - Windows Installation    
echo ========================================================
echo.

REM Check for Python installation
echo Checking for Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found in PATH!
    echo Please install Python 3.7 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo After installing, make sure to check "Add Python to PATH"
    echo during the installation process.
    echo.
    pause
    exit /b 1
)

REM Verify Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
echo Found Python %PYTHON_VERSION%

REM Upgrade pip
echo.
echo Upgrading pip to the latest version...
python -m pip install --upgrade pip

REM Create virtual environment (optional)
echo.
echo Would you like to create a virtual environment? (Recommended)
echo This keeps the dependencies isolated from your system Python.
set /p CREATE_VENV="Create virtual environment? (y/n): "

if /i "%CREATE_VENV%"=="y" (
    echo.
    echo Creating virtual environment...
    python -m pip install --upgrade virtualenv
    python -m virtualenv venv
    
    echo.
    echo Activating virtual environment...
    call venv\Scripts\activate
    
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create or activate virtual environment!
        echo Installation will continue using system Python.
    ) else (
        echo Virtual environment created and activated successfully.
    )
)

REM Install dependencies
echo.
echo Installing required dependencies...
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error installing dependencies!
    echo.
    pause
    exit /b 1
)

REM Verify installation
echo.
echo Verifying installation...
python verify_dependencies.py

echo.
echo ========================================================
echo     Installation complete!
echo.
echo     Run the system using: python start_system.py --all
echo ========================================================
echo.

pause
