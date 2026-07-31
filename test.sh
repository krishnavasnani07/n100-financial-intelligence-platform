#!/bin/bash
# ====================================================================
# Testing Helper Script for Unix / macOS / Git Bash
# ====================================================================

if [ ! -d ".venv" ]; then
    echo "[ERROR] Virtual environment (.venv) not found. Please run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate
export PYTHONPATH="."

echo "Running Pytest Suite..."
pytest "$@"
exit $?
