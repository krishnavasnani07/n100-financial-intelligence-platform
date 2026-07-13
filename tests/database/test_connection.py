import sqlite3
from pathlib import Path
from src.database.database import get_connection, get_db


def test_connection_creation(tmp_path: Path):
    db_file = tmp_path / "test_nifty.db"
    conn = get_connection(db_file)
    assert isinstance(conn, sqlite3.Connection)

    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    # Verify foreign_keys PRAGMA is ON (1)
    assert fk_status == 1
    conn.close()


def test_context_manager_commit(tmp_path: Path):
    db_file = tmp_path / "test_ctx.db"
    with get_db(db_file) as conn:
        conn.execute("CREATE TABLE test_tbl (id INT PRIMARY KEY, val TEXT);")
        conn.execute("INSERT INTO test_tbl VALUES (1, 'demo');")

    # Reopen connection and verify row persisted
    conn2 = get_connection(db_file)
    cursor = conn2.cursor()
    cursor.execute("SELECT val FROM test_tbl WHERE id = 1;")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "demo"
    conn2.close()
