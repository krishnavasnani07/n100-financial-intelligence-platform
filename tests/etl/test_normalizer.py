import pytest
from src.etl.normalizer import normalize_year, normalize_ticker

# --- Test Cases for normalize_year() ---
@pytest.mark.parametrize("raw_input, expected_output", [
    # Standard format
    ("2023-03", "2023-03"),
    ("2022-12", "2022-12"),
    
    # Month-Year formats (hyphen separator)
    ("Mar-23", "2023-03"),
    ("Dec-22", "2022-12"),
    ("Jun-23", "2023-06"),
    ("Jan-21", "2021-01"),
    ("Sep-20", "2020-09"),
    
    # Month-Year formats (space separator)
    ("Mar 23", "2023-03"),
    ("Dec 22", "2022-12"),
    ("Jun 23", "2023-06"),
    
    # Full month names
    ("March-2023", "2023-03"),
    ("December-2022", "2022-12"),
    ("June-2023", "2023-06"),
    
    # Financial Year prefix (FY)
    ("FY23", "2023-03"),
    ("fy22", "2022-03"),
    ("FY 24", "2024-03"),
    ("fy 2025", "2025-03"),
    
    # Standalone years (defaults to March financial year end)
    ("2023", "2023-03"),
    ("2022", "2022-03"),
    (2023, "2023-03"),        # Integer input
    (2022.0, "2022-03"),      # Float input
    ("2023.0", "2023-03"),    # Float string input
    
    # Out of bounds or invalid months
    ("2023-13", None),
    ("2023-00", None),
    
    # Invalid or garbage inputs (should return None to be rejected by validation)
    ("garbage", None),
    ("", None),
    ("   ", None),
    (None, None),
    ("Mar-20234", None),
    ("123", None),
])
def test_normalize_year(raw_input, expected_output):
    assert normalize_year(raw_input) == expected_output


# --- Test Cases for normalize_ticker() ---
@pytest.mark.parametrize("raw_input, expected_output", [
    # Exact match / clean
    ("TCS", "TCS"),
    ("RELIANCE", "RELIANCE"),
    
    # Case normalization
    ("tcs", "TCS"),
    ("reliance", "RELIANCE"),
    ("hdfcbank", "HDFCBANK"),
    
    # Whitespace stripping
    (" tcs ", "TCS"),
    ("  RELIANCE  ", "RELIANCE"),
    ("\tINFY\n", "INFY"),
    
    # Hyphens and special characters allowed
    ("BAJAJ-AUTO", "BAJAJ-AUTO"),
    ("bajaj-auto", "BAJAJ-AUTO"),
    ("M&M", "M&M"),
    ("m&m", "M&M"),
    ("L&T", "L&T"),
    
    # Length validation: Too short (less than 2 chars)
    ("A", None),
    ("a", None),
    
    # Length validation: Too long (greater than 12 chars)
    ("ABCDEFGHIJKLM", None),       # 13 characters
    ("ABC-DEF-GHI-JKL", None),   # 15 characters
    
    # Invalid characters (exchange suffixes not supported by default, or special chars)
    ("TCS.NS", None),             # contains dot
    ("TCS.BO", None),             # contains dot
    ("RELIANCE#", None),          # contains hash
    ("INFY$", None),              # contains dollar
    
    # Empty / null inputs
    ("", None),
    ("   ", None),
    (None, None),
])
def test_normalize_ticker(raw_input, expected_output):
    assert normalize_ticker(raw_input) == expected_output
