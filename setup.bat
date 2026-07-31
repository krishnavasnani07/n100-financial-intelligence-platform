@echo off
rem ====================================================================
rem Developer Onboarding Setup Script for Windows
rem ====================================================================

echo [1/4] Checking python installation...
where python >nul 2>nul
if %errorlevel% neq 0 goto no_python

echo [2/4] Initializing Python Virtual Environment (.venv)...
if not exist "%~dp0.venv" python -m venv "%~dp0.venv"
echo Virtual environment setup checked.

echo [3/4] Copying environment configuration...
if not exist "%~dp0.env" copy "%~dp0.env.example" "%~dp0.env" >nul
echo Environment configuration check completed.

echo [4/4] Installing dependencies...
call "%~dp0.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

echo ====================================================================
echo SUCCESS: Developer setup complete!
echo ====================================================================
echo To activate the environment:
echo   call .venv\Scripts\activate
echo.
echo To run the full ETL pipeline:
echo   run.bat etl
echo.
echo To launch the Streamlit dashboard:
echo   run.bat app
echo.
echo To execute the test suite:
echo   test.bat
echo ====================================================================
goto :eof

:no_python
echo [ERROR] Python was not found in your PATH. Please install Python 3.11 or 3.12 and try again.
exit /b 1
