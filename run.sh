#!/bin/bash
# ====================================================================
# Execution Helper Script for Unix / macOS / Git Bash
# ====================================================================

if [ ! -d ".venv" ]; then
    echo "[ERROR] Virtual environment (.venv) not found. Please run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate

if [ "$1" = "etl" ]; then
    echo "Running ETL and Data Validation Pipeline..."
    python main.py
    exit $?
elif [ "$1" = "app" ]; then
    echo "Launching Streamlit Web Dashboard..."
    streamlit run app.py
    exit $?
elif [ "$1" = "api" ]; then
    echo "Launching uvicorn API server..."
    uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
    exit $?
elif [ "$1" = "report" ]; then
    echo "Generating Portfolio Summary PDF Report..."
    python -m src.reports.portfolio_summary
    exit $?
elif [ -z "$1" ]; then
    echo "[NOTICE] Running default flow: ETL Pipeline, then Streamlit Dashboard..."
    echo "===================================================================="
    echo "Phase 1: Running Ingestion and Validation ETL"
    python main.py
    if [ $? -ne 0 ]; then
        echo "[ERROR] ETL pipeline failed. Skipping Streamlit app start."
        exit 1
    fi
    echo "===================================================================="
    echo "Phase 2: Launching Streamlit Web Dashboard"
    streamlit run app.py
    exit $?
else
    echo "[ERROR] Unknown option: $1"
    echo "Usage:"
    echo "  ./run.sh        - Runs ETL, then launches Streamlit Dashboard"
    echo "  ./run.sh etl    - Runs ETL and Data Validation Pipeline"
    echo "  ./run.sh app    - Launches Streamlit Web Dashboard"
    echo "  ./run.sh api    - Launches FastAPI server"
    echo "  ./run.sh report - Generates Portfolio Summary PDF Report"
    exit 1
fi
