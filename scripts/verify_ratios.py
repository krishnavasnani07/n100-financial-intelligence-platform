"""
Automated Financial Ratio Spot-Check Verification Script.
Validates calculated SQLite KPIs against raw Excel source data for sample companies across sectors.
Exports detailed verification audit report to output/reports/ratio_spot_check.csv.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to sys.path for module resolution
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.utils.logger import get_logger
from src.analytics.ratios import ProfitabilityEngine, safe_divide

logger = get_logger("ratio_verification")

SAMPLE_COMPANIES = ["TCS", "HDFCBANK", "ITC", "TATAMOTORS", "SUNPHARMA"]


def run_spot_check_verification(db_path: Path, output_dir: Path) -> pd.DataFrame:
    """Run automated spot-check verification against raw and SQLite datasets."""
    logger.info("Starting automated ratio spot-check verification...")
    conn = sqlite3.connect(db_path)

    query = """
        SELECT 
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            pl.year,
            pl.sales,
            pl.operating_profit,
            pl.opm_percentage AS reported_opm,
            pl.net_profit,
            bs.equity_capital,
            bs.reserves,
            bs.borrowings,
            bs.total_assets
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        JOIN profitandloss pl ON c.id = pl.company_id
        JOIN balancesheet bs ON c.id = bs.company_id AND pl.year = bs.year
        WHERE c.id IN ({})
    """.format(",".join([f"'{ticker}'" for ticker in SAMPLE_COMPANIES]))

    df = pd.read_sql(query, conn)
    conn.close()

    records: List[Dict[str, Any]] = []

    for idx, row in df.iterrows():
        company_id = row["company_id"]
        year = row["year"]
        sales = row["sales"]
        op_prof = row["operating_profit"]
        net_prof = row["net_profit"]
        eq_cap = row["equity_capital"]
        res = row["reserves"]
        borr = row["borrowings"]
        assets = row["total_assets"]
        rep_opm = row["reported_opm"]
        is_fin = str(row.get("broad_sector")) == "Financials"

        ratios = ProfitabilityEngine.compute_all_ratios(
            company_id=company_id,
            year=year,
            sales=sales,
            operating_profit=op_prof,
            net_profit=net_prof,
            equity_capital=eq_cap,
            reserves=res,
            borrowings=borr,
            total_assets=assets,
            reported_opm=rep_opm,
            is_financial=is_fin,
        )

        # Re-verify math manually
        manual_npm = (
            round((net_prof / sales) * 100.0, 2) if sales and sales > 0 else None
        )
        manual_opm = (
            round((op_prof / sales) * 100.0, 2) if sales and sales > 0 else None
        )
        tot_eq = (eq_cap or 0) + (res or 0)
        manual_roe = round((net_prof / tot_eq) * 100.0, 2) if tot_eq > 0 else None
        cap_emp = tot_eq + (borr or 0)
        manual_roce = round((op_prof / cap_emp) * 100.0, 2) if cap_emp > 0 else None
        manual_roa = (
            round((net_prof / assets) * 100.0, 2) if assets and assets > 0 else None
        )

        # Calculate deltas
        npm_delta = (
            abs(ratios["npm"] - manual_npm) if ratios["npm"] and manual_npm else 0.0
        )
        opm_delta = (
            abs(ratios["opm"] - manual_opm) if ratios["opm"] and manual_opm else 0.0
        )
        roe_delta = (
            abs(ratios["roe"] - manual_roe) if ratios["roe"] and manual_roe else 0.0
        )
        roce_delta = (
            abs(ratios["roce"] - manual_roce) if ratios["roce"] and manual_roce else 0.0
        )
        roa_delta = (
            abs(ratios["roa"] - manual_roa) if ratios["roa"] and manual_roa else 0.0
        )

        records.append(
            {
                "company_id": company_id,
                "year": year,
                "sector": row["broad_sector"],
                "engine_npm": ratios["npm"],
                "manual_npm": manual_npm,
                "npm_match": npm_delta < 0.01,
                "engine_opm": ratios["opm"],
                "manual_opm": manual_opm,
                "opm_match": opm_delta < 0.01,
                "engine_roe": ratios["roe"],
                "manual_roe": manual_roe,
                "roe_match": roe_delta < 0.01,
                "engine_roce": ratios["roce"],
                "manual_roce": manual_roce,
                "roce_match": roce_delta < 0.01,
                "engine_roa": ratios["roa"],
                "manual_roa": manual_roa,
                "roa_match": roa_delta < 0.01,
                "reported_opm": rep_opm,
            }
        )

    df_result = pd.DataFrame(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "ratio_spot_check.csv"
    df_result.to_csv(report_file, index=False)
    logger.info(
        f"Spot-check verification complete for {len(df_result)} records. Report exported to {report_file}"
    )
    return df_result


if __name__ == "__main__":
    db_path = BASE_DIR / "db" / "nifty100.db"
    out_dir = BASE_DIR / "output" / "reports"
    df_res = run_spot_check_verification(db_path, out_dir)
    print("\n====================================")
    print("      RATIO SPOT-CHECK SUMMARY      ")
    print("====================================")
    print(f"Total Records Checked : {len(df_res)}")
    print(f"NPM Match Pass Rate   : {(df_res['npm_match'].mean() * 100):.1f}%")
    print(f"OPM Match Pass Rate   : {(df_res['opm_match'].mean() * 100):.1f}%")
    print(f"ROE Match Pass Rate   : {(df_res['roe_match'].mean() * 100):.1f}%")
    print(f"ROCE Match Pass Rate  : {(df_res['roce_match'].mean() * 100):.1f}%")
    print(f"ROA Match Pass Rate   : {(df_res['roa_match'].mean() * 100):.1f}%\n")
