@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating the Python environment...
    py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error
python Polish_Editor.py
exit /b %errorlevel%

:error
echo.
echo Setup failed. Confirm that 64-bit Python 3.11 or newer is installed.
pause
exit /b 1
