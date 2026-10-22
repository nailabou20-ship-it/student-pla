@echo off
REM ===========================================================================
REM  STUDENT INFORMATION PLATFORM - ESGEN
REM  Launcher: prepares everything and starts the web server.
REM
REM  Just double-click this file. Nothing else to do.
REM
REM  NOTE FOR THE DEVELOPER: this file uses "goto" and NOT the
REM  "if ( ... )" blocks, because a ")" written inside an echo command
REM  closes the block too early and breaks the script.
REM ===========================================================================
REM NOTE: "setlocal" WITHOUT "enabledelayedexpansion", because with the delayed
REM expansion the "!" characters written in the messages are swallowed.
setlocal
cd /d "%~dp0"
title Student Information Platform - ESGEN

echo.
echo   ============================================================
echo     STUDENT INFORMATION PLATFORM
echo     ESGEN - Master in Data Management
echo   ============================================================
echo.

REM ---------------------------------------------------------------------------
REM  1. Is Python installed ?
REM ---------------------------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 goto NO_PYTHON

REM ---------------------------------------------------------------------------
REM  2. The virtual environment - created only once
REM ---------------------------------------------------------------------------
if exist ".venv\Scripts\python.exe" goto VENV_READY
echo   [1/5] Creating the virtual environment .venv ...
python -m venv .venv
if errorlevel 1 goto VENV_ERROR
:VENV_READY
echo   [1/5] The virtual environment is ready.

REM From now on we use the Python of the project, not the system one.
set "PYTHON=%~dp0.venv\Scripts\python.exe"

REM ---------------------------------------------------------------------------
REM  3. The packages - Django
REM ---------------------------------------------------------------------------
"%PYTHON%" -c "import django" >nul 2>&1
if not errorlevel 1 goto PACKAGES_READY
echo   [2/5] Installing the packages - Django ...
"%PYTHON%" -m pip install --upgrade pip --quiet
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto PACKAGES_ERROR
:PACKAGES_READY
echo   [2/5] The packages are ready.

REM ---------------------------------------------------------------------------
REM  4. The database - the file db.sqlite3
REM ---------------------------------------------------------------------------
echo   [3/5] Preparing the database ...
"%PYTHON%" manage.py migrate --noinput
if errorlevel 1 goto DB_ERROR

REM ---------------------------------------------------------------------------
REM  5. The administrator account - admin / admin123
REM     The command below returns 0 when the account ALREADY exists.
REM ---------------------------------------------------------------------------
"%PYTHON%" manage.py shell -c "from django.contrib.auth.models import User; import sys; sys.exit(0 if User.objects.filter(username='admin').exists() else 1)" >nul 2>&1
if not errorlevel 1 goto ADMIN_READY
echo   [4/5] Creating the administrator account ...
set "DJANGO_SUPERUSER_USERNAME=admin"
set "DJANGO_SUPERUSER_PASSWORD=admin123"
set "DJANGO_SUPERUSER_EMAIL=admin@esgen.dz"
"%PYTHON%" manage.py createsuperuser --noinput
:ADMIN_READY
echo   [4/5] The administrator account is ready - admin / admin123

REM ---------------------------------------------------------------------------
REM  6. The demo students - only when the database is empty
REM ---------------------------------------------------------------------------
"%PYTHON%" manage.py shell -c "from students.models import Student; import sys; sys.exit(0 if Student.objects.count() == 0 else 1)" >nul 2>&1
if not errorlevel 1 goto DEMO_ADD
echo   [5/5] The database already contains students.
goto DEMO_DONE
:DEMO_ADD
echo   [5/5] Adding the demo students ...
"%PYTHON%" manage.py seed_students
:DEMO_DONE

REM ---------------------------------------------------------------------------
REM  7. Is the port 8000 already used ?
REM ---------------------------------------------------------------------------
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 goto START_SERVER
echo.
echo   [!] The port 8000 is already in use: the server is probably already
echo       running. Open http://127.0.0.1:8000/ in your browser.
echo.
echo       To start it on another port, close the other window first or run:
echo       .venv\Scripts\python.exe manage.py runserver 8001
echo.
pause
exit /b 0

REM ---------------------------------------------------------------------------
REM  8. Start the server
REM ---------------------------------------------------------------------------
:START_SERVER
echo.
echo   ============================================================
echo     Everything is ready. Starting the server ...
echo.
echo     Platform : http://127.0.0.1:8000/
echo     Form     : http://127.0.0.1:8000/add/
echo     Admin    : http://127.0.0.1:8000/admin/   - admin / admin123
echo.
echo     Press CTRL + C to stop the server.
echo   ============================================================
echo.

REM Open the browser 3 seconds after the server has started.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000/'"

REM The server runs in this window: its messages are shown here.
"%PYTHON%" manage.py runserver

echo.
echo   The server has been stopped. You can close this window.
pause
exit /b 0

REM ===========================================================================
REM  The error messages
REM ===========================================================================
:NO_PYTHON
echo   [X] Python is not installed or it is not in the PATH.
echo.
echo       Install Python 3.10 or more from https://www.python.org/downloads/
echo       Do not forget to tick "Add Python to PATH" during the installation.
echo       Then run this file again.
echo.
pause
exit /b 1

:VENV_ERROR
echo   [X] The virtual environment could not be created.
echo       Delete the folder .venv and run this file again.
echo.
pause
exit /b 1

:PACKAGES_ERROR
echo   [X] The packages could not be installed.
echo       Check your internet connection and run this file again.
echo.
pause
exit /b 1

:DB_ERROR
echo   [X] The database could not be prepared.
echo.
pause
exit /b 1
