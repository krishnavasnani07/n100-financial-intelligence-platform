import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Check if .env exists, if not warn the developer about .env.example
env_file = BASE_DIR / ".env"
if not env_file.exists():
    print(
        f"NOTICE: '.env' configuration file not found at {env_file.resolve()}.\n"
        f"You can copy '.env.example' to '.env' to configure local variables.\n"
        f"Using default configuration values for development...\n",
        file=sys.stderr
    )

# Load environment variables
load_dotenv(dotenv_path=env_file)

# App Configurations
ENV = os.getenv("ENV", "development").lower()
VALID_ENVS = {"development", "production", "testing"}
if ENV not in VALID_ENVS:
    print(
        f"WARNING: Invalid ENV value '{os.getenv('ENV')}' in environment. "
        f"Must be one of {VALID_ENVS}. Defaulting to 'development'.",
        file=sys.stderr
    )
    ENV = "development"

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
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
if LOG_LEVEL not in VALID_LOG_LEVELS:
    print(
        f"WARNING: Invalid LOG_LEVEL value '{os.getenv('LOG_LEVEL')}' in environment. "
        f"Must be one of {VALID_LOG_LEVELS}. Defaulting to 'INFO'.",
        file=sys.stderr
    )
    LOG_LEVEL = "INFO"

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
