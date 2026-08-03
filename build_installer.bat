@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\PolishEditor.exe" (
    echo dist\PolishEditor.exe is missing. Run build_windows.bat first.
    pause
    exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 7\ISCC.exe"

if not exist "%ISCC%" (
    echo Inno Setup 7 was not found. Install it and run this file again.
    pause
    exit /b 1
)

"%ISCC%" installer\PolishEditor.iss
if errorlevel 1 (
    echo Installer build failed.
    pause
    exit /b 1
)

echo Installer ready: installer\output\PolishEditorSetup.exe
pause
