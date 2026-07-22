from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.analytics.ratio_validation import build_ratio_mismatch_entries, write_ratio_edge_case_log


def _load_companies_source(path: Path) -> pd.DataFrame:
    companies_raw = pd.read_excel(path, header=None)
    if companies_raw.shape[0] >= 2:
        companies_df = companies_raw.iloc[1:].copy()
        companies_df.columns = [
            "company_id",
            "company_logo",
            "company_name",
            "chart_link",
            "about_company",
            "website",
            "nse_profile",
            "bse_profile",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage",
        ]
    else:
        companies_df = pd.read_excel(path)
        if "id" in companies_df.columns:
            companies_df = companies_df.rename(columns={"id": "company_id"})

    companies_df = companies_df[["company_id", "roce_percentage"]].copy()
    companies_df["company_id"] = companies_df["company_id"].astype(str).str.strip().str.upper()
    companies_df["roce_percentage"] = pd.to_numeric(companies_df["roce_percentage"], errors="coerce")
    return companies_df


def _extract_year(value: object) -> int | None:
    if value is None:
        return None
    match = re.search(r"(19\d{2}|20\d{2})", str(value))
    return int(match.group(1)) if match else None


def _load_latest_computed_roce(db_path: Path) -> pd.DataFrame:
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        computed_df = pd.read_sql_query(
            "SELECT company_id, year, return_on_capital_employed_pct AS computed_value FROM financial_ratios",
            conn,
        )
        conn.close()
        computed_df = computed_df.copy()
        computed_df["company_id"] = computed_df["company_id"].astype(str).str.strip().str.upper()
        computed_df["year_sort"] = computed_df["year"].apply(_extract_year)
        computed_df = computed_df.sort_values(["company_id", "year_sort"], ascending=[True, False], na_position="last")
        computed_df = computed_df.drop_duplicates(subset=["company_id"], keep="first")
        return computed_df[["company_id", "computed_value"]]

    financial_ratios_path = BASE_DIR / "data" / "raw" / "financial_ratios.xlsx"
    financial_ratios_df = pd.read_excel(financial_ratios_path)
    if "company_id" not in financial_ratios_df.columns:
        financial_ratios_df = financial_ratios_df.rename(columns={"id": "company_id"})
    computed_df = financial_ratios_df[["company_id", "return_on_capital_employed_pct"]].copy()
    computed_df.columns = ["company_id", "computed_value"]
    computed_df["company_id"] = computed_df["company_id"].astype(str).str.strip().str.upper()
    computed_df["computed_value"] = pd.to_numeric(computed_df["computed_value"], errors="coerce")
    return computed_df


def main() -> None:
    companies_path = BASE_DIR / "data" / "raw" / "companies.xlsx"
    db_path = BASE_DIR / "db" / "nifty100.db"

    companies_df = _load_companies_source(companies_path)
    computed_df = _load_latest_computed_roce(db_path)

    mis_matches = build_ratio_mismatch_entries(
        computed_df,
        companies_df.rename(columns={"roce_percentage": "source"}),
        ratio_name="ROCE",
        computed_column="computed_value",
        source_column="source",
    )

    if mis_matches:
        output_path = write_ratio_edge_case_log(mis_matches, output_path=BASE_DIR / "output" / "ratio_edge_cases.log")
        print(f"Wrote {len(mis_matches)} ROCE mismatches to {output_path}")
    else:
        print("No ROCE mismatches found")


if __name__ == "__main__":
    main()
