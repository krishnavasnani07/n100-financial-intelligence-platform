import pytest
import pandas as pd
from pathlib import Path
from src.etl.loader import ExcelLoader, load_excel

@pytest.fixture
def temp_excel_file(tmp_path):
    """Creates a temporary Excel file for testing in isolation."""
    data = {
        "Ticker": ["TCS", "INFY", "M&M"],
        "Year": ["Mar-23", "2023", "Dec-22"],
        "Value": [100, 200, 300],
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_data.xlsx"
    df.to_excel(file_path, index=False, engine="openpyxl")
    return file_path

def test_load_excel_success(temp_excel_file):
    loader = ExcelLoader()
    df = loader.load_excel(temp_excel_file)
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 3)
    assert list(df.columns) == ["Ticker", "Year", "Value"]
    assert df.iloc[0]["Ticker"] == "TCS"

def test_load_excel_file_not_found():
    loader = ExcelLoader()
    df = loader.load_excel(Path("data/raw/does_not_exist_file.xlsx"))
    assert df is None

def test_load_excel_wrong_extension(tmp_path):
    txt_file = tmp_path / "invalid_file.txt"
    txt_file.write_text("dummy content")
    loader = ExcelLoader()
    assert loader.validate_extension(txt_file) is False
    assert loader.load_excel(txt_file) is None

def test_load_excel_empty_file(tmp_path):
    empty_df = pd.DataFrame()
    empty_file = tmp_path / "empty.xlsx"
    empty_df.to_excel(empty_file, index=False, engine="openpyxl")

    loader = ExcelLoader()
    df = loader.load_excel(empty_file)
    assert df is None

def test_load_excel_missing_required_columns(temp_excel_file):
    loader = ExcelLoader()
    # "NonExistentCol" does not exist in temp_excel_file
    df = loader.load_excel(
        temp_excel_file, required_columns=["Ticker", "NonExistentCol"]
    )
    assert df is None

def test_load_excel_corrupt_file(tmp_path):
    corrupt_file = tmp_path / "corrupt.xlsx"
    corrupt_file.write_bytes(b"This is not a valid zip or excel file binary data")

    loader = ExcelLoader()
    df = loader.load_excel(corrupt_file)
    assert df is None

def test_load_all_files(tmp_path):
    d1 = pd.DataFrame([{"id": "TCS", "name": "Tata"}])
    f1 = tmp_path / "companies.xlsx"
    d1.to_excel(f1, index=False, engine="openpyxl")

    loader = ExcelLoader()
    mappings = {"companies.xlsx": (0, 0, "companies")}
    datasets = loader.load_all_files(tmp_path, mappings)

    assert "companies" in datasets
    assert len(datasets["companies"]) == 1

def test_load_excel_backward_compatibility(temp_excel_file):
    df = load_excel(temp_excel_file)
    assert df is not None
    assert len(df) == 3

def test_load_excel_sheet_by_name(tmp_path):
    file_path = tmp_path / "multi_sheet.xlsx"
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        pd.DataFrame({"A": [1]}).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame({"B": [2, 3]}).to_excel(writer, sheet_name="Sheet2", index=False)
    
    loader = ExcelLoader()
    df = loader.load_excel(file_path, sheet_name="Sheet2")
    assert df is not None
    assert list(df.columns) == ["B"]
    assert len(df) == 2

def test_load_excel_header_custom(tmp_path):
    file_path = tmp_path / "header_test.xlsx"
    # Row 0: dummy label
    # Row 1: actual headers
    # Row 2: data
    df_raw = pd.DataFrame([
        ["Title Row", None],
        ["Col1", "Col2"],
        [10, 20]
    ])
    df_raw.to_excel(file_path, header=False, index=False, engine="openpyxl")
    
    loader = ExcelLoader()
    df = loader.load_excel(file_path, header=1)
    assert df is not None
    assert list(df.columns) == ["Col1", "Col2"]
    assert df.iloc[0]["Col1"] == 10
