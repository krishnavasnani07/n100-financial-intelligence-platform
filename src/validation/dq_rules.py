import re
from typing import Dict

import pandas as pd

from src.config import validation_config
from src.etl.normalizer import normalize_ticker, normalize_year
from src.utils.logger import get_logger
from src.validation.report import ValidationFailure, ValidationReport

logger = get_logger(__name__)

# URL regex pattern
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def validate_dq01_company_pk(df_companies: pd.DataFrame, report: ValidationReport):
    """
    DQ-01: Company PK uniqueness (companies.id must be unique)
    Severity: CRITICAL
    """
    logger.info("Executing DQ-01 (Company PK uniqueness)...")
    if df_companies is None or df_companies.empty:
        report.register_check("DQ-01", 0)
        return

    report.register_check("DQ-01", len(df_companies))

    # Check for duplicates in companies.id
    dups = df_companies[df_companies.duplicated(subset=["id"], keep=False)]
    for _, row in dups.iterrows():
        report.add_failure(
            ValidationFailure(
                rule_id="DQ-01",
                severity="CRITICAL",
                table="companies",
                company_id=str(row["id"]),
                year="N/A",
                field="id",
                raw_value=row["id"],
                issue=f"Duplicate primary key 'id' in companies table: {row['id']}",
            )
        )


def validate_dq02_no_duplicate_company_year(
    dfs: Dict[str, pd.DataFrame], report: ValidationReport
):
    """
    DQ-02: No duplicate (company_id, year) in Profit & Loss, Balance Sheet, Cash Flow
    Severity: CRITICAL
    """
    logger.info("Executing DQ-02 (No duplicate company_id, year)...")
    target_tables = ["profitandloss", "balancesheet", "cashflow"]

    for table_name in target_tables:
        df = dfs.get(table_name)
        if df is None or df.empty:
            continue

        # Ensure required columns are present
        if "company_id" not in df.columns or "year" not in df.columns:
            logger.warning(
                f"Table {table_name} missing 'company_id' or 'year' column for DQ-02"
            )
            continue

        report.register_check("DQ-02", len(df))

        # Check duplicates
        dups = df[df.duplicated(subset=["company_id", "year"], keep=False)]
        for _, row in dups.iterrows():
            report.add_failure(
                ValidationFailure(
                    rule_id="DQ-02",
                    severity="CRITICAL",
                    table=table_name,
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="company_id,year",
                    raw_value=f"({row['company_id']}, {row['year']})",
                    issue=f"Duplicate (company_id, year) combination in table {table_name}",
                )
            )


def validate_dq03_foreign_keys(dfs: Dict[str, pd.DataFrame], report: ValidationReport):
    """
    DQ-03: Foreign Key Integrity (Every company_id must exist inside companies.id)
    Severity: CRITICAL
    """
    logger.info("Executing DQ-03 (Foreign Key Integrity)...")
    df_companies = dfs.get("companies")
    if df_companies is None or df_companies.empty:
        logger.error(
            "Companies table missing or empty. Cannot check foreign key integrity."
        )
        return

    valid_company_ids = set(df_companies["id"].dropna().astype(str).str.strip())

    for table_name, df in dfs.items():
        if table_name == "companies" or df is None or df.empty:
            continue

        if "company_id" not in df.columns:
            continue

        report.register_check("DQ-03", len(df))

        # Check invalid FKs
        for idx, row in df.iterrows():
            comp_id = str(row["company_id"]).strip()
            if comp_id not in valid_company_ids:
                # Get year if present
                year = str(row.get("year", row.get("Year", "N/A")))
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-03",
                        severity="CRITICAL",
                        table=table_name,
                        company_id=comp_id,
                        year=year,
                        field="company_id",
                        raw_value=row["company_id"],
                        issue=f"Foreign Key violation: company_id '{comp_id}' in table {table_name} does not exist in companies.id",
                    )
                )


def validate_dq04_balancesheet_balance(df_bs: pd.DataFrame, report: ValidationReport):
    """
    DQ-04: Balance Sheet balance (total_assets == total_liabilities)
    Severity: WARNING
    """
    logger.info("Executing DQ-04 (Balance Sheet balance)...")
    if df_bs is None or df_bs.empty:
        return

    required_cols = ["total_assets", "total_liabilities", "company_id", "year"]
    if not all(col in df_bs.columns for col in required_cols):
        logger.warning("Balance sheet table missing required columns for DQ-04")
        return

    report.register_check("DQ-04", len(df_bs))

    for idx, row in df_bs.iterrows():
        ta = row["total_assets"]
        tl = row["total_liabilities"]

        if pd.isna(ta) or pd.isna(tl):
            report.add_failure(
                ValidationFailure(
                    rule_id="DQ-04",
                    severity="WARNING",
                    table="balancesheet",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="total_assets,total_liabilities",
                    raw_value=f"total_assets={ta}, total_liabilities={tl}",
                    issue="Null total_assets or total_liabilities in balance sheet",
                )
            )
            continue

        try:
            diff = abs(float(ta) - float(tl))
            if diff > validation_config.BALANCE_TOLERANCE:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-04",
                        severity="WARNING",
                        table="balancesheet",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="total_assets,total_liabilities",
                        raw_value=f"total_assets={ta}, total_liabilities={tl}",
                        issue=f"Balance sheet does not balance: diff = {diff} (tolerance = {validation_config.BALANCE_TOLERANCE})",
                    )
                )
        except (ValueError, TypeError) as e:
            report.add_failure(
                ValidationFailure(
                    rule_id="DQ-04",
                    severity="WARNING",
                    table="balancesheet",
                    company_id=str(row["company_id"]),
                    year=str(row["year"]),
                    field="total_assets,total_liabilities",
                    raw_value=f"total_assets={ta}, total_liabilities={tl}",
                    issue=f"Data type conversion error during balance sheet check: {e}",
                )
            )


def validate_dq05_opm_crosscheck(df_pl: pd.DataFrame, report: ValidationReport):
    """
    DQ-05: Operating Profit Margin cross-check (opm_percentage should be close to operating_profit / sales * 100)
    Severity: WARNING
    """
    logger.info("Executing DQ-05 (OPM cross-check)...")
    if df_pl is None or df_pl.empty:
        return

    required_cols = [
        "sales",
        "operating_profit",
        "opm_percentage",
        "company_id",
        "year",
    ]
    if not all(col in df_pl.columns for col in required_cols):
        logger.warning("Profit & Loss table missing required columns for DQ-05")
        return

    report.register_check("DQ-05", len(df_pl))

    for idx, row in df_pl.iterrows():
        sales = row["sales"]
        op = row["operating_profit"]
        opm = row["opm_percentage"]

        if pd.isna(sales) or pd.isna(op) or pd.isna(opm):
            continue

        try:
            sales_val = float(sales)
            op_val = float(op)
            opm_val = float(opm)

            if sales_val > 0:
                expected_opm = (op_val / sales_val) * 100
                diff = abs(expected_opm - opm_val)
                if diff > validation_config.OPM_TOLERANCE:
                    report.add_failure(
                        ValidationFailure(
                            rule_id="DQ-05",
                            severity="WARNING",
                            table="profitandloss",
                            company_id=str(row["company_id"]),
                            year=str(row["year"]),
                            field="opm_percentage",
                            raw_value=f"opm_percentage={opm}, sales={sales}, operating_profit={op}",
                            issue=f"OPM mismatch: reported {opm_val}%, calculated {expected_opm:.2f}% (diff={diff:.2f}%, tolerance={validation_config.OPM_TOLERANCE}%)",
                        )
                    )
        except (ValueError, TypeError):
            continue


def validate_dq06_positive_sales(df_pl: pd.DataFrame, report: ValidationReport):
    """
    DQ-06: Positive Sales (sales > 0 in profitandloss)
    Severity: WARNING
    """
    logger.info("Executing DQ-06 (Positive Sales)...")
    if df_pl is None or df_pl.empty:
        return

    if "sales" not in df_pl.columns:
        logger.warning("Profit & Loss table missing 'sales' column for DQ-06")
        return

    report.register_check("DQ-06", len(df_pl))

    for idx, row in df_pl.iterrows():
        sales = row["sales"]
        if pd.isna(sales):
            continue

        try:
            sales_val = float(sales)
            if sales_val <= 0:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-06",
                        severity="WARNING",
                        table="profitandloss",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="sales",
                        raw_value=sales,
                        issue=f"Non-positive sales: {sales_val}",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq07_year_format(dfs: Dict[str, pd.DataFrame], report: ValidationReport):
    """
    DQ-07: Year format (Must match YYYY-MM after normalization)
    Severity: CRITICAL
    """
    logger.info("Executing DQ-07 (Year format check)...")

    for table_name, df in dfs.items():
        if df is None or df.empty:
            continue

        # Identify year column (case insensitive or Year/year)
        year_col = None
        for col in df.columns:
            if col.lower() == "year":
                year_col = col
                break

        if not year_col:
            continue

        report.register_check("DQ-07", len(df))

        for idx, row in df.iterrows():
            raw_y = row[year_col]
            if pd.isna(raw_y):
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-07",
                        severity="CRITICAL",
                        table=table_name,
                        company_id=str(row.get("company_id", row.get("id", "N/A"))),
                        year="N/A",
                        field=year_col,
                        raw_value=raw_y,
                        issue=f"Null year value in {table_name}",
                    )
                )
                continue

            norm_y = normalize_year(raw_y)
            if not norm_y:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-07",
                        severity="CRITICAL",
                        table=table_name,
                        company_id=str(row.get("company_id", row.get("id", "N/A"))),
                        year=str(raw_y),
                        field=year_col,
                        raw_value=raw_y,
                        issue=f"Year normalization failed for '{raw_y}' (does not match YYYY-MM)",
                    )
                )


def validate_dq08_ticker_format(dfs: Dict[str, pd.DataFrame], report: ValidationReport):
    """
    DQ-08: Ticker format (Must satisfy uppercase, stripped, length between 2 and 12, alphanumeric/hyphen/ampersand)
    Severity: CRITICAL
    """
    logger.info("Executing DQ-08 (Ticker format check)...")

    for table_name, df in dfs.items():
        if df is None or df.empty:
            continue

        # Target ticker columns: 'id' for companies, 'company_id' for others
        ticker_col = "id" if table_name == "companies" else "company_id"
        if ticker_col not in df.columns:
            continue

        report.register_check("DQ-08", len(df))

        for idx, row in df.iterrows():
            ticker = row[ticker_col]
            if pd.isna(ticker):
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-08",
                        severity="CRITICAL",
                        table=table_name,
                        company_id=str(row.get("company_id", row.get("id", "N/A"))),
                        year=str(row.get("year", row.get("Year", "N/A"))),
                        field=ticker_col,
                        raw_value=ticker,
                        issue=f"Null ticker value in {table_name}",
                    )
                )
                continue

            norm_ticker = normalize_ticker(ticker)
            # A ticker fails if it cannot be normalized or if normalization changes the format (meaning it wasn't valid stripped/uppercase/length in the first place)
            if not norm_ticker or norm_ticker != str(ticker):
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-08",
                        severity="CRITICAL",
                        table=table_name,
                        company_id=str(row.get("company_id", row.get("id", "N/A"))),
                        year=str(row.get("year", row.get("Year", "N/A"))),
                        field=ticker_col,
                        raw_value=ticker,
                        issue=f"Ticker format violation: '{ticker}' (expected uppercase, stripped, 2-12 chars, valid symbols)",
                    )
                )


def validate_dq09_net_cash_flow(df_cf: pd.DataFrame, report: ValidationReport):
    """
    DQ-09: Net Cash Flow (net_cash_flow == operating_activity + investing_activity + financing_activity)
    Severity: WARNING
    """
    logger.info("Executing DQ-09 (Net Cash Flow check)...")
    if df_cf is None or df_cf.empty:
        return

    required_cols = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
        "company_id",
        "year",
    ]
    if not all(col in df_cf.columns for col in required_cols):
        logger.warning("Cash Flow table missing required columns for DQ-09")
        return

    report.register_check("DQ-09", len(df_cf))

    for idx, row in df_cf.iterrows():
        op = row["operating_activity"]
        inv = row["investing_activity"]
        fin = row["financing_activity"]
        ncf = row["net_cash_flow"]

        if pd.isna(op) or pd.isna(inv) or pd.isna(fin) or pd.isna(ncf):
            continue

        try:
            op_val = float(op)
            inv_val = float(inv)
            fin_val = float(fin)
            ncf_val = float(ncf)

            expected_ncf = op_val + inv_val + fin_val
            diff = abs(expected_ncf - ncf_val)
            if diff > validation_config.BALANCE_TOLERANCE:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-09",
                        severity="WARNING",
                        table="cashflow",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="net_cash_flow",
                        raw_value=ncf,
                        issue=f"Net cash flow mismatch: reported {ncf_val}, calculated {expected_ncf} (diff={diff}, tolerance={validation_config.BALANCE_TOLERANCE})",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq10_fixed_assets(df_bs: pd.DataFrame, report: ValidationReport):
    """
    DQ-10: Fixed Assets (fixed_assets >= 0 and fixed_assets <= total_assets)
    Severity: WARNING
    """
    logger.info("Executing DQ-10 (Fixed Assets check)...")
    if df_bs is None or df_bs.empty:
        return

    required_cols = ["fixed_assets", "total_assets", "company_id", "year"]
    if not all(col in df_bs.columns for col in required_cols):
        logger.warning("Balance sheet table missing required columns for DQ-10")
        return

    report.register_check("DQ-10", len(df_bs))

    for idx, row in df_bs.iterrows():
        fa = row["fixed_assets"]
        ta = row["total_assets"]

        if pd.isna(fa) or pd.isna(ta):
            continue

        try:
            fa_val = float(fa)
            ta_val = float(ta)

            if fa_val < 0:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-10",
                        severity="WARNING",
                        table="balancesheet",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="fixed_assets",
                        raw_value=fa,
                        issue=f"Negative fixed assets: {fa_val}",
                    )
                )
            if fa_val > ta_val:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-10",
                        severity="WARNING",
                        table="balancesheet",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="fixed_assets",
                        raw_value=f"fixed_assets={fa}, total_assets={ta}",
                        issue="Fixed assets exceed total assets",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq11_tax_rate(df_pl: pd.DataFrame, report: ValidationReport):
    """
    DQ-11: Tax Rate (0 <= tax_percentage <= 100)
    Severity: WARNING
    """
    logger.info("Executing DQ-11 (Tax Rate check)...")
    if df_pl is None or df_pl.empty:
        return

    required_cols = ["tax_percentage", "company_id", "year"]
    if not all(col in df_pl.columns for col in required_cols):
        logger.warning("Profit & Loss table missing required columns for DQ-11")
        return

    report.register_check("DQ-11", len(df_pl))

    for idx, row in df_pl.iterrows():
        tax = row["tax_percentage"]
        if pd.isna(tax):
            continue

        try:
            tax_val = float(tax)
            if (
                tax_val < validation_config.MIN_TAX_PERCENTAGE
                or tax_val > validation_config.MAX_TAX_PERCENTAGE
            ):
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-11",
                        severity="WARNING",
                        table="profitandloss",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="tax_percentage",
                        raw_value=tax,
                        issue=f"Tax rate outside range [{validation_config.MIN_TAX_PERCENTAGE}, {validation_config.MAX_TAX_PERCENTAGE}]: {tax_val}%",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq12_dividend_payout(df_pl: pd.DataFrame, report: ValidationReport):
    """
    DQ-12: Dividend Payout (0 <= dividend_payout <= MAX_DIVIDEND_PAYOUT)
    Severity: WARNING
    """
    logger.info("Executing DQ-12 (Dividend Payout check)...")
    if df_pl is None or df_pl.empty:
        return

    required_cols = ["dividend_payout", "company_id", "year"]
    if not all(col in df_pl.columns for col in required_cols):
        logger.warning("Profit & Loss table missing required columns for DQ-12")
        return

    report.register_check("DQ-12", len(df_pl))

    for idx, row in df_pl.iterrows():
        div = row["dividend_payout"]
        if pd.isna(div):
            continue

        try:
            div_val = float(div)
            if div_val < 0 or div_val > validation_config.MAX_DIVIDEND_PAYOUT:
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-12",
                        severity="WARNING",
                        table="profitandloss",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="dividend_payout",
                        raw_value=div,
                        issue=f"Dividend payout percentage outside range [0, {validation_config.MAX_DIVIDEND_PAYOUT}]: {div_val}%",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq13_url_validation(
    dfs: Dict[str, pd.DataFrame], report: ValidationReport
):
    """
    DQ-13: URL Validation (Validate format of URLs in companies and documents tables)
    Severity: WARNING
    """
    logger.info("Executing DQ-13 (URL Validation)...")

    # 1. Check companies table
    df_c = dfs.get("companies")
    if df_c is not None and not df_c.empty:
        url_cols = [
            "company_logo",
            "chart_link",
            "website",
            "nse_profile",
            "bse_profile",
        ]
        for col in url_cols:
            if col not in df_c.columns:
                continue

            # Record number of checks
            report.register_check("DQ-13", len(df_c))

            for idx, row in df_c.iterrows():
                val = row[col]
                if pd.isna(val) or not str(val).strip():
                    continue

                # Check for literal "Null" string or invalid URL format
                val_str = str(val).strip()
                if val_str.lower() in ("null", "nan", "none") or not URL_PATTERN.match(
                    val_str
                ):
                    report.add_failure(
                        ValidationFailure(
                            rule_id="DQ-13",
                            severity="WARNING",
                            table="companies",
                            company_id=str(row["id"]),
                            year="N/A",
                            field=col,
                            raw_value=val,
                            issue=f"Invalid URL format: '{val}'",
                        )
                    )

    # 2. Check documents table
    df_d = dfs.get("documents")
    if df_d is not None and not df_d.empty:
        col = "Annual_Report"
        if col in df_d.columns:
            report.register_check("DQ-13", len(df_d))
            for idx, row in df_d.iterrows():
                val = row[col]
                if pd.isna(val) or not str(val).strip():
                    continue

                val_str = str(val).strip()
                if val_str.lower() in ("null", "nan", "none") or not URL_PATTERN.match(
                    val_str
                ):
                    report.add_failure(
                        ValidationFailure(
                            rule_id="DQ-13",
                            severity="WARNING",
                            table="documents",
                            company_id=str(row.get("company_id", "N/A")),
                            year=str(row.get("Year", "N/A")),
                            field=col,
                            raw_value=val,
                            issue=f"Invalid Annual_Report URL: '{val}'",
                        )
                    )


def validate_dq14_eps_sign(df_pl: pd.DataFrame, report: ValidationReport):
    """
    DQ-14: EPS Sign (EPS and net_profit signs should match)
    Severity: WARNING
    """
    logger.info("Executing DQ-14 (EPS Sign match)...")
    if df_pl is None or df_pl.empty:
        return

    required_cols = ["net_profit", "eps", "company_id", "year"]
    if not all(col in df_pl.columns for col in required_cols):
        logger.warning("Profit & Loss table missing required columns for DQ-14")
        return

    report.register_check("DQ-14", len(df_pl))

    for idx, row in df_pl.iterrows():
        np_val = row["net_profit"]
        eps_val = row["eps"]

        if pd.isna(np_val) or pd.isna(eps_val):
            continue

        try:
            np_f = float(np_val)
            eps_f = float(eps_val)

            # Violate if signs differ (i.e. one is strictly positive, the other strictly negative)
            if (np_f > 0 and eps_f < 0) or (np_f < 0 and eps_f > 0):
                report.add_failure(
                    ValidationFailure(
                        rule_id="DQ-14",
                        severity="WARNING",
                        table="profitandloss",
                        company_id=str(row["company_id"]),
                        year=str(row["year"]),
                        field="net_profit,eps",
                        raw_value=f"net_profit={np_val}, eps={eps_val}",
                        issue="Sign mismatch between net_profit and eps",
                    )
                )
        except (ValueError, TypeError):
            continue


def validate_dq15_balancesheet_info(df_bs: pd.DataFrame, report: ValidationReport):
    """
    DQ-15: Balance Sheet informational check (Subcategories should sum to total_assets and total_liabilities)
    Severity: WARNING
    """
    logger.info("Executing DQ-15 (Balance Sheet informational sums)...")
    if df_bs is None or df_bs.empty:
        return

    # Check liabilities components: equity_capital, reserves, borrowings, other_liabilities vs total_liabilities
    liab_cols = [
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "company_id",
        "year",
    ]
    asset_cols = [
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
        "company_id",
        "year",
    ]

    if all(col in df_bs.columns for col in liab_cols):
        report.register_check("DQ-15", len(df_bs))
        for idx, row in df_bs.iterrows():
            try:
                eq = float(row.get("equity_capital", 0))
                res = float(row.get("reserves", 0))
                bor = float(row.get("borrowings", 0))
                oth_l = float(row.get("other_liabilities", 0))
                tl = float(row.get("total_liabilities", 0))

                calculated_liab = eq + res + bor + oth_l
                if abs(calculated_liab - tl) > validation_config.BALANCE_TOLERANCE:
                    report.add_failure(
                        ValidationFailure(
                            rule_id="DQ-15",
                            severity="WARNING",
                            table="balancesheet",
                            company_id=str(row["company_id"]),
                            year=str(row["year"]),
                            field="equity_capital,reserves,borrowings,other_liabilities",
                            raw_value=f"eq={eq}, res={res}, bor={bor}, oth_l={oth_l}, tl={tl}",
                            issue=f"Liabilities sum mismatch: calculated {calculated_liab}, reported {tl} (tolerance={validation_config.BALANCE_TOLERANCE})",
                        )
                    )
            except (ValueError, TypeError):
                continue

    if all(col in df_bs.columns for col in asset_cols):
        report.register_check("DQ-15", len(df_bs))
        for idx, row in df_bs.iterrows():
            try:
                fa = float(row.get("fixed_assets", 0))
                cwip = float(row.get("cwip", 0))
                inv = float(row.get("investments", 0))
                oth_a = float(row.get("other_asset", 0))
                ta = float(row.get("total_assets", 0))

                calculated_assets = fa + cwip + inv + oth_a
                if abs(calculated_assets - ta) > validation_config.BALANCE_TOLERANCE:
                    report.add_failure(
                        ValidationFailure(
                            rule_id="DQ-15",
                            severity="WARNING",
                            table="balancesheet",
                            company_id=str(row["company_id"]),
                            year=str(row["year"]),
                            field="fixed_assets,cwip,investments,other_asset",
                            raw_value=f"fa={fa}, cwip={cwip}, inv={inv}, oth_a={oth_a}, ta={ta}",
                            issue=f"Assets sum mismatch: calculated {calculated_assets}, reported {ta} (tolerance={validation_config.BALANCE_TOLERANCE})",
                        )
                    )
            except (ValueError, TypeError):
                continue


def validate_dq16_coverage(dfs: Dict[str, pd.DataFrame], report: ValidationReport):
    """
    DQ-16: Coverage (Each company should have >= MIN_HISTORY_YEARS of data in profitandloss)
    Severity: WARNING
    """
    logger.info("Executing DQ-16 (Company years coverage)...")
    df_companies = dfs.get("companies")
    df_pl = dfs.get("profitandloss")

    if df_companies is None or df_companies.empty or df_pl is None or df_pl.empty:
        logger.warning(
            "Companies or Profit & Loss table missing for DQ-16 coverage check"
        )
        return

    company_ids = df_companies["id"].dropna().astype(str).str.strip().unique()
    report.register_check("DQ-16", len(company_ids))

    # Calculate years per company
    pl_years = df_pl.groupby("company_id")["year"].nunique().to_dict()

    for comp_id in company_ids:
        years_count = pl_years.get(comp_id, 0)
        if years_count < validation_config.MIN_HISTORY_YEARS:
            report.add_failure(
                ValidationFailure(
                    rule_id="DQ-16",
                    severity="WARNING",
                    table="profitandloss",
                    company_id=comp_id,
                    year="N/A",
                    field="year",
                    raw_value=years_count,
                    issue=f"Insufficient historical coverage: company has only {years_count} years of P&L records (expected >= {validation_config.MIN_HISTORY_YEARS})",
                )
            )


from src.validation.report import Rule

RULE_REGISTRY: Dict[str, Rule] = {
    "DQ-01": Rule(
        "DQ-01",
        "Company PK Uniqueness",
        "CRITICAL",
        "Verify company IDs in master table are unique",
    ),
    "DQ-02": Rule(
        "DQ-02",
        "No Duplicate Company-Year",
        "CRITICAL",
        "Ensure no duplicate company_id and year combinations",
    ),
    "DQ-03": Rule(
        "DQ-03",
        "Foreign Key Integrity",
        "CRITICAL",
        "Validate company_id foreign key references",
    ),
    "DQ-04": Rule(
        "DQ-04",
        "Balance Sheet Balance",
        "WARNING",
        "Validate total_assets equals total_liabilities",
    ),
    "DQ-05": Rule(
        "DQ-05",
        "OPM Cross-Check",
        "WARNING",
        "Validate operating profit margin matches calculation",
    ),
    "DQ-06": Rule(
        "DQ-06", "Positive Sales", "WARNING", "Ensure sales in P&L are positive"
    ),
    "DQ-07": Rule(
        "DQ-07",
        "Year Format",
        "CRITICAL",
        "Verify year matches YYYY-MM standard format",
    ),
    "DQ-08": Rule(
        "DQ-08",
        "Ticker Format",
        "CRITICAL",
        "Ensure company ticker meets format and length rules",
    ),
    "DQ-09": Rule(
        "DQ-09",
        "Net Cash Flow Check",
        "WARNING",
        "Validate net cash flow matches component sum",
    ),
    "DQ-10": Rule(
        "DQ-10",
        "Fixed Assets Range",
        "WARNING",
        "Ensure fixed assets are non-negative and <= total assets",
    ),
    "DQ-11": Rule(
        "DQ-11",
        "Tax Rate Bounds",
        "WARNING",
        "Validate tax percentage is within [0, 100]",
    ),
    "DQ-12": Rule(
        "DQ-12", "Dividend Payout Bounds", "WARNING", "Validate dividend payout range"
    ),
    "DQ-13": Rule(
        "DQ-13",
        "URL Format Validation",
        "WARNING",
        "Verify company website and document URLs",
    ),
    "DQ-14": Rule(
        "DQ-14", "EPS Sign Alignment", "WARNING", "Match signs of EPS and Net Profit"
    ),
    "DQ-15": Rule(
        "DQ-15",
        "Balance Sheet Sum Check",
        "WARNING",
        "Verify asset and liability component sums",
    ),
    "DQ-16": Rule(
        "DQ-16",
        "Historical Coverage",
        "WARNING",
        "Ensure minimum required years of P&L history",
    ),
}

# Standalone check aliases for modular execution
check_dq01 = validate_dq01_company_pk
check_dq02 = validate_dq02_no_duplicate_company_year
check_dq03 = validate_dq03_foreign_keys
check_dq04 = validate_dq04_balancesheet_balance
check_dq05 = validate_dq05_opm_crosscheck
check_dq06 = validate_dq06_positive_sales
check_dq07 = validate_dq07_year_format
check_dq08 = validate_dq08_ticker_format
check_dq09 = validate_dq09_net_cash_flow
check_dq10 = validate_dq10_fixed_assets
check_dq11 = validate_dq11_tax_rate
check_dq12 = validate_dq12_dividend_payout
check_dq13 = validate_dq13_url_validation
check_dq14 = validate_dq14_eps_sign
check_dq15 = validate_dq15_balancesheet_info
check_dq16 = validate_dq16_coverage
