from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FinancialRatio:
    id: int
    company_id: str
    year: str
    net_profit_margin_pct: Optional[float] = None
    operating_profit_margin_pct: Optional[float] = None
    return_on_equity_pct: Optional[float] = None
    return_on_capital_employed_pct: Optional[float] = None
    return_on_assets_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    asset_turnover: Optional[float] = None
    free_cash_flow_cr: Optional[float] = None
    capex_cr: Optional[float] = None
    earnings_per_share: Optional[float] = None
    book_value_per_share: Optional[float] = None
    dividend_payout_ratio_pct: Optional[float] = None
    total_debt_cr: Optional[float] = None
    cash_from_operations_cr: Optional[float] = None
    revenue_cagr_5yr: Optional[float] = None
    pat_cagr_5yr: Optional[float] = None
    eps_cagr_5yr: Optional[float] = None
    composite_quality_score: Optional[float] = None
    created_at: Optional[str] = None


@dataclass
class ProfitAndLoss:
    company_id: str
    year: str
    sales: Optional[float] = None
    expenses: Optional[float] = None
    operating_profit: Optional[float] = None
    opm_percentage: Optional[float] = None
    other_income: Optional[float] = None
    interest: Optional[float] = None
    depreciation: Optional[float] = None
    profit_before_tax: Optional[float] = None
    tax_percentage: Optional[float] = None
    net_profit: Optional[float] = None
    eps: Optional[float] = None
    dividend_payout: Optional[float] = None


@dataclass
class BalanceSheet:
    company_id: str
    year: str
    equity_capital: Optional[float] = None
    reserves: Optional[float] = None
    borrowings: Optional[float] = None
    other_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None
    fixed_assets: Optional[float] = None
    cwip: Optional[float] = None
    investments: Optional[float] = None
    other_asset: Optional[float] = None
    total_assets: Optional[float] = None


@dataclass
class CashFlow:
    company_id: str
    year: str
    operating_activity: Optional[float] = None
    investing_activity: Optional[float] = None
    financing_activity: Optional[float] = None
    net_cash_flow: Optional[float] = None


class RatioRepository(ABC):
    @abstractmethod
    def get_by_company_and_year(self, company_id: str, year: str) -> Optional[FinancialRatio]:
        pass

    @abstractmethod
    def get_all_by_company(self, company_id: str) -> list[FinancialRatio]:
        pass

    @abstractmethod
    def get_latest_ratios_for_all(self) -> list[FinancialRatio]:
        pass

    @abstractmethod
    def get_historical_ratios(self) -> list[FinancialRatio]:
        pass

    @abstractmethod
    def get_pnl_by_company(self, company_id: str) -> list[ProfitAndLoss]:
        pass

    @abstractmethod
    def get_balancesheet_by_company(self, company_id: str) -> list[BalanceSheet]:
        pass

    @abstractmethod
    def get_cashflow_by_company(self, company_id: str) -> list[CashFlow]:
        pass


from src.database.database import get_db


class SQLiteRatioRepository(RatioRepository):
    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = db_path

    def _row_to_ratio(self, row: sqlite3.Row) -> FinancialRatio:
        return FinancialRatio(
            id=row["id"],
            company_id=row["company_id"],
            year=row["year"],
            net_profit_margin_pct=row["net_profit_margin_pct"],
            operating_profit_margin_pct=row["operating_profit_margin_pct"],
            return_on_equity_pct=row["return_on_equity_pct"],
            return_on_capital_employed_pct=row["return_on_capital_employed_pct"],
            return_on_assets_pct=row["return_on_assets_pct"],
            debt_to_equity=row["debt_to_equity"],
            interest_coverage=row["interest_coverage"],
            asset_turnover=row["asset_turnover"],
            free_cash_flow_cr=row["free_cash_flow_cr"],
            capex_cr=row["capex_cr"],
            earnings_per_share=row["earnings_per_share"],
            book_value_per_share=row["book_value_per_share"],
            dividend_payout_ratio_pct=row["dividend_payout_ratio_pct"],
            total_debt_cr=row["total_debt_cr"],
            cash_from_operations_cr=row["cash_from_operations_cr"],
            revenue_cagr_5yr=row["revenue_cagr_5yr"],
            pat_cagr_5yr=row["pat_cagr_5yr"],
            eps_cagr_5yr=row["eps_cagr_5yr"],
            composite_quality_score=row["composite_quality_score"],
            created_at=row["created_at"],
        )

    def _row_to_pnl(self, row: sqlite3.Row) -> ProfitAndLoss:
        return ProfitAndLoss(
            company_id=row["company_id"],
            year=row["year"],
            sales=row["sales"],
            expenses=row["expenses"],
            operating_profit=row["operating_profit"],
            opm_percentage=row["opm_percentage"],
            other_income=row["other_income"],
            interest=row["interest"],
            depreciation=row["depreciation"],
            profit_before_tax=row["profit_before_tax"],
            tax_percentage=row["tax_percentage"],
            net_profit=row["net_profit"],
            eps=row["eps"],
            dividend_payout=row["dividend_payout"],
        )

    def _row_to_balancesheet(self, row: sqlite3.Row) -> BalanceSheet:
        return BalanceSheet(
            company_id=row["company_id"],
            year=row["year"],
            equity_capital=row["equity_capital"],
            reserves=row["reserves"],
            borrowings=row["borrowings"],
            other_liabilities=row["other_liabilities"],
            total_liabilities=row["total_liabilities"],
            fixed_assets=row["fixed_assets"],
            cwip=row["cwip"],
            investments=row["investments"],
            other_asset=row["other_asset"],
            total_assets=row["total_assets"],
        )

    def _row_to_cashflow(self, row: sqlite3.Row) -> CashFlow:
        return CashFlow(
            company_id=row["company_id"],
            year=row["year"],
            operating_activity=row["operating_activity"],
            investing_activity=row["investing_activity"],
            financing_activity=row["financing_activity"],
            net_cash_flow=row["net_cash_flow"],
        )

    def get_by_company_and_year(self, company_id: str, year: str) -> Optional[FinancialRatio]:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?"
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id, year))
            row = cursor.fetchone()
            if row:
                return self._row_to_ratio(row)
        return None

    def get_all_by_company(self, company_id: str) -> list[FinancialRatio]:
        query = "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC"
        ratios = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                ratios.append(self._row_to_ratio(row))
        return ratios

    def get_latest_ratios_for_all(self) -> list[FinancialRatio]:
        # Subquery to select latest ratios by year
        query = """
            WITH ranked_ratios AS (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
                FROM financial_ratios
            )
            SELECT * FROM ranked_ratios WHERE rn = 1
        """
        ratios = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                ratios.append(self._row_to_ratio(row))
        return ratios

    def get_historical_ratios(self) -> list[FinancialRatio]:
        query = "SELECT * FROM financial_ratios ORDER BY company_id ASC, year ASC"
        ratios = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                ratios.append(self._row_to_ratio(row))
        return ratios

    def get_pnl_by_company(self, company_id: str) -> list[ProfitAndLoss]:
        query = "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC"
        pnls = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                pnls.append(self._row_to_pnl(row))
        return pnls

    def get_balancesheet_by_company(self, company_id: str) -> list[BalanceSheet]:
        query = "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC"
        balances = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                balances.append(self._row_to_balancesheet(row))
        return balances

    def get_cashflow_by_company(self, company_id: str) -> list[CashFlow]:
        query = "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC"
        flows = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                flows.append(self._row_to_cashflow(row))
        return flows
