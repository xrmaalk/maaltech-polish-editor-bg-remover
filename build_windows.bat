@echo off
setlocal
cd /d "%~dp0"

echo [1/5] Preparing build environment...
if not exist ".venv-build\Scripts\python.exe" (
    py -3.12 -m venv .venv-build 2>nul || py -3 -m venv .venv-build
    if errorlevel 1 goto :error
)
call ".venv-build\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

echo [2/5] Generating application icon...
python tools\generate_icon.py
if errorlevel 1 goto :error

echo [3/5] Building the standalone Windows EXE...
python -m PyInstaller --noconfirm --clean PolishEditor.spec
if errorlevel 1 goto :error

echo [4/5] Validating the packaged background-removal engine...
dist\PolishEditor.exe --self-test-background
if errorlevel 1 (
    if exist "PolishEditor_background_self_test.log" type "PolishEditor_background_self_test.log"
    goto :error
)

echo [5/5] Looking for Inno Setup 7...
set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 7\ISCC.exe"

if exist "%ISCC%" (
    "%ISCC%" installer\PolishEditor.iss
    if errorlevel 1 goto :error
    echo.
    echo Build complete:
    echo   Portable EXE: dist\PolishEditor.exe
    echo   Installer:    installer\output\PolishEditorSetup.exe
) else (
    echo.
    echo The portable EXE is ready at dist\PolishEditor.exe
    echo Inno Setup 7 was not found, so the installer was skipped.
    echo Install Inno Setup 7, then run build_installer.bat.
)

pause
exit /b 0

:error
echo.
echo Build failed. Review the message above for details.
pause
exit /b 1
