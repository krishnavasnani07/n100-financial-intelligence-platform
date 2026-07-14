import sqlite3
import pytest
import pandas as pd
from pathlib import Path

from src.etl.loader import load_excel
from src.database.database import init_db, get_connection, get_db
from src.database.loader import DatabaseLoader
from src.validation.exceptions import DataLoadError
from src.validation.validator import DataValidator


def test_missing_excel_file_recovery(tmp_path: Path):
    non_existent = tmp_path / "non_existent_file.xlsx"
    result = load_excel(non_existent)
    assert result is None

    # Test DataValidator raises DataLoadError for missing dataset directory
    validator = DataValidator(raw_data_dir=tmp_path)
    with pytest.raises(DataLoadError, match="Missing required dataset"):
        validator.load_all_datasets()


def test_empty_dataframe_recovery(tmp_path: Path):
    db_file = tmp_path / "test_empty.db"
    audit_dir = tmp_path / "audit"
    init_db(db_path=db_file)

    loader = DatabaseLoader(db_path=db_file, audit_dir=audit_dir)
    empty_dfs = {
        "companies": pd.DataFrame(),
        "profitandloss": pd.DataFrame(),
    }

    res = loader.load_all(empty_dfs)
    assert res["success"] is True
    assert res["total_inserted"] == 0
    assert res["total_rejected"] == 0


def test_transaction_rollback_on_duplicate_pk(tmp_path: Path):
    db_file = tmp_path / "test_rollback_pk.db"
    init_db(db_path=db_file)

    # Context manager should rollback changes if error occurs
    with pytest.raises(sqlite3.IntegrityError):
        with get_db(db_file) as conn:
            conn.execute("INSERT INTO companies (id, company_name) VALUES ('RELIANCE', 'Reliance Ltd');")
            # Duplicate PK insertion should fail transaction
            conn.execute("INSERT INTO companies (id, company_name) VALUES ('RELIANCE', 'Duplicate Ltd');")

    # Verify database state was rolled back completely
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies;")
    assert cursor.fetchone()[0] == 0
    conn.close()


def test_transaction_rollback_on_fk_violation(tmp_path: Path):
    db_file = tmp_path / "test_rollback_fk.db"
    init_db(db_path=db_file)

    with pytest.raises(sqlite3.IntegrityError):
        with get_db(db_file) as conn:
            # Inserting into child table without parent company present
            conn.execute("INSERT INTO sectors (company_id, broad_sector) VALUES ('INVALID_TICKER', 'Tech');")

    # Verify no orphan rows were committed
    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sectors;")
    assert cursor.fetchone()[0] == 0
    conn.close()
