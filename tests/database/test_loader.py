from pathlib import Path
import pandas as pd
from src.database.loader import DatabaseLoader
from src.database.queries import get_table_counts


def test_database_loader(tmp_path: Path):
    db_file = tmp_path / "test_loader.db"
    audit_dir = tmp_path / "audit"

    # Create dummy mock dataframes
    df_companies = pd.DataFrame(
        [
            {"id": "TCS", "company_name": "Tata Consultancy Services"},
            {"id": "INFY", "company_name": "Infosys Ltd"},
        ]
    )

    df_pl = pd.DataFrame(
        [
            {
                "company_id": "TCS",
                "year": "2023-03",
                "sales": 225458.0,
                "net_profit": 42147.0,
            },
            {
                "company_id": "INFY",
                "year": "2023-03",
                "sales": 146767.0,
                "net_profit": 24095.0,
            },
            # Invalid FK reference row (should be filtered out by loader)
            {
                "company_id": "UNKNOWN_COMP",
                "year": "2023-03",
                "sales": 100.0,
                "net_profit": 10.0,
            },
        ]
    )

    dfs = {"companies": df_companies, "profitandloss": df_pl}

    loader = DatabaseLoader(db_path=db_file, audit_dir=audit_dir)
    res = loader.load_all(dfs)

    assert res["success"] is True
    assert res["total_inserted"] == 4  # 2 companies + 2 valid PL
    assert res["total_rejected"] == 1  # 1 invalid PL row with unknown FK

    # Verify counts in DB
    counts = get_table_counts(db_file)
    assert counts["companies"] == 2
    assert counts["profitandloss"] == 2

    # Verify audit CSV generated
    audit_csv = audit_dir / "load_audit.csv"
    assert audit_csv.exists()
    assert audit_csv.stat().st_size > 0
