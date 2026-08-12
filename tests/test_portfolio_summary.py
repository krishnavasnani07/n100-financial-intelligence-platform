import pytest
from pathlib import Path
import sys

# Insert project base path to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.reports.portfolio_summary import generate_portfolio_summary_report
from src.utils.helpers import extract_year_int
from src.reports.generate_sample_reports import count_pdf_pages
from src.config.settings import DB_PATH


def test_extract_year_int():
    """Verify that extract_year_int correctly extracts year digits."""
    assert extract_year_int("Mar 2024") == 2024
    assert extract_year_int("Dec 2012") == 2012
    assert extract_year_int("TTM") is None
    assert extract_year_int(None) is None
    assert extract_year_int("FY 2021") == 2021


def test_generate_portfolio_summary_success():
    """Test generating the master portfolio summary report on default DB."""
    pdf_path = generate_portfolio_summary_report(DB_PATH)

    # 1. Verify file exists
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"

    # 2. Verify page count is exactly 92
    pages = count_pdf_pages(pdf_path)
    assert pages == 92, f"Expected 92 pages, got {pages}"
