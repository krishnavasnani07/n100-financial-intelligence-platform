from pathlib import Path
from src.database.database import init_db, get_connection
from src.database.queries import get_table_counts


def test_schema_initialization(tmp_path: Path):
    db_file = tmp_path / "test_schema.db"
    init_db(db_path=db_file)

    counts = get_table_counts(db_path=db_file)
    # Check that all 11 tables exist in the initialized schema
    expected_tables = [
        "analysis",
        "balancesheet",
        "cashflow",
        "companies",
        "documents",
        "financial_ratios",
        "peer_groups",
        "profitandloss",
        "prosandcons",
        "sectors",
        "stock_prices",
    ]

    for tbl in expected_tables:
        assert tbl in counts
        assert counts[tbl] == 0  # Table exists and is empty initially


def test_schema_indexes_exist(tmp_path: Path):
    db_file = tmp_path / "test_indexes.db"
    init_db(db_path=db_file)

    conn = get_connection(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';"
    )
    indexes = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "idx_sectors_company_id" in indexes
    assert "idx_pl_company_year" in indexes
    assert "idx_stock_prices_company_date" in indexes
