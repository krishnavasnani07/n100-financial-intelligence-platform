@echo off
rem ====================================================================
rem Testing Helper Script for Windows
rem ====================================================================

if not exist "%~dp0.venv" goto venv_missing

call "%~dp0.venv\Scripts\activate.bat"
set PYTHONPATH=%~dp0

echo Running Pytest Suite...
pytest "%~dp0tests" %*
exit /b %errorlevel%

:venv_missing
echo [ERROR] Virtual environment not found. Please run setup.bat first.
exit /b 1
