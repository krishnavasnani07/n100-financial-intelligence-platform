import pytest
import pandas as pd
from pathlib import Path
from src.etl.loader import load_excel

@pytest.fixture
def temp_excel_file(tmp_path):
    """
    Creates a temporary Excel file for testing the loader in isolation.
    """
    data = {
        "Ticker": ["TCS", "INFY", "M&M"],
        "Year": ["Mar-23", "2023", "Dec-22"],
        "Value": [100, 200, 300]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_data.xlsx"
    df.to_excel(file_path, index=False, engine='openpyxl')
    return file_path

def test_load_excel_success(temp_excel_file):
    """
    Tests that a valid Excel file is loaded correctly.
    """
    df = load_excel(temp_excel_file)
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 3)
    assert list(df.columns) == ["Ticker", "Year", "Value"]
    assert df.iloc[0]["Ticker"] == "TCS"

def test_load_excel_file_not_found():
    """
    Tests that requesting a non-existent file returns None.
    """
    non_existent_path = Path("data/raw/does_not_exist_file.xlsx")
    df = load_excel(non_existent_path)
    assert df is None

def test_load_excel_is_directory(tmp_path):
    """
    Tests that passing a directory path instead of a file returns None.
    """
    df = load_excel(tmp_path)
    assert df is None

def test_load_excel_real_file_integration():
    """
    Integration test: verify the loader can read one of the actual raw Excel files.
    """
    real_file_path = Path("data/raw/companies.xlsx")
    # Skip if the raw data files are not present in the current test environment
    if real_file_path.exists():
        df = load_excel(real_file_path)
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0
