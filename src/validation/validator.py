from pathlib import Path
from typing import Any

import pandas as pd

from src.config import settings
from src.etl.loader import load_excel
from src.utils.logger import get_logger
from src.validation import dq_rules
from src.validation.exceptions import DataLoadError
from src.validation.report import ValidationReport

logger = get_logger(__name__)


class DataValidator:
    """
    Reusable validation engine to register and execute DQ rules,
    aggregate failures, and generate validation reports.
    """

    def __init__(self, raw_data_dir: Path | None = None):
        self.raw_data_dir = raw_data_dir or settings.RAW_DATA_DIR
        self.report = ValidationReport()
        self.datasets: dict[str, pd.DataFrame] = {}

    def load_all_datasets(self) -> dict[str, pd.DataFrame]:
        """
        Loads all 12 datasets with their specific sheet names and headers.
        """
        logger.info(f"Loading datasets for validation from {self.raw_data_dir}...")

        # Mappings of filename -> (sheet_name, header_row_index, dataset_key)
        mappings = {
            "companies.xlsx": ("Companies", 1, "companies"),
            "balancesheet.xlsx": ("Balance Sheet", 1, "balancesheet"),
            "cashflow.xlsx": ("Cash Flow", 1, "cashflow"),
            "profitandloss.xlsx": ("Profit & Loss", 1, "profitandloss"),
            "prosandcons.xlsx": ("Pros & Cons", 1, "prosandcons"),
            "analysis.xlsx": ("Analysis", 1, "analysis"),
            "documents.xlsx": ("Documents", 1, "documents"),
            "financial_ratios.xlsx": (0, 0, "financial_ratios"),
            "market_cap.xlsx": (0, 0, "market_cap"),
            "peer_groups.xlsx": (0, 0, "peer_groups"),
            "sectors.xlsx": (0, 0, "sectors"),
            "stock_prices.xlsx": (0, 0, "stock_prices"),
        }

        for filename, (sheet, header, key) in mappings.items():
            file_path = self.raw_data_dir / filename
            if not file_path.exists():
                logger.error(f"Required Excel file not found: {file_path}")
                raise DataLoadError(f"Missing required dataset: {filename}")

            df = load_excel(file_path, sheet_name=sheet, header=header)
            if df is None:
                logger.error(f"Failed to load dataset: {filename}")
                raise DataLoadError(f"Failed to read data from: {filename}")

            # Clean columns: strip whitespace
            df.columns = [str(col).strip() for col in df.columns]
            self.datasets[key] = df
            logger.info(f"Loaded '{key}' dataset with {len(df)} records.")

        return self.datasets

    def run_validation(self) -> dict[str, Any]:
        """
        Executes all 16 DQ rules against the loaded datasets.
        Returns a validation summary dictionary.
        """
        if not self.datasets:
            self.load_all_datasets()

        logger.info("Starting Data Quality validation pipeline...")
        self.report = ValidationReport()  # Reset report for a fresh run

        # Execute CRITICAL Rules
        dq_rules.validate_dq01_company_pk(self.datasets.get("companies"), self.report)
        dq_rules.validate_dq02_no_duplicate_company_year(self.datasets, self.report)
        dq_rules.validate_dq03_foreign_keys(self.datasets, self.report)
        dq_rules.validate_dq07_year_format(self.datasets, self.report)
        dq_rules.validate_dq08_ticker_format(self.datasets, self.report)

        # Execute WARNING Rules
        dq_rules.validate_dq04_balancesheet_balance(
            self.datasets.get("balancesheet"), self.report
        )
        dq_rules.validate_dq05_opm_crosscheck(
            self.datasets.get("profitandloss"), self.report
        )
        dq_rules.validate_dq06_positive_sales(
            self.datasets.get("profitandloss"), self.report
        )
        dq_rules.validate_dq09_net_cash_flow(self.datasets.get("cashflow"), self.report)
        dq_rules.validate_dq10_fixed_assets(
            self.datasets.get("balancesheet"), self.report
        )
        dq_rules.validate_dq11_tax_rate(self.datasets.get("profitandloss"), self.report)
        dq_rules.validate_dq12_dividend_payout(
            self.datasets.get("profitandloss"), self.report
        )
        dq_rules.validate_dq13_url_validation(self.datasets, self.report)
        dq_rules.validate_dq14_eps_sign(self.datasets.get("profitandloss"), self.report)
        dq_rules.validate_dq15_balancesheet_info(
            self.datasets.get("balancesheet"), self.report
        )
        dq_rules.validate_dq16_coverage(self.datasets, self.report)

        # Aggregate results
        total_failures = len(self.report.failures)
        critical_failures = sum(
            1 for f in self.report.failures if f.severity == "CRITICAL"
        )
        warning_failures = sum(
            1 for f in self.report.failures if f.severity == "WARNING"
        )

        status = "Passed" if critical_failures == 0 else "Failed"
        success = critical_failures == 0

        summary = {
            "success": success,
            "status": status,
            "total_failures": total_failures,
            "critical_failures": critical_failures,
            "warning_failures": warning_failures,
            "rules_checked": list(self.report.rules_checked.keys()),
        }

        logger.info(
            f"Validation run completed. Status: {status}. "
            f"Total failures: {total_failures} (Critical: {critical_failures}, Warning: {warning_failures})."
        )

        # Save reports
        self.report.save()

        return summary
