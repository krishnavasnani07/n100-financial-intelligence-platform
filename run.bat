@echo off
rem ====================================================================
rem Execution Helper Script for Windows
rem ====================================================================

if not exist "%~dp0.venv" goto venv_missing

call "%~dp0.venv\Scripts\activate.bat"

if "%1" == "etl" goto run_etl
if "%1" == "app" goto run_app
if "%1" == "api" goto run_api
if "%1" == "" goto run_default

echo [ERROR] Unknown option: %1
goto show_usage

:run_etl
echo Running ETL and Data Validation Pipeline...
python "%~dp0main.py"
exit /b %errorlevel%

:run_app
echo Launching Streamlit Web Dashboard...
streamlit run "%~dp0app.py"
exit /b %errorlevel%

:run_api
echo Launching uvicorn API server...
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
exit /b %errorlevel%

:run_default
echo [NOTICE] Running default flow: ETL Pipeline, then Streamlit Dashboard...
echo ====================================================================
echo Phase 1: Running Ingestion and Validation ETL
python "%~dp0main.py"
if %errorlevel% neq 0 goto etl_failed
echo ====================================================================
echo Phase 2: Launching Streamlit Web Dashboard
streamlit run "%~dp0app.py"
exit /b %errorlevel%

:etl_failed
echo [ERROR] ETL pipeline failed. Skipping Streamlit app start.
exit /b %errorlevel%

:venv_missing
echo [ERROR] Virtual environment (.venv) not found. Please run setup.bat first.
exit /b 1

:show_usage
echo Usage:
echo   run.bat        - Runs ETL, then launches Streamlit Dashboard
echo   run.bat etl    - Runs ETL and Data Validation Pipeline
echo   run.bat app    - Launches Streamlit Web Dashboard
echo   run.bat api    - Launches FastAPI server
exit /b 1
