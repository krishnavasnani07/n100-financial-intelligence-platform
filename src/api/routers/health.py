import time
from fastapi import APIRouter
from src.database.queries import get_table_counts
from src.config.settings import DB_PATH

router = APIRouter(tags=["Health"])

# Record the start time of the API process
SERVER_START_TIME = time.monotonic()
API_VERSION = "1.0.0"


@router.get("/health")
def get_health():
    """
    Returns the health status of the API, database row counts, server uptime, and version.
    """
    uptime = time.monotonic() - SERVER_START_TIME
    try:
        counts = get_table_counts(DB_PATH)
        status = "ok"
    except Exception:
        counts = {}
        status = "database_error"

    return {
        "status": status,
        "db_row_counts": counts,
        "uptime_seconds": round(uptime, 2),
        "version": API_VERSION,
    }
