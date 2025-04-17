@echo off
echo Setting up virtual environment and installing dependencies...

REM Check if Python 3 is installed
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3 and try again.
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist my-venv (
    echo Creating virtual environment 'my-venv'...
    python -m venv my-venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call my-venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install required packages
pip install requests

echo Installation complete!
echo.
echo To activate the virtual environment, run:
echo my-venv\Scripts\activate.bat
echo.
echo To run the application, activate the virtual environment and run:
echo python main.py

pause
