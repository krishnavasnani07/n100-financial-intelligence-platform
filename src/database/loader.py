import csv
import time
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd

from src.config import settings
from src.database.database import get_db, init_db
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Mandatory load order enforcing parent-child relational dependencies
LOAD_ORDER = [
    ("companies", "companies.xlsx"),
    ("sectors", "sectors.xlsx"),
    ("analysis", "analysis.xlsx"),
    ("prosandcons", "prosandcons.xlsx"),
    ("profitandloss", "profitandloss.xlsx"),
    ("balancesheet", "balancesheet.xlsx"),
    ("cashflow", "cashflow.xlsx"),
    ("documents", "documents.xlsx"),
    ("stock_prices", "stock_prices.xlsx"),
    ("peer_groups", "peer_groups.xlsx"),
]


class DatabaseLoader:
    def __init__(self, db_path: Path | str = None, audit_dir: Path | str = None):
        self.db_path = Path(db_path) if db_path else settings.DB_PATH
        self.audit_dir = Path(audit_dir) if audit_dir else settings.AUDIT_DIR
        self.audit_records: List[Dict[str, Any]] = []

    def prepare_data_for_loading(
        self, table_name: str, df: pd.DataFrame, valid_company_ids: set
    ) -> Tuple[pd.DataFrame, int]:
        """
        Cleans and filters DataFrame to ensure strict PK and FK compliance before insertion.
        Returns (df_to_insert, rejected_count).
        """
        rows_read = len(df)
        df_clean = df.copy()

        # Clean column names
        df_clean.columns = [str(c).strip().lower() for c in df_clean.columns]

        # 1. Foreign Key Filter: Ensure company_id exists in companies table if applicable
        if table_name != "companies" and "company_id" in df_clean.columns:
            df_clean = df_clean[
                df_clean["company_id"].dropna().astype(str).str.strip().isin(valid_company_ids)
            ]

        # 2. Primary Key Uniqueness Filter
        if table_name == "companies":
            df_clean = df_clean.drop_duplicates(subset=["id"], keep="first")
        elif table_name in ["profitandloss", "balancesheet", "cashflow"]:
            df_clean = df_clean.drop_duplicates(
                subset=["company_id", "year"], keep="first"
            )
        elif table_name == "stock_prices":
            df_clean = df_clean.drop_duplicates(
                subset=["company_id", "date"], keep="first"
            )

        # Drop explicit 'id' auto-increment column if present in raw sheet to let SQLite handle AUTOINCREMENT
        if table_name in ["sectors", "analysis", "prosandcons", "documents", "peer_groups"]:
            if "id" in df_clean.columns:
                df_clean = df_clean.drop(columns=["id"])

        rows_inserted = len(df_clean)
        rows_rejected = rows_read - rows_inserted

        return df_clean, rows_rejected

    def load_table(
        self, table_name: str, df: pd.DataFrame, valid_company_ids: set
    ) -> set:
        """
        Loads a single DataFrame into SQLite within a transaction context.
        """
        start_time = time.time()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows_read = len(df)

        df_to_insert, rows_rejected = self.prepare_data_for_loading(
            table_name, df, valid_company_ids
        )
        rows_inserted = len(df_to_insert)

        logger.info(
            f"Loading table '{table_name}': {rows_read} rows read, {rows_inserted} inserting, {rows_rejected} rejected."
        )

        with get_db(self.db_path) as conn:
            # Use to_sql with if_exists='append' inside the transaction block
            df_to_insert.to_sql(
                name=table_name,
                con=conn,
                if_exists="append",
                index=False,
                chunksize=1000,
            )

        runtime_sec = round(time.time() - start_time, 4)

        # Record audit metric
        audit_entry = {
            "table": table_name,
            "rows_read": rows_read,
            "rows_inserted": rows_inserted,
            "rows_rejected": rows_rejected,
            "runtime": f"{runtime_sec}s",
            "timestamp": timestamp,
        }
        self.audit_records.append(audit_entry)

        # If loading companies, update active valid_company_ids
        if table_name == "companies":
            valid_company_ids = set(df_to_insert["id"].dropna().astype(str).str.strip().unique())

        return valid_company_ids

    def save_audit_report(self) -> Path:
        """
        Writes the load_audit.csv file to the audit directory.
        """
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        audit_file = self.audit_dir / "load_audit.csv"

        fieldnames = [
            "table",
            "rows_read",
            "rows_inserted",
            "rows_rejected",
            "runtime",
            "timestamp",
        ]

        with open(audit_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.audit_records:
                writer.writerow(record)

        logger.info(f"Successfully generated load audit report at {audit_file}")
        return audit_file

    def load_all(self, normalized_dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Executes the end-to-end database loading process in strict topological order.
        """
        logger.info("Initializing database schema before loading...")
        init_db(self.db_path)

        valid_company_ids: set = set()

        for table_name, file_name in LOAD_ORDER:
            df = normalized_dfs.get(table_name)
            if df is None or df.empty:
                logger.warning(f"No DataFrame found for table '{table_name}'. Skipping load.")
                continue

            valid_company_ids = self.load_table(table_name, df, valid_company_ids)

        audit_path = self.save_audit_report()

        total_inserted = sum(r["rows_inserted"] for r in self.audit_records)
        total_rejected = sum(r["rows_rejected"] for r in self.audit_records)

        return {
            "success": True,
            "total_inserted": total_inserted,
            "total_rejected": total_rejected,
            "audit_file": str(audit_path),
        }
