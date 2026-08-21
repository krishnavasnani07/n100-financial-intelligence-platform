from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.database.database import get_db, init_db
from src.repositories.company_repository import SQLiteCompanyRepository
from src.repositories.market_repository import SQLiteMarketRepository
from src.repositories.peer_repository import SQLitePeerRepository
from src.repositories.ratio_repository import SQLiteRatioRepository


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Creates a temporary SQLite database initialized with the project schema."""
    db_file = tmp_path / "test_nifty100_v2.db"
    
    # Locate schema.sql in workspace
    schema_path = Path(__file__).resolve().parent.parent.parent.parent / "db" / "schema.sql"
    init_db(db_file, schema_path)
    
    # Populate mock data for testing
    with get_db(db_file) as conn:
        # 1. Insert Companies
        conn.execute(
            """
            INSERT INTO companies (id, company_name, face_value, book_value, roce_percentage, roe_percentage)
            VALUES 
                ('TCS', 'Tata Consultancy Services', 1.0, 310.0, 52.0, 48.0),
                ('INFY', 'Infosys Limited', 5.0, 240.0, 38.0, 31.0),
                ('RELIANCE', 'Reliance Industries Limited', 10.0, 1200.0, 11.5, 10.2),
                ('HDFCBANK', 'HDFC Bank Limited', 1.0, 520.0, 18.2, 16.5),
                ('LT', 'Larsen & Toubro Limited', 2.0, 410.0, 14.5, 12.8);
            """
        )
        # 2. Insert Sectors
        conn.execute(
            """
            INSERT INTO sectors (company_id, broad_sector, sub_sector, index_weight_pct, market_cap_category)
            VALUES 
                ('TCS', 'IT', 'Computers - Software', 7.5, 'Large Cap'),
                ('INFY', 'IT', 'Computers - Software', 5.2, 'Large Cap'),
                ('RELIANCE', 'Energy', 'Oil & Gas', 10.1, 'Large Cap'),
                ('HDFCBANK', 'Financial Services', 'Banks', 9.2, 'Large Cap'),
                ('LT', 'Construction', 'Engineering', 4.1, 'Large Cap');
            """
        )
        # 3. Insert Profit and Loss
        conn.execute(
            """
            INSERT INTO profitandloss (company_id, year, sales, expenses, operating_profit, net_profit, eps, dividend_payout)
            VALUES 
                ('TCS', 'Mar 2023', 225330.0, 165000.0, 60330.0, 42150.0, 115.0, 80.0),
                ('TCS', 'Mar 2024', 240890.0, 175000.0, 65890.0, 46100.0, 126.0, 85.0),
                ('INFY', 'Mar 2023', 146760.0, 110000.0, 36760.0, 24100.0, 58.0, 45.0),
                ('INFY', 'Mar 2024', 153670.0, 115000.0, 38670.0, 26230.0, 63.0, 50.0),
                ('RELIANCE', 'Mar 2023', 890000.0, 750000.0, 140000.0, 66000.0, 98.0, 10.0),
                ('RELIANCE', 'Mar 2024', 920000.0, 770000.0, 150000.0, 70000.0, 103.0, 12.0),
                ('HDFCBANK', 'Mar 2023', 190000.0, 120000.0, 70000.0, 44000.0, 78.0, 15.0),
                ('HDFCBANK', 'Mar 2024', 210000.0, 130000.0, 80000.0, 50000.0, 89.0, 18.0),
                ('LT', 'Mar 2023', 180000.0, 160000.0, 20000.0, 10400.0, 74.0, 22.0),
                ('LT', 'Mar 2024', 200000.0, 178000.0, 22000.0, 12500.0, 89.0, 26.0);
            """
        )
        # 4. Insert Balance Sheet
        conn.execute(
            """
            INSERT INTO balancesheet (company_id, year, equity_capital, reserves, borrowings, total_assets)
            VALUES 
                ('TCS', 'Mar 2023', 366.0, 95000.0, 7800.0, 142000.0),
                ('TCS', 'Mar 2024', 366.0, 105000.0, 8200.0, 155000.0),
                ('INFY', 'Mar 2023', 2070.0, 75000.0, 5500.0, 112000.0),
                ('INFY', 'Mar 2024', 2070.0, 82000.0, 5200.0, 124000.0),
                ('RELIANCE', 'Mar 2023', 6760.0, 800000.0, 310000.0, 1400000.0),
                ('RELIANCE', 'Mar 2024', 6760.0, 860000.0, 320000.0, 1500000.0),
                ('HDFCBANK', 'Mar 2023', 558.0, 280000.0, 2000000.0, 2400000.0),
                ('HDFCBANK', 'Mar 2024', 558.0, 320000.0, 2200000.0, 2600000.0),
                ('LT', 'Mar 2023', 280.0, 85000.0, 110000.0, 310000.0),
                ('LT', 'Mar 2024', 280.0, 95000.0, 115000.0, 330000.0);
            """
        )
        # 5. Insert Cash Flow
        conn.execute(
            """
            INSERT INTO cashflow (company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow)
            VALUES 
                ('TCS', 'Mar 2024', 45000.0, -12000.0, -32000.0, 1000.0),
                ('INFY', 'Mar 2024', 28000.0, -8000.0, -20000.0, 0.0),
                ('RELIANCE', 'Mar 2024', 120000.0, -95000.0, -20000.0, 5000.0),
                ('HDFCBANK', 'Mar 2024', 150000.0, -30000.0, -115000.0, 5000.0),
                ('LT', 'Mar 2024', 25000.0, -15000.0, -11000.0, -1000.0);
            """
        )
        # 6. Insert Financial Ratios
        conn.execute(
            """
            INSERT INTO financial_ratios (company_id, year, return_on_equity_pct, return_on_capital_employed_pct, debt_to_equity, interest_coverage, earnings_per_share, book_value_per_share, composite_quality_score, revenue_cagr_5yr, pat_cagr_5yr)
            VALUES 
                ('TCS', 'Mar 2023', 45.1, 51.2, 0.08, 12.5, 115.0, 260.0, 91.5, 12.1, 14.2),
                ('TCS', 'Mar 2024', 48.2, 56.1, 0.08, 14.2, 126.0, 287.0, 93.4, 12.4, 14.1),
                ('INFY', 'Mar 2023', 29.5, 36.4, 0.07, 10.1, 58.0, 185.0, 84.2, 10.5, 11.2),
                ('INFY', 'Mar 2024', 31.7, 39.8, 0.06, 11.5, 63.0, 203.0, 86.8, 10.8, 11.5),
                ('RELIANCE', 'Mar 2023', 9.8, 10.5, 0.38, 4.2, 98.0, 1150.0, 68.5, 9.2, 8.5),
                ('RELIANCE', 'Mar 2024', 10.2, 11.2, 0.37, 4.8, 103.0, 1230.0, 70.1, 9.5, 8.8),
                ('HDFCBANK', 'Mar 2023', 16.1, 17.5, 6.8, 2.5, 78.0, 480.0, 75.4, 14.5, 16.2),
                ('HDFCBANK', 'Mar 2024', 16.5, 18.0, 6.5, 2.8, 89.0, 515.0, 77.2, 15.1, 16.8),
                ('LT', 'Mar 2023', 12.1, 13.8, 1.25, 3.1, 74.0, 390.0, 71.2, 8.4, 9.1),
                ('LT', 'Mar 2024', 12.8, 14.2, 1.18, 3.4, 89.0, 412.0, 72.8, 8.8, 9.5);
            """
        )
        # 7. Insert Stock Prices
        # We need a series of prices to test volatility/beta and 52w metrics
        for date, price_tcs, price_infy, price_rel, price_hdfc, price_lt in [
            ("2024-01-01", 3400.0, 1500.0, 2400.0, 1600.0, 3200.0),
            ("2024-01-02", 3420.0, 1510.0, 2420.0, 1610.0, 3210.0),
            ("2024-01-03", 3410.0, 1490.0, 2390.0, 1590.0, 3190.0),
            ("2024-01-04", 3450.0, 1530.0, 2450.0, 1630.0, 3250.0),
            ("2024-01-05", 3480.0, 1550.0, 2480.0, 1650.0, 3280.0),
        ]:
            conn.execute(
                """
                INSERT INTO stock_prices (company_id, date, open_price, high_price, low_price, close_price, volume)
                VALUES 
                    ('TCS', ?, ?, ?, ?, ?, 100000),
                    ('INFY', ?, ?, ?, ?, ?, 150000),
                    ('RELIANCE', ?, ?, ?, ?, ?, 200000),
                    ('HDFCBANK', ?, ?, ?, ?, ?, 250000),
                    ('LT', ?, ?, ?, ?, ?, 80000);
                """,
                (date, price_tcs, price_tcs + 20, price_tcs - 20, price_tcs,
                 date, price_infy, price_infy + 15, price_infy - 15, price_infy,
                 date, price_rel, price_rel + 30, price_rel - 30, price_rel,
                 date, price_hdfc, price_hdfc + 10, price_hdfc - 10, price_hdfc,
                 date, price_lt, price_lt + 25, price_lt - 25, price_lt)
            )
            
        # 8. Peer Groups
        conn.execute(
            """
            INSERT INTO peer_groups (peer_group_name, company_id, is_benchmark)
            VALUES 
                ('IT_Peers', 'TCS', 1),
                ('IT_Peers', 'INFY', 0);
            """
        )
    return db_file


def test_company_repository(test_db_path: Path):
    repo = SQLiteCompanyRepository(test_db_path)
    
    # Test get_by_id
    comp = repo.get_by_id("TCS")
    assert comp is not None
    assert comp.company_name == "Tata Consultancy Services"
    assert comp.roe_percentage == 48.0
    
    # Test get_all
    all_comps = repo.get_all()
    assert len(all_comps) == 5
    assert all_comps[0].id == "HDFCBANK"  # Sorted alphabetically by ID
    assert all_comps[4].id == "TCS"
    
    # Test search
    search_res = repo.search("Tata")
    assert len(search_res) == 1
    assert search_res[0].id == "TCS"


def test_ratio_repository(test_db_path: Path):
    repo = SQLiteRatioRepository(test_db_path)
    
    # Test get_by_company_and_year
    ratio = repo.get_by_company_and_year("TCS", "Mar 2024")
    assert ratio is not None
    assert ratio.return_on_equity_pct == 48.2
    assert ratio.composite_quality_score == 93.4
    
    # Test get_all_by_company
    tcs_ratios = repo.get_all_by_company("TCS")
    assert len(tcs_ratios) == 2
    assert tcs_ratios[0].year == "Mar 2023"
    assert tcs_ratios[1].year == "Mar 2024"
    
    # Test get_latest_ratios_for_all
    latests = repo.get_latest_ratios_for_all()
    assert len(latests) == 5
    for r in latests:
        assert r.year == "Mar 2024"
        
    # Test Statement queries
    pnls = repo.get_pnl_by_company("INFY")
    assert len(pnls) == 2
    assert pnls[1].sales == 153670.0
    
    bs = repo.get_balancesheet_by_company("INFY")
    assert len(bs) == 2
    assert bs[1].equity_capital == 2070.0
    
    cfs = repo.get_cashflow_by_company("TCS")
    assert len(cfs) == 1
    assert cfs[0].operating_activity == 45000.0


def test_market_repository(test_db_path: Path):
    repo = SQLiteMarketRepository(test_db_path)
    
    # Test get_prices_by_company
    prices = repo.get_prices_by_company("TCS")
    assert len(prices) == 5
    assert prices[-1].close_price == 3480.0
    
    # Test get_latest_price
    latest = repo.get_latest_price("INFY")
    assert latest is not None
    assert latest.close_price == 1550.0
    
    # Test get_market_metrics
    metrics = repo.get_market_metrics("TCS")
    assert metrics is not None
    assert metrics.current_price == 3480.0
    assert metrics.fifty_two_week_high == 3480.0
    assert metrics.fifty_two_week_low == 3400.0
    assert metrics.volatility > 0.0
    assert metrics.beta is not None
    assert metrics.pe_ratio == round(3480.0 / 126.0, 2)


def test_peer_repository(test_db_path: Path):
    repo = SQLitePeerRepository(test_db_path)
    
    # Test get_all_sectors
    sectors = repo.get_all_sectors()
    assert "IT" in sectors
    
    # Test get_sector_by_company
    sec = repo.get_sector_by_company("INFY")
    assert sec is not None
    assert sec.broad_sector == "IT"
    
    # Test get_companies_in_sector
    comps = repo.get_companies_in_sector("IT")
    assert "INFY" in comps
    assert "TCS" in comps
    
    # Test get_peer_group_by_company
    peers = repo.get_peer_group_by_company("TCS")
    assert len(peers) == 2
    assert peers[0].peer_group_name == "IT_Peers"
    
    # Test get_sector_statistics
    stats = repo.get_sector_statistics("IT", ["ROE", "Composite Quality Score"])
    assert len(stats) == 2
    assert stats[0].kpi == "ROE"
    # TCS is 48.2, INFY is 31.7 -> median is 39.95
    assert stats[0].median == 39.95
