@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_project.ps1"
if errorlevel 1 (
    echo.
    echo El proyecto termino con errores.
    pause
    exit /b 1
)

endlocal
