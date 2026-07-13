import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env in the base directory
load_dotenv(dotenv_path=BASE_DIR / ".env")

# App Configurations
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t", "y", "yes")

# Centralized Paths (resolved to absolute paths)
DB_PATH = Path(os.getenv("DB_PATH", "db/nifty100.db"))
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH

SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

OUTPUT_DIR = BASE_DIR / "output"
AUDIT_DIR = OUTPUT_DIR / "audit"
REPORTS_DIR = OUTPUT_DIR / "reports"
VALIDATION_DIR = OUTPUT_DIR / "validation"

# Logging Configurations
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = Path(os.getenv("LOG_FILE", "logs/app.log"))
if not LOG_FILE.is_absolute():
    LOG_FILE = BASE_DIR / LOG_FILE

# Ensure critical directories exist when settings are loaded
for path in [
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    EXTERNAL_DATA_DIR,
    OUTPUT_DIR,
    AUDIT_DIR,
    REPORTS_DIR,
    VALIDATION_DIR,
    LOG_FILE.parent,
    DB_PATH.parent,
]:
    path.mkdir(parents=True, exist_ok=True)
