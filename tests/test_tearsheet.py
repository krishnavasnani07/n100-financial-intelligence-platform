import pytest
from pathlib import Path
import sys

# Insert project base path to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.reports.tearsheet import generate_tearsheet
from src.reports.generate_sample_reports import count_pdf_pages


def test_generate_tearsheet_success():
    """Test generating tearsheet for a valid company ticker."""
    company_id = "TCS"
    pdf_path = generate_tearsheet(company_id)

    # 1. Verify file exists
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"

    # 2. Verify page count is exactly 2
    pages = count_pdf_pages(pdf_path)
    assert pages == 2, f"Expected 2 pages for {company_id}, got {pages}"


def test_generate_tearsheet_invalid_company():
    """Test that generating tearsheet for an invalid ticker raises ValueError."""
    with pytest.raises(ValueError):
        generate_tearsheet("INVALID_TICKER")


def test_count_pdf_pages_invalid_path():
    """Test count_pdf_pages handles invalid path gracefully."""
    pages = count_pdf_pages(Path("non_existent_file.pdf"))
    assert pages == -1
