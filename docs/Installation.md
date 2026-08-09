# Installation and Setup Guide

This guide provides step-by-step instructions to configure, install, and execute the Nifty 100 Financial Intelligence Platform on your local environment.

## 1. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version `3.11` or `3.12` installed.
- **Dependencies**: SQLite3 database engine (standard in python), Git.
- **Optional**: Docker & Docker Compose for containerized run.

---

## 2. Installation Steps

### Step 1: Clone the Repository
Clone this repository to your local system and navigate to the project directory:
```bash
git clone https://github.com/krishnavasnani07/n100-financial-intelligence-platform.git
cd n100-financial-intelligence-platform
```

### Step 2: Initialize Virtual Environment
Set up a clean virtual environment and install all packages.

**On Windows (Powershell/CMD)**:
```powershell
.\setup.bat
```
*(Or manually):*
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**On Linux/macOS**:
```bash
./setup.sh
```
*(Or manually):*
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the environment template file:
```bash
cp .env.example .env
```
Open `.env` and verify the settings:
```ini
ENV=development
DEBUG=True
DB_PATH=db/nifty100.db
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 3. Seeding the Database (ETL Pipeline)

The repository includes raw data in `data/raw/` (Excel files). Before running the API or Dashboard, you must parse and seed this data into the SQLite database.

Run the ETL loader pipeline:
```bash
# On Windows
.\run.bat etl

# On Linux/macOS
./run.sh etl
```
This script creates the database tables (configured via `db/schema.sql`) and populates them. You will see success logs verifying the rows inserted.

---

## 4. Verifying Installation (Unit Tests)

Verify that the local environment is operational by running the comprehensive unit test suite:
```bash
# On Windows
.\test.bat

# On Linux/macOS
./test.sh
```
All tests should pass with zero failures.
