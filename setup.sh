#!/bin/bash
# ====================================================================
# Developer Onboarding Setup Script for Unix / macOS / Git Bash
# ====================================================================

set -e

echo "[1/4] Checking python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 was not found in your PATH. Please install Python 3.11 or 3.12 and try again."
    exit 1
fi

echo "[2/4] Initializing Python Virtual Environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created virtual environment .venv"
else
    echo "Virtual environment .venv already exists"
fi

echo "[3/4] Copying environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from .env.example template"
else
    echo ".env file already exists"
fi

echo "[4/4] Installing dependencies..."
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "===================================================================="
echo "SUCCESS: Developer setup complete!"
echo "===================================================================="
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the full ETL pipeline:"
echo "  ./run.sh etl"
echo ""
echo "To launch the Streamlit dashboard:"
echo "  ./run.sh app"
echo ""
echo "To execute the test suite:"
echo "  ./test.sh"
echo "===================================================================="
