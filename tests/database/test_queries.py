import pytest
from pathlib import Path
from src.database.database import init_db, get_connection
from src.database.queries import (
    get_table_counts,
    check_foreign_key_violations,
    query_to_dataframe,
)


def test_get_table_counts(tmp_path: Path):
    db_file = tmp_path / "test_queries.db"
    init_db(db_path=db_file)

    conn = get_connection(db_file)
    conn.execute(
        "INSERT INTO companies (id, company_name) VALUES ('RELIANCE', 'Reliance Industries Ltd');"
    )
    conn.commit()
    conn.close()

    counts = get_table_counts(db_file)
    assert isinstance(counts, dict)
    assert counts.get("companies") == 1
    assert counts.get("profitandloss") == 0


def test_check_foreign_key_violations_clean(tmp_path: Path):
    db_file = tmp_path / "test_fk_clean.db"
    init_db(db_path=db_file)

    conn = get_connection(db_file)
    conn.execute(
        "INSERT INTO companies (id, company_name) VALUES ('TCS', 'Tata Consultancy Services');"
    )
    conn.execute(
        "INSERT INTO sectors (company_id, broad_sector) VALUES ('TCS', 'Information Technology');"
    )
    conn.commit()
    conn.close()

    violations = check_foreign_key_violations(db_file)
    assert len(violations) == 0


def test_query_to_dataframe(tmp_path: Path):
    db_file = tmp_path / "test_query_df.db"
    init_db(db_path=db_file)

    conn = get_connection(db_file)
    conn.execute(
        "INSERT INTO companies (id, company_name) VALUES ('INFY', 'Infosys Ltd');"
    )
    conn.commit()
    conn.close()

    df = query_to_dataframe(
        "SELECT id, company_name FROM companies WHERE id = ?",
        db_path=db_file,
        params=["INFY"],
    )
    assert len(df) == 1
    assert df.iloc[0]["id"] == "INFY"
    assert df.iloc[0]["company_name"] == "Infosys Ltd"
