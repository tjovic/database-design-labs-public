@echo off
REM Builds dist\obp-rest-demo.exe (run on Windows, from this folder).
cd /d "%~dp0"

if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --onefile --name obp-rest-demo --collect-submodules uvicorn run.py
if errorlevel 1 exit /b 1

if not exist dist\config.env copy config.env.example dist\config.env

echo.
echo Done. Copy these two files to the lab computer:
echo   dist\obp-rest-demo.exe
echo   dist\config.env
