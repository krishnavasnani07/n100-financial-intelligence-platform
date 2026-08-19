from pathlib import Path

from src.config.settings import DB_PATH
from src.reports.report_utils import check_eligibility, map_sector, validate_pdf


def test_sector_mapping():
    """Verify standard sectors map correctly to the 11 target groupings."""
    # IT Services
    assert map_sector("Information Technology", "IT Services") == "IT Services"
    assert map_sector("Information Technology", "Software") == "IT Services"

    # Banking
    assert map_sector("Financials", "Private Banks") == "Banking"
    assert map_sector("Financials", "Consumer Finance") == "Banking"

    # Healthcare
    assert map_sector("Healthcare", "Pharmaceuticals") == "Healthcare"

    # Utilities split from Energy
    assert map_sector("Energy", "Power & Utilities") == "Utilities"
    assert map_sector("Energy", "Power Transmission") == "Utilities"
    assert map_sector("Energy", "Renewable Energy") == "Utilities"

    # Energy unchanged
    assert map_sector("Energy", "Oil & Gas Exploration") == "Energy"
    assert map_sector("Energy", "Oil & Gas Refining") == "Energy"

    # Other sectors unchanged
    assert map_sector("Materials", "Cement") == "Materials"
    assert map_sector("Real Estate", "Real Estate") == "Real Estate"


def test_company_eligibility():
    """Verify data eligibility filters correctly flags short histories."""
    # TCS has full 10-year history
    eligible, reason = check_eligibility("TCS", DB_PATH)
    assert eligible is True
    assert reason == ""

    # JIOFIN has only 2 years of cash flow data
    eligible, reason = check_eligibility("JIOFIN", DB_PATH)
    assert eligible is False
    assert "Less than 3 years of financial data" in reason
    assert "cashflow" in reason


def test_pdf_validation_missing_file():
    """Verify that validator catches missing PDF files."""
    dummy_path = Path("reports/tearsheets/nonexistent_company_report.pdf")
    valid, msg = validate_pdf(dummy_path)
    assert valid is False
    assert "File does not exist" in msg


def test_sector_report_generation(tmp_path):
    """Test generating sector reports and validating them."""
    from src.reports.sector_report import generate_all_sector_reports

    # Generate reports to the temp path
    generate_all_sector_reports(db_path=DB_PATH, out_dir=tmp_path)

    # Check that sector PDFs were created
    pdf_files = list(tmp_path.glob("*.pdf"))
    assert len(pdf_files) > 0, "No sector reports were generated"

    # Validate each generated PDF
    for pdf_file in pdf_files:
        valid, msg = validate_pdf(pdf_file, min_size_kb=4.0)
        assert valid is True, f"PDF {pdf_file.name} failed validation: {msg}"
