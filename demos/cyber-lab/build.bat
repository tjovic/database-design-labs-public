@echo off
REM Builds dist\cyber-lab.exe (run on Windows, from this folder).
cd /d "%~dp0"

if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --onefile --name cyber-lab ^
  --collect-submodules uvicorn ^
  --hidden-import python_multipart --hidden-import multipart ^
  --add-data "app\templates;app\templates" ^
  --add-data "app\static;app\static" ^
  run.py
if errorlevel 1 exit /b 1

if not exist dist\config.env copy config.env.example dist\config.env
xcopy /e /i /y database dist\database >nul

echo.
echo Done. Copy the whole dist folder to the lab computer:
echo   dist\cyber-lab.exe
echo   dist\config.env
echo   dist\database\
