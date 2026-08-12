"""
Unit tests for the NLP Text Parser and CAGR Validation module.
"""

import pytest
import pandas as pd
import sqlite3
import numpy as np
from unittest.mock import MagicMock

from src.nlp.parser import parse_growth_metric, get_computed_value, METRIC_MAPPING


def test_parse_growth_metric_single():
    """Test parsing simple single metrics with spaces, decimals, and negative values."""
    # Positive integer
    res = parse_growth_metric("10 Years: 21%", "Sales CAGR")
    assert res == [{"metric_type": "Sales CAGR", "period_years": 10, "value_pct": 21.0}]

    # Decimals and spaces
    res = parse_growth_metric("5 Years : 18.4%", "Profit CAGR")
    assert res == [{"metric_type": "Profit CAGR", "period_years": 5, "value_pct": 18.4}]

    # Negative values
    res = parse_growth_metric("3 Years: -12.5%", "Stock Price CAGR")
    assert res == [
        {"metric_type": "Stock Price CAGR", "period_years": 3, "value_pct": -12.5}
    ]

    # Space in 'Years'
    res = parse_growth_metric("1 Year: 15%", "ROE")
    assert res == [{"metric_type": "ROE", "period_years": 1, "value_pct": 15.0}]


def test_parse_growth_metric_multiple():
    """Test parsing multiple CAGR records in one cell (separated by commas or newlines)."""
    text = "10 Years: 21%, 5 Years : 18.4%\n3 Years: -2%"
    res = parse_growth_metric(text, "Sales CAGR")
    assert len(res) == 3
    assert res[0] == {
        "metric_type": "Sales CAGR",
        "period_years": 10,
        "value_pct": 21.0,
    }
    assert res[1] == {"metric_type": "Sales CAGR", "period_years": 5, "value_pct": 18.4}
    assert res[2] == {"metric_type": "Sales CAGR", "period_years": 3, "value_pct": -2.0}


def test_parse_growth_metric_failures():
    """Test handling of invalid and non-matching formats."""
    # TTM (no years)
    assert parse_growth_metric("TTM: 43%", "Sales CAGR") is None

    # Last Year (no digits for years)
    assert parse_growth_metric("Last Year: 12%", "ROE") is None

    # Missing percentage symbol
    assert parse_growth_metric("10 Years: 21", "Sales CAGR") is None

    # Completely empty or invalid inputs
    assert parse_growth_metric("", "Sales CAGR") is None
    assert parse_growth_metric(None, "Sales CAGR") is None
    assert parse_growth_metric("Unexpected Wording", "Sales CAGR") is None


def test_get_computed_value_growth_summary():
    """Test retrieving Sales/Profit CAGR from growth summary dataframe."""
    # Mock growth dataframe
    growth_data = {
        "Company": ["TCS", "INFY"],
        "Revenue_3Y": [12.0, 15.5],
        "Revenue_5Y": [10.5, 13.0],
        "PAT_10Y": [14.0, 16.0],
    }
    growth_df = pd.DataFrame(growth_data)
    mock_conn = MagicMock()

    # Sales CAGR 3Y
    val = get_computed_value("TCS", "Sales CAGR", 3, mock_conn, growth_df)
    assert val == 12.0

    # Sales CAGR 5Y
    val = get_computed_value("INFY", "Sales CAGR", 5, mock_conn, growth_df)
    assert val == 13.0

    # Profit CAGR 10Y
    val = get_computed_value("TCS", "Profit CAGR", 10, mock_conn, growth_df)
    assert val == 14.0

    # Missing column
    val = get_computed_value("TCS", "Sales CAGR", 10, mock_conn, growth_df)
    assert val is None


def test_get_computed_value_roe_db():
    """Test retrieving and averaging ROE values from database."""
    # Setup mock SQLite connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # DB returns: (return_on_equity_pct, year_str)
    mock_cursor.fetchall.return_value = [
        (15.0, "Mar 2024"),
        (16.0, "Mar 2023"),
        (14.0, "Mar 2022"),
        (17.0, "Mar 2021"),
    ]

    # 1 Year / Last Year (Latest ROE)
    val = get_computed_value("TCS", "ROE", 1, mock_conn, None)
    assert val == 15.0  # Mar 2024 is latest

    # 3 Year ROE Average
    # First 3 sorted descending: Mar 2024 (15.0), Mar 2023 (16.0), Mar 2022 (14.0)
    # Average = (15 + 16 + 14) / 3 = 15.0
    val = get_computed_value("TCS", "ROE", 3, mock_conn, None)
    assert val == 15.0

    # 5 Year ROE Average (only 4 available)
    # Average = (15 + 16 + 14 + 17) / 4 = 15.5
    val = get_computed_value("TCS", "ROE", 5, mock_conn, None)
    assert val == 15.5
