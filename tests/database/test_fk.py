import sqlite3
from pathlib import Path
import pytest
from src.database.database import init_db, get_connection
from src.database.queries import check_foreign_key_violations


def test_foreign_key_enforcement(tmp_path: Path):
    db_file = tmp_path / "test_fk.db"
    init_db(db_path=db_file)

    conn = get_connection(db_file)

    # Insert valid parent company
    conn.execute(
        "INSERT INTO companies (id, company_name) VALUES ('RELIANCE', 'Reliance Industries Ltd');"
    )
    conn.commit()

    # Attempting raw direct insertion of child record referencing missing company ID should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO sectors (company_id, broad_sector) VALUES ('NON_EXISTENT_TICKER', 'Energy');"
        )
        conn.commit()

    # Check foreign key violations function returns 0 violations for current DB state
    violations = check_foreign_key_violations(db_file)
    assert len(violations) == 0

    conn.close()
