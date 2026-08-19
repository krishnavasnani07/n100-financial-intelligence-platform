import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Explicitly enables foreign key constraint enforcement.
    """
    if db_path is None:
        db_path = settings.DB_PATH

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(str(db_path))
        # Explicitly enable foreign key checks as required by spec
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for enhanced performance and concurrent read access
        conn.execute("PRAGMA journal_mode = WAL;")
        logger.debug(f"Connected to SQLite database at {db_path} (Foreign keys ON)")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to SQLite database at {db_path}: {e}")
        raise


@contextmanager
def get_db(
    db_path: Path | str | None = None,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections that automatically handles
    commit and rollback on exceptions.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed, changes rolled back: {e}")
        raise
    finally:
        conn.close()


def init_db(
    db_path: Path | str | None = None, schema_path: Path | str | None = None
) -> None:
    """
    Initializes the database by executing schema.sql statements.
    """
    if db_path is None:
        db_path = settings.DB_PATH
    if schema_path is None:
        schema_path = settings.SCHEMA_PATH

    db_path = Path(db_path)
    schema_path = Path(schema_path)
    if not schema_path.exists():
        err_msg = f"Schema file not found at {schema_path}"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    # Remove existing database file and journal sidecars to guarantee clean schema state
    if db_path.exists():
        try:
            db_path.unlink()
            wal_file = Path(str(db_path) + "-wal")
            shm_file = Path(str(db_path) + "-shm")
            if wal_file.exists():
                wal_file.unlink()
            if shm_file.exists():
                shm_file.unlink()
            logger.info(f"Cleared pre-existing database file at {db_path}")
        except Exception as e:
            logger.warning(f"Could not remove old db file {db_path}: {e}")

    logger.info(f"Initializing database at {db_path} using schema {schema_path}...")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_script = f.read()

    with get_db(db_path) as conn:
        conn.executescript(schema_script)

    logger.info("Database schema initialized successfully.")
