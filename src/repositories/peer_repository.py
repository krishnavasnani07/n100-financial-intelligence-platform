from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.database.database import get_db


@dataclass
class SectorInfo:
    company_id: str
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    index_weight_pct: Optional[float] = None
    market_cap_category: Optional[str] = None


@dataclass
class PeerGroupInfo:
    peer_group_name: str
    company_id: str
    is_benchmark: int


@dataclass
class SectorStatistic:
    sector: str
    kpi: str
    mean: float
    median: float
    minimum: float
    maximum: float
    std_dev: float


class PeerRepository(ABC):
    @abstractmethod
    def get_all_sectors(self) -> list[str]:
        pass

    @abstractmethod
    def get_sector_by_company(self, company_id: str) -> Optional[SectorInfo]:
        pass

    @abstractmethod
    def get_companies_in_sector(self, sector: str) -> list[str]:
        pass

    @abstractmethod
    def get_peer_group_by_company(self, company_id: str) -> list[PeerGroupInfo]:
        pass

    @abstractmethod
    def get_sector_statistics(self, sector: str, kpis: list[str]) -> list[SectorStatistic]:
        pass


class SQLitePeerRepository(PeerRepository):
    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = db_path

    def _row_to_sector_info(self, row: sqlite3.Row) -> SectorInfo:
        return SectorInfo(
            company_id=row["company_id"],
            broad_sector=row["broad_sector"],
            sub_sector=row["sub_sector"],
            index_weight_pct=row["index_weight_pct"],
            market_cap_category=row["market_cap_category"],
        )

    def _row_to_peer_group_info(self, row: sqlite3.Row) -> PeerGroupInfo:
        return PeerGroupInfo(
            peer_group_name=row["peer_group_name"],
            company_id=row["company_id"],
            is_benchmark=row["is_benchmark"],
        )

    def get_all_sectors(self) -> list[str]:
        query = "SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL ORDER BY broad_sector ASC"
        sectors = []
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                sectors.append(row[0])
        return sectors

    def get_sector_by_company(self, company_id: str) -> Optional[SectorInfo]:
        query = "SELECT * FROM sectors WHERE company_id = ?"
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_sector_info(row)
        return None

    def get_companies_in_sector(self, sector: str) -> list[str]:
        query = "SELECT company_id FROM sectors WHERE broad_sector = ? ORDER BY company_id ASC"
        companies = []
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (sector,))
            rows = cursor.fetchall()
            for row in rows:
                companies.append(row[0])
        return companies

    def get_peer_group_by_company(self, company_id: str) -> list[PeerGroupInfo]:
        # Find if the company belongs to any peer group and fetch all companies in that peer group
        query = """
            SELECT peer_group_name, company_id, is_benchmark 
            FROM peer_groups 
            WHERE peer_group_name IN (
                SELECT DISTINCT peer_group_name FROM peer_groups WHERE company_id = ?
            )
            ORDER BY peer_group_name ASC, company_id ASC
        """
        peers = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            rows = cursor.fetchall()
            for row in rows:
                peers.append(self._row_to_peer_group_info(row))
        return peers

    def get_sector_statistics(self, sector: str, kpis: list[str]) -> list[SectorStatistic]:
        # Let's map clean column names
        column_mapping = {
            "ROE": "return_on_equity_pct",
            "ROCE": "return_on_capital_employed_pct",
            "Revenue CAGR": "revenue_cagr_5yr",
            "PAT CAGR": "pat_cagr_5yr",
            "Operating Margin": "operating_profit_margin_pct",
            "Debt to Equity": "debt_to_equity",
            "Interest Coverage": "interest_coverage",
            "Composite Quality Score": "composite_quality_score",
        }

        # Query all latest ratios for the sector
        placeholders = ", ".join(["?"] * len(kpis))
        db_cols = [column_mapping.get(k, k) for k in kpis]
        
        query = f"""
            WITH ranked_ratios AS (
                SELECT fr.*, s.broad_sector,
                       ROW_NUMBER() OVER (PARTITION BY fr.company_id ORDER BY fr.year DESC) as rn
                FROM financial_ratios fr
                JOIN sectors s ON fr.company_id = s.company_id
                WHERE s.broad_sector = ?
            )
            SELECT * FROM ranked_ratios WHERE rn = 1
        """

        stats_list = []
        with get_db(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=[sector])

        for kpi in kpis:
            col_name = column_mapping.get(kpi, kpi)
            if col_name not in df.columns:
                continue
            
            series = df[col_name].dropna()
            if not series.empty:
                mean_val = float(series.mean())
                median_val = float(series.median())
                min_val = float(series.min())
                max_val = float(series.max())
                std_val = float(series.std()) if len(series) > 1 else 0.0
            else:
                mean_val = 0.0
                median_val = 0.0
                min_val = 0.0
                max_val = 0.0
                std_val = 0.0
                
            stats_list.append(
                SectorStatistic(
                    sector=sector,
                    kpi=kpi,
                    mean=round(mean_val, 4),
                    median=round(median_val, 4),
                    minimum=round(min_val, 4),
                    maximum=round(max_val, 4),
                    std_dev=round(std_val, 4),
                )
            )

        return stats_list
