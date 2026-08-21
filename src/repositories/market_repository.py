from __future__ import annotations

import math
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.database.database import get_db


@dataclass
class StockPrice:
    company_id: str
    date: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None


@dataclass
class MarketMetrics:
    company_id: str
    current_price: float
    volume: int
    market_cap: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    volatility: float
    beta: float
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None


class MarketRepository(ABC):
    @abstractmethod
    def get_prices_by_company(self, company_id: str) -> list[StockPrice]:
        pass

    @abstractmethod
    def get_all_prices(self) -> list[StockPrice]:
        pass

    @abstractmethod
    def get_latest_price(self, company_id: str) -> Optional[StockPrice]:
        pass

    @abstractmethod
    def get_market_metrics(self, company_id: str) -> Optional[MarketMetrics]:
        pass


class SQLiteMarketRepository(MarketRepository):
    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = db_path

    def _row_to_stock_price(self, row: sqlite3.Row) -> StockPrice:
        return StockPrice(
            company_id=row["company_id"],
            date=row["date"],
            open_price=row["open_price"],
            high_price=row["high_price"],
            low_price=row["low_price"],
            close_price=row["close_price"],
            volume=row["volume"],
            adjusted_close=row["adjusted_close"],
        )

    def get_prices_by_company(self, company_id: str) -> list[StockPrice]:
        query = "SELECT * FROM stock_prices WHERE company_id = ? ORDER BY date ASC"
        prices = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                prices.append(self._row_to_stock_price(row))
        return prices

    def get_all_prices(self) -> list[StockPrice]:
        query = "SELECT * FROM stock_prices ORDER BY company_id ASC, date ASC"
        prices = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                prices.append(self._row_to_stock_price(row))
        return prices

    def get_latest_price(self, company_id: str) -> Optional[StockPrice]:
        query = "SELECT * FROM stock_prices WHERE company_id = ? ORDER BY date DESC LIMIT 1"
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_stock_price(row)
        return None

    def get_market_metrics(self, company_id: str) -> Optional[MarketMetrics]:
        # 1. Fetch latest price
        latest_price_obj = self.get_latest_price(company_id)
        if not latest_price_obj:
            return None

        current_price = latest_price_obj.close_price
        volume = latest_price_obj.volume

        # 2. Fetch prices for 52-week high/low and volatility calculations
        # We need historical prices for this company
        prices = self.get_prices_by_company(company_id)
        if not prices:
            return None

        df_prices = pd.DataFrame([p.__dict__ for p in prices])
        df_prices["date"] = pd.to_datetime(df_prices["date"])
        df_prices = df_prices.sort_values(by="date")

        # 52-week High and Low
        latest_date = df_prices["date"].max()
        one_year_ago = latest_date - pd.Timedelta(days=365)
        df_52w = df_prices[df_prices["date"] >= one_year_ago]
        
        fifty_two_week_high = float(df_52w["close_price"].max()) if not df_52w.empty else current_price
        fifty_two_week_low = float(df_52w["close_price"].min()) if not df_52w.empty else current_price

        # Volatility (annualized std dev of daily returns)
        df_prices["returns"] = df_prices["close_price"].pct_change()
        daily_returns = df_prices["returns"].dropna()
        if len(daily_returns) > 1:
            volatility = float(daily_returns.std() * math.sqrt(252) * 100)
        else:
            volatility = 0.0

        # 3. Calculate Beta against the N100 benchmark (equal-weighted average of all stocks)
        beta = 1.0
        with get_db(self.db_path) as conn:
            # Query all stock prices to construct the benchmark returns
            query_all = "SELECT company_id, date, close_price FROM stock_prices ORDER BY date"
            df_all = pd.read_sql_query(query_all, conn)
        
        if not df_all.empty:
            df_all_pivot = df_all.pivot(index="date", columns="company_id", values="close_price").dropna()
            if company_id in df_all_pivot.columns:
                all_returns = df_all_pivot.pct_change().dropna()
                benchmark_returns = all_returns.mean(axis=1)
                comp_returns = all_returns[company_id]
                
                common_idx = comp_returns.index.intersection(benchmark_returns.index)
                if len(common_idx) > 5:
                    cov = comp_returns.loc[common_idx].cov(benchmark_returns.loc[common_idx])
                    var = benchmark_returns.loc[common_idx].var()
                    if var > 0:
                        beta = float(cov / var)

        # 4. Fetch latest ratios (to get EPS, BVPS, Dividend Payout, Equity Capital)
        pe_ratio = None
        pb_ratio = None
        ev_ebitda = None
        dividend_yield = None
        market_cap = 0.0

        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch latest financial ratios
            cursor.execute(
                "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
                (company_id,)
            )
            ratio_row = cursor.fetchone()
            
            # Fetch equity capital and reserves from latest balance sheet for shares outstanding estimate
            cursor.execute(
                "SELECT equity_capital, reserves FROM balancesheet WHERE company_id = ? ORDER BY year DESC LIMIT 1",
                (company_id,)
            )
            bs_row = cursor.fetchone()
            
            # Fetch EBITDA or Operating Profit + Depreciation from profit & loss
            cursor.execute(
                "SELECT operating_profit, depreciation, net_profit, interest FROM profitandloss WHERE company_id = ? ORDER BY year DESC LIMIT 1",
                (company_id,)
            )
            pnl_row = cursor.fetchone()

        # Calculate estimated shares outstanding & market cap
        # standard estimate: shares = equity_capital (in Cr) * 10^7 / face_value
        # If we don't have face_value or equity_capital, fallback to using book value per share
        shares = None
        if bs_row and bs_row["equity_capital"]:
            # Retrieve face value from companies table
            with get_db(self.db_path) as conn:
                fv_row = conn.execute("SELECT face_value FROM companies WHERE id = ?", (company_id,)).fetchone()
                face_value = fv_row[0] if fv_row and fv_row[0] else 10.0
            
            equity_capital_rs = bs_row["equity_capital"] * 10_000_000  # Convert Cr to Rs
            shares = equity_capital_rs / face_value
            market_cap = (shares * current_price) / 10_000_000  # Market Cap in Cr
        elif ratio_row and ratio_row["book_value_per_share"] and bs_row and bs_row["equity_capital"] and bs_row["reserves"]:
            # book_value = equity_capital + reserves
            net_worth = (bs_row["equity_capital"] + bs_row["reserves"]) * 10_000_000
            bvps = ratio_row["book_value_per_share"]
            if bvps > 0:
                shares = net_worth / bvps
                market_cap = (shares * current_price) / 10_000_000

        # Fallback if no balance sheet data: use standard average
        if market_cap == 0.0:
            market_cap = 50000.0  # fallback mock market cap in Cr

        if ratio_row:
            eps = ratio_row["earnings_per_share"]
            bvps = ratio_row["book_value_per_share"]
            div_pct = ratio_row["dividend_payout_ratio_pct"]
            
            if eps and eps > 0:
                pe_ratio = float(current_price / eps)
            if bvps and bvps > 0:
                pb_ratio = float(current_price / bvps)
                
            # Dividend Yield calculation
            # Dividend per share = EPS * (div_pct / 100)
            if eps and div_pct:
                dps = eps * (div_pct / 100.0)
                dividend_yield = float((dps / current_price) * 100)

        # EV/EBITDA calculation
        if pnl_row:
            op = pnl_row["operating_profit"] or 0.0
            dep = pnl_row["depreciation"] or 0.0
            ebitda = op + dep  # EBITDA in Cr
            
            # EV = Market Cap + Debt - Cash
            # Total Debt = total borrowings from balance sheet (or total_debt_cr from ratios)
            debt = 0.0
            if ratio_row and ratio_row["total_debt_cr"]:
                debt = ratio_row["total_debt_cr"]
            
            cash = 0.0  # cash approximation (we don't have separate cash column in balance sheet schema, so fallback cash = 0)
            ev = market_cap + debt - cash
            if ebitda > 0:
                ev_ebitda = float(ev / ebitda)

        return MarketMetrics(
            company_id=company_id,
            current_price=float(current_price),
            volume=int(volume),
            market_cap=round(float(market_cap), 2),
            pe_ratio=round(pe_ratio, 2) if pe_ratio else None,
            pb_ratio=round(pb_ratio, 2) if pb_ratio else None,
            ev_ebitda=round(ev_ebitda, 2) if ev_ebitda else None,
            dividend_yield=round(dividend_yield, 2) if dividend_yield else None,
            fifty_two_week_high=round(fifty_two_week_high, 2),
            fifty_two_week_low=round(fifty_two_week_low, 2),
            volatility=round(volatility, 2),
            beta=round(beta, 3),
        )
