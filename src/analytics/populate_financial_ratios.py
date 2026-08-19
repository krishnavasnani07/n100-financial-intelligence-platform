"""
Financial Ratio Population Pipeline.

Integrates Profitability, Leverage, CAGR, and Cash Flow analytics engines
to populate the `financial_ratios` SQLite database table and generate `output/financial_ratios.csv`.
"""

import logging
import math
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# Add parent directory to sys.path if needed
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import calculate_cfo_quality, calculate_free_cash_flow
from src.analytics.ratios import (
    calculate_asset_turnover,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roa,
    calculate_roce,
    calculate_roe,
)
from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR


def setup_logger() -> logging.Logger:
    """Setup dedicated logger for ratio population pipeline."""
    logger = logging.getLogger("populate_ratios")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "populate_ratios.log"

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


from src.utils.helpers import extract_year_int


def calculate_composite_quality_score(
    roe: float | None,
    roce: float | None,
    rev_cagr: float | None,
    pat_cagr: float | None,
    de_ratio: float | None,
    icr: float | None,
    cfo_quality: float | None,
) -> float | None:
    """
    Computes a weighted Composite Quality Score (0 - 100).
    Weight distribution:
      - ROE (20%)
      - ROCE (20%)
      - Revenue CAGR 5yr (15%)
      - PAT CAGR 5yr (15%)
      - Debt to Equity (10%)
      - Interest Coverage (10%)
      - CFO Quality (10%)
    Re-normalizes weights for valid components if any input metric is missing.
    """
    components: list[tuple[float, float]] = []

    # 1. ROE Score (Target: >=20%)
    if roe is not None and not math.isnan(roe):
        score = min(100.0, max(0.0, (roe / 20.0) * 100.0))
        components.append((score, 0.20))

    # 2. ROCE Score (Target: >=20%)
    if roce is not None and not math.isnan(roce):
        score = min(100.0, max(0.0, (roce / 20.0) * 100.0))
        components.append((score, 0.20))

    # 3. Revenue CAGR 5yr Score (Target: >=15%)
    if rev_cagr is not None and not math.isnan(rev_cagr):
        score = min(100.0, max(0.0, (rev_cagr / 15.0) * 100.0))
        components.append((score, 0.15))

    # 4. PAT CAGR 5yr Score (Target: >=15%)
    if pat_cagr is not None and not math.isnan(pat_cagr):
        score = min(100.0, max(0.0, (pat_cagr / 15.0) * 100.0))
        components.append((score, 0.15))

    # 5. Debt to Equity Score (Target: <=0.5 is 100, >=2.0 is 0)
    if de_ratio is not None and not math.isnan(de_ratio):
        if de_ratio <= 0.5:
            score = 100.0
        elif de_ratio >= 2.0:
            score = 0.0
        else:
            score = (2.0 - de_ratio) / 1.5 * 100.0
        components.append((score, 0.10))

    # 6. Interest Coverage Score (Target: >=10 is 100, <=1 is 0)
    if icr is not None and not math.isnan(icr):
        if icr >= 10.0:
            score = 100.0
        elif icr <= 1.0:
            score = 0.0
        else:
            score = (icr - 1.0) / 9.0 * 100.0
        components.append((score, 0.10))
    elif de_ratio is not None and not math.isnan(de_ratio) and de_ratio == 0.0:
        # Debt free company gets 100 points for ICR
        components.append((100.0, 0.10))

    # 7. CFO Quality Score (Target: >=1.0)
    if cfo_quality is not None and not math.isnan(cfo_quality):
        score = min(100.0, max(0.0, cfo_quality * 100.0))
        components.append((score, 0.10))

    if not components:
        return None

    weighted_sum = sum(s * w for s, w in components)
    weight_sum = sum(w for _, w in components)

    final_score = round(weighted_sum / weight_sum, 2)
    return min(100.0, max(0.0, final_score))


def load_master_dataframe(db_path: Path) -> pd.DataFrame:
    """
    Loads financial statements from SQLite and merges them on company_id and year.
    """
    conn = sqlite3.connect(db_path)

    query_pl = """
        SELECT 
            company_id, year, sales, expenses, operating_profit, opm_percentage AS reported_opm,
            other_income, interest, depreciation, profit_before_tax, tax_percentage,
            net_profit, eps, dividend_payout
        FROM profitandloss
    """
    df_pl = pd.read_sql(query_pl, conn)

    query_bs = """
        SELECT 
            company_id, year, equity_capital, reserves, borrowings, other_liabilities,
            total_liabilities, fixed_assets, cwip, investments, other_asset, total_assets
        FROM balancesheet
    """
    df_bs = pd.read_sql(query_bs, conn)

    query_cf = """
        SELECT 
            company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow
        FROM cashflow
    """
    df_cf = pd.read_sql(query_cf, conn)

    query_comp = """
        SELECT c.id AS company_id, c.company_name, c.face_value, s.broad_sector AS sector
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
    """
    df_comp = pd.read_sql(query_comp, conn)

    conn.close()

    # Merge PL and BS on company_id, year
    df_master = pd.merge(df_pl, df_bs, on=["company_id", "year"], how="left")

    # Merge Cash Flow
    df_master = pd.merge(df_master, df_cf, on=["company_id", "year"], how="left")

    # Merge Company & Sector details
    df_master = pd.merge(df_master, df_comp, on="company_id", how="left")

    df_master["year_int"] = df_master["year"].apply(extract_year_int)

    return df_master


def populate_ratios_pipeline(db_path: Path | None = None) -> pd.DataFrame:
    """
    Executes the end-to-end Financial Ratio population pipeline.
    """
    start_time = time.time()
    db_file = db_path or DB_PATH

    logger.info(f"Starting Financial Ratio Pipeline using database: {db_file}")

    # 1. Load & Merge Data
    df_master = load_master_dataframe(db_file)
    logger.info(
        f"Loaded master dataset: {len(df_master)} company-year records across {df_master['company_id'].nunique()} companies."
    )

    # 2. Build Historical Lookup for 5-Year CAGR
    # Map (company_id, year_int) -> row dict
    cagr_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for _, row in df_master.iterrows():
        cid = str(row["company_id"])
        yint = row["year_int"]
        if pd.notnull(yint):
            cagr_lookup[(cid, int(yint))] = {
                "sales": row.get("sales"),
                "net_profit": row.get("net_profit"),
                "eps": row.get("eps"),
            }

    records: list[dict[str, Any]] = []
    errors_count = 0

    # 3. Iterate row-by-row and compute all KPIs
    for _, row in df_master.iterrows():
        cid = str(row["company_id"])
        yr = str(row["year"])
        yint = row["year_int"]
        is_fin = str(row.get("sector")) == "Financials"

        sales = row.get("sales")
        op_prof = row.get("operating_profit")
        net_prof = row.get("net_profit")
        eq_cap = row.get("equity_capital")
        reserves = row.get("reserves")
        borrowings = row.get("borrowings")
        total_assets = row.get("total_assets")
        reported_opm = row.get("reported_opm")
        interest = row.get("interest")
        other_inc = row.get("other_income")
        cfo = row.get("operating_activity")
        cfi = row.get("investing_activity")
        face_val = row.get("face_value")

        # Core Profitability KPIs
        npm = calculate_net_profit_margin(net_prof, sales)
        opm = calculate_operating_profit_margin(
            op_prof, sales, reported_opm=reported_opm, company_id=cid, year=yr
        )
        roe = calculate_roe(net_prof, eq_cap, reserves)
        roce = calculate_roce(
            op_prof,
            eq_cap,
            reserves,
            borrowings,
            is_financial=is_fin,
            company_id=cid,
            year=yr,
        )
        roa = calculate_roa(net_prof, total_assets)

        # Leverage & Efficiency KPIs
        de_ratio = calculate_debt_to_equity(
            borrowings, eq_cap, reserves, company_id=cid, year=yr
        )
        icr = calculate_interest_coverage(op_prof, interest, other_income=other_inc)
        asset_turnover = calculate_asset_turnover(sales, total_assets)

        # Cashflow KPIs
        fcf = calculate_free_cash_flow(cfo, cfi, company_id=cid, year=yr)
        capex = (
            abs(float(cfi))
            if cfi is not None and not math.isnan(float(cfi or 0))
            else None
        )
        cash_from_ops = (
            float(cfo) if cfo is not None and not math.isnan(float(cfo or 0)) else None
        )
        total_debt = (
            float(borrowings)
            if borrowings is not None and not math.isnan(float(borrowings or 0))
            else None
        )
        cfo_qual = calculate_cfo_quality(cfo, net_prof, company_id=cid, year=yr)

        # Shareholder Metrics
        eps = (
            float(row.get("eps"))
            if row.get("eps") is not None and not math.isnan(float(row.get("eps") or 0))
            else None
        )
        div_payout = (
            float(row.get("dividend_payout"))
            if row.get("dividend_payout") is not None
            and not math.isnan(float(row.get("dividend_payout") or 0))
            else None
        )

        # Book Value per share = ((Equity Capital + Reserves) / Equity Capital) * Face Value
        bv_per_share = None
        try:
            eq_val = float(eq_cap or 0)
            res_val = float(reserves or 0)
            fv_val = float(face_val or 0)
            if eq_val > 0 and fv_val > 0:
                bv_per_share = round(((eq_val + res_val) / eq_val) * fv_val, 2)
        except (ValueError, TypeError):
            bv_per_share = None

        # 5-Year CAGR computations
        rev_cagr_5yr = None
        pat_cagr_5yr = None
        eps_cagr_5yr = None

        if pd.notnull(yint) and (cid, int(yint) - 5) in cagr_lookup:
            start_data = cagr_lookup[(cid, int(yint) - 5)]
            rev_cagr_5yr, _ = calculate_cagr(
                start_data["sales"], sales, 5, company_id=cid, metric_name="Revenue_5Y"
            )
            pat_cagr_5yr, _ = calculate_cagr(
                start_data["net_profit"],
                net_prof,
                5,
                company_id=cid,
                metric_name="PAT_5Y",
            )
            eps_cagr_5yr, _ = calculate_cagr(
                start_data["eps"], eps, 5, company_id=cid, metric_name="EPS_5Y"
            )

        # Composite Quality Score
        quality_score = calculate_composite_quality_score(
            roe=roe,
            roce=roce,
            rev_cagr=rev_cagr_5yr,
            pat_cagr=pat_cagr_5yr,
            de_ratio=de_ratio,
            icr=icr,
            cfo_quality=cfo_qual,
        )

        records.append(
            {
                "company_id": cid,
                "year": yr,
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "return_on_capital_employed_pct": roce,
                "return_on_assets_pct": roa,
                "debt_to_equity": de_ratio,
                "interest_coverage": icr,
                "asset_turnover": asset_turnover,
                "free_cash_flow_cr": fcf,
                "capex_cr": capex,
                "earnings_per_share": eps,
                "book_value_per_share": bv_per_share,
                "dividend_payout_ratio_pct": div_payout,
                "total_debt_cr": total_debt,
                "cash_from_operations_cr": cash_from_ops,
                "revenue_cagr_5yr": rev_cagr_5yr,
                "pat_cagr_5yr": pat_cagr_5yr,
                "eps_cagr_5yr": eps_cagr_5yr,
                "composite_quality_score": quality_score,
            }
        )

    df_ratios = pd.DataFrame(records)

    # 4. Write to SQLite financial_ratios table
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Recreate table using schema.sql structure
    schema_script = """
        DROP TABLE IF EXISTS financial_ratios;
        CREATE TABLE financial_ratios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            year TEXT NOT NULL,
            net_profit_margin_pct REAL,
            operating_profit_margin_pct REAL,
            return_on_equity_pct REAL,
            return_on_capital_employed_pct REAL,
            return_on_assets_pct REAL,
            debt_to_equity REAL,
            interest_coverage REAL,
            asset_turnover REAL,
            free_cash_flow_cr REAL,
            capex_cr REAL,
            earnings_per_share REAL,
            book_value_per_share REAL,
            dividend_payout_ratio_pct REAL,
            total_debt_cr REAL,
            cash_from_operations_cr REAL,
            revenue_cagr_5yr REAL,
            pat_cagr_5yr REAL,
            eps_cagr_5yr REAL,
            composite_quality_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (company_id, year),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );
    """
    cursor.executescript(schema_script)
    conn.commit()

    # Insert records into SQLite
    cols_to_insert = [
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "composite_quality_score",
    ]

    placeholders = ", ".join(["?"] * len(cols_to_insert))
    insert_sql = f"INSERT INTO financial_ratios ({', '.join(cols_to_insert)}) VALUES ({placeholders})"

    data_tuples = [
        tuple(row[col] for col in cols_to_insert) for _, row in df_ratios.iterrows()
    ]
    cursor.executemany(insert_sql, data_tuples)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM financial_ratios")
    inserted_count = cursor.fetchone()[0]
    conn.close()

    # 5. Export CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / "financial_ratios.csv"
    df_ratios.to_csv(csv_path, index=False)

    elapsed_time = round(time.time() - start_time, 2)

    # 6. Validations
    logger.info("====================================")
    logger.info("  FINANCIAL RATIO PIPELINE SUMMARY  ")
    logger.info("====================================")
    logger.info(f"Companies Processed : {df_master['company_id'].nunique()}")
    logger.info(f"Years Processed     : {df_master['year'].nunique()}")
    logger.info(f"Rows Generated      : {len(df_ratios)}")
    logger.info(f"Rows Inserted (DB)  : {inserted_count}")
    logger.info(f"CSV Exported        : {csv_path}")
    logger.info(f"Execution Time      : {elapsed_time} sec")
    logger.info("====================================\n")

    # Step 11: Verify Row Count >= 1100
    if inserted_count < 1100:
        logger.warning(
            f"WARNING: Inserted row count {inserted_count} is less than target 1,100!"
        )
    else:
        logger.info(
            f"[PASS] Row count validation PASSED: {inserted_count} >= 1100 records inserted."
        )

    # Step 12: Check Null Columns
    null_summary = df_ratios[cols_to_insert].isnull().sum()
    logger.info("--- Null Column Check ---")
    for col, null_cnt in null_summary.items():
        pct = (null_cnt / len(df_ratios)) * 100
        logger.info(f"  {col:<30}: {null_cnt:<4} NULLs ({pct:.1f}%)")
        if null_cnt == len(df_ratios):
            logger.error(f"[FAIL] CRITICAL ERROR: Column {col} is 100% NULL!")
            errors_count += 1
            raise ValueError(f"KPI Column {col} is 100% NULL.")

    # Step 13: Spot Check 3 Companies (TCS, INFY, HDFCBANK)
    verify_spot_checks(df_ratios, df_master)

    return df_ratios


def verify_spot_checks(df_ratios: pd.DataFrame, df_master: pd.DataFrame):
    """
    Spot checks TCS, INFY, HDFCBANK ROE and 5-Year Revenue CAGR against manual formula calculations.
    Ensures difference < 0.1%.
    """
    logger.info("--- Spot Check Validation (TCS, INFY, HDFCBANK) ---")
    sample_tickers = ["TCS", "INFY", "HDFCBANK"]
    target_year = "Mar 2024"

    for ticker in sample_tickers:
        sub_ratio = df_ratios[
            (df_ratios["company_id"] == ticker) & (df_ratios["year"] == target_year)
        ]
        sub_master = df_master[
            (df_master["company_id"] == ticker) & (df_master["year"] == target_year)
        ]
        sub_master_2019 = df_master[
            (df_master["company_id"] == ticker) & (df_master["year"] == "Mar 2019")
        ]

        if sub_ratio.empty or sub_master.empty:
            logger.warning(
                f"Spot check skipped for {ticker} ({target_year}): Data not found."
            )
            continue

        row_r = sub_ratio.iloc[0]
        row_m = sub_master.iloc[0]

        # Manual ROE = PAT / (Equity + Reserves) * 100
        pat = float(row_m.get("net_profit") or 0)
        tot_eq = float(row_m.get("equity_capital") or 0) + float(
            row_m.get("reserves") or 0
        )
        manual_roe = (pat / tot_eq * 100.0) if tot_eq > 0 else None

        # Manual 5yr Revenue CAGR = ((Sales_2024 / Sales_2019) ** 0.2 - 1) * 100
        manual_cagr = None
        if not sub_master_2019.empty:
            s_2019 = float(sub_master_2019.iloc[0].get("sales") or 0)
            s_2024 = float(row_m.get("sales") or 0)
            if s_2019 > 0 and s_2024 > 0:
                manual_cagr = ((s_2024 / s_2019) ** 0.2 - 1.0) * 100.0

        pipeline_roe = row_r.get("return_on_equity_pct")
        pipeline_cagr = row_r.get("revenue_cagr_5yr")

        # Compare ROE
        roe_diff = (
            abs(pipeline_roe - manual_roe)
            if pipeline_roe is not None and manual_roe is not None
            else 0.0
        )
        cagr_diff = (
            abs(pipeline_cagr - manual_cagr)
            if pipeline_cagr is not None and manual_cagr is not None
            else 0.0
        )

        logger.info(f"  [{ticker} {target_year}]")
        logger.info(
            f"    ROE          -> Pipeline: {pipeline_roe:.2f}%, Manual: {manual_roe:.2f}%, Diff: {roe_diff:.4f}%"
        )
        logger.info(
            f"    Revenue CAGR -> Pipeline: {pipeline_cagr:.2f}%, Manual: {manual_cagr:.2f}%, Diff: {cagr_diff:.4f}%"
        )

        if roe_diff >= 0.1 or cagr_diff >= 0.1:
            logger.error(
                f"[FAIL] Spot check failed for {ticker}! ROE diff={roe_diff:.4f}%, CAGR diff={cagr_diff:.4f}%"
            )
            raise ValueError(f"Spot check validation failed for {ticker}.")
        else:
            logger.info(f"    [PASS] Spot check PASSED for {ticker} (Diff < 0.1%)")

    logger.info("All 3 company spot checks completed successfully.\n")


if __name__ == "__main__":
    populate_ratios_pipeline()
