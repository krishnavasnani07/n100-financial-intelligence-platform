"""
Daily Background Scheduler.
Orchestrates daily ETL validation, database loading, ratio computation,
and peer analysis updates. Clears/updates cache signals for the dashboard.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config.settings import DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_daily_refresh():
    """
    Executes the full data refresh pipeline.
    """
    logger.info("Starting daily scheduler refresh pipeline...")
    start_time = time.time()

    # 1. Run Data Validation
    logger.info("Step 1: Running Data Validation...")
    from src.validation.validator import DataValidator

    validator = DataValidator()
    validator_summary = validator.run_validation()
    logger.info(
        f"Validation completed. Success: {validator_summary['success']}, Critical failures: {validator_summary['critical_failures']}"
    )

    # 2. SQLite Database Loading
    logger.info("Step 2: Loading Data into SQLite...")
    from src.database.loader import DatabaseLoader

    db_loader = DatabaseLoader()
    load_summary = db_loader.load_all(validator.datasets)
    logger.info(
        f"Database load completed. Total read: {load_summary['total_read']}, Total inserted: {load_summary['total_inserted']}"
    )

    # 3. Calculate Profitability KPIs
    logger.info("Step 3: Calculating Profitability KPIs...")
    import sqlite3

    import pandas as pd

    from src.analytics.ratios import ProfitabilityEngine

    conn = sqlite3.connect(str(DB_PATH))
    query_ratios = """
        SELECT 
            c.id AS company_id,
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
    """
    df_ratios_data = pd.read_sql(query_ratios, conn)
    conn.close()

    all_ratio_results = []
    for idx, row in df_ratios_data.iterrows():
        is_fin = str(row.get("broad_sector")) == "Financials"
        results = ProfitabilityEngine.compute_period_ratios(
            company_id=row["company_id"],
            year=row["year"],
            sales=row["sales"],
            operating_profit=row["operating_profit"],
            net_profit=row["net_profit"],
            equity_capital=row["equity_capital"],
            reserves=row["reserves"],
            borrowings=row["borrowings"],
            total_assets=row["total_assets"],
            reported_opm=row["reported_opm"],
            is_financial=is_fin,
        )
        all_ratio_results.extend(results)
    ProfitabilityEngine.export_ratio_audit_and_summary(all_ratio_results)
    logger.info("Profitability KPIs calculation complete.")

    # 4. Calculate CAGR KPIs
    logger.info("Step 4: Calculating Growth CAGR KPIs...")
    from src.analytics.cagr import CAGREngine

    conn_cagr = sqlite3.connect(str(DB_PATH))
    query_pl = "SELECT company_id, year, sales, net_profit, eps FROM profitandloss"
    df_pl_all = pd.read_sql(query_pl, conn_cagr)
    conn_cagr.close()

    all_cagr_results = []
    for cid in df_pl_all["company_id"].unique():
        df_comp = df_pl_all[df_pl_all["company_id"] == cid]
        cagr_res = CAGREngine.compute_company_cagr(cid, df_comp)
        all_cagr_results.extend(cagr_res)
    CAGREngine.export_growth_reports(all_cagr_results)
    logger.info("Growth CAGR calculation complete.")

    # 5. Calculate Cash Flow KPIs
    logger.info("Step 5: Calculating Cash Flow KPIs...")
    from src.analytics.cashflow_kpis import CashFlowEngine

    conn_cf = sqlite3.connect(str(DB_PATH))
    query_cf = """
        SELECT 
            cf.company_id,
            cf.year,
            cf.operating_activity,
            cf.investing_activity,
            cf.financing_activity,
            pl.sales,
            pl.operating_profit,
            pl.net_profit
        FROM cashflow cf
        LEFT JOIN profitandloss pl ON cf.company_id = pl.company_id AND cf.year = pl.year
        ORDER BY cf.company_id, cf.year
    """
    df_cf_all = pd.read_sql(query_cf, conn_cf)
    conn_cf.close()

    all_cashflow_results = []
    for cid in df_cf_all["company_id"].unique():
        df_comp = df_cf_all[df_cf_all["company_id"] == cid]
        cf_res = CashFlowEngine.compute_company_cashflow_kpis(cid, df_comp)
        all_cashflow_results.extend(cf_res)
    CashFlowEngine.export_cashflow_reports(all_cashflow_results)
    logger.info("Cash Flow KPIs calculation complete.")

    # 6. Populate Financial Ratios Database Table
    logger.info("Step 6: Populating SQLite financial_ratios table...")
    from src.analytics.populate_financial_ratios import \
        populate_ratios_pipeline

    populate_ratios_pipeline(DB_PATH)
    logger.info("financial_ratios table populated.")

    # 7. Run Peer Percentile Ranking Engine
    logger.info("Step 7: Running Peer Percentile Ranking Engine...")
    from src.peer_analysis.comparison import run_peer_analysis

    run_peer_analysis(DB_PATH)
    logger.info("Peer comparison and percentile ranking completed.")

    # 8. Write Cache Invalidation Token
    cache_token_path = BASE_DIR / "data" / "last_update.txt"
    cache_token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_token_path, "w") as f:
        f.write(datetime.now().isoformat())

    runtime = round(time.time() - start_time, 2)
    logger.info(
        f"Daily Scheduler execution completed successfully in {runtime} seconds."
    )


if __name__ == "__main__":
    run_daily_refresh()
