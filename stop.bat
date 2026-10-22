@echo off
REM ===========================================================================
REM  Stops the Django server if it is running on the port 8000.
REM  (Useful if the launcher window was closed by mistake.)
REM ===========================================================================
cd /d "%~dp0"
title Stop Student Information Platform

echo.
echo   Looking for a server on the port 8000 ...

set "FOUND=0"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    set "FOUND=1"
    echo   Stopping the process %%p ...
    taskkill /PID %%p /F >nul 2>&1
)

if "%FOUND%"=="0" (
    echo   No server was running on the port 8000.
) else (
    echo   The server has been stopped.
)

echo.
pause
