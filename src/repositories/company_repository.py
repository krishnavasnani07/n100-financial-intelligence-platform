from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.database.database import get_db


@dataclass
class Company:
    id: str
    company_name: str
    company_logo: Optional[str] = None
    chart_link: Optional[str] = None
    about_company: Optional[str] = None
    website: Optional[str] = None
    nse_profile: Optional[str] = None
    bse_profile: Optional[str] = None
    face_value: Optional[float] = None
    book_value: Optional[float] = None
    roce_percentage: Optional[float] = None
    roe_percentage: Optional[float] = None
    created_at: Optional[str] = None


class CompanyRepository(ABC):
    @abstractmethod
    def get_by_id(self, company_id: str) -> Optional[Company]:
        pass

    @abstractmethod
    def get_all(self) -> list[Company]:
        pass

    @abstractmethod
    def search(self, query: str) -> list[Company]:
        pass


class SQLiteCompanyRepository(CompanyRepository):
    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = db_path

    def _row_to_company(self, row: sqlite3.Row) -> Company:
        return Company(
            id=row["id"],
            company_name=row["company_name"],
            company_logo=row["company_logo"],
            chart_link=row["chart_link"],
            about_company=row["about_company"],
            website=row["website"],
            nse_profile=row["nse_profile"],
            bse_profile=row["bse_profile"],
            face_value=row["face_value"],
            book_value=row["book_value"],
            roce_percentage=row["roce_percentage"],
            roe_percentage=row["roe_percentage"],
            created_at=row["created_at"],
        )

    def get_by_id(self, company_id: str) -> Optional[Company]:
        query = "SELECT * FROM companies WHERE id = ?"
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (company_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_company(row)
        return None

    def get_all(self) -> list[Company]:
        query = "SELECT * FROM companies ORDER BY id ASC"
        companies = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                companies.append(self._row_to_company(row))
        return companies

    def search(self, query: str) -> list[Company]:
        sql = "SELECT * FROM companies WHERE id LIKE ? OR company_name LIKE ? ORDER BY id ASC"
        like_query = f"%{query}%"
        companies = []
        with get_db(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, (like_query, like_query))
            rows = cursor.fetchall()
            for row in rows:
                companies.append(self._row_to_company(row))
        return companies
