import pytest
from src.etl.normalizer import normalize_ticker


@pytest.mark.parametrize(
    "raw_input, expected_output",
    [
        # Clean uppercase tickers
        ("TCS", "TCS"),
        ("RELIANCE", "RELIANCE"),
        ("INFY", "INFY"),
        ("SBIN", "SBIN"),
        ("HDFCBANK", "HDFCBANK"),
        # Case normalization
        ("tcs", "TCS"),
        ("reliance", "RELIANCE"),
        ("tCs", "TCS"),
        ("hdfcbank", "HDFCBANK"),
        # Whitespace, tab, newline stripping
        (" tcs ", "TCS"),
        ("  RELIANCE  ", "RELIANCE"),
        ("\tINFY\n", "INFY"),
        # Allowed special symbols (hyphen & ampersand)
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        ("M&M", "M&M"),
        ("m&m", "M&M"),
        ("L&T", "L&T"),
        # Length validation: Too short (<2 chars)
        ("A", None),
        ("a", None),
        # Length validation: Too long (>12 chars)
        ("ABCDEFGHIJKLM", None),
        ("ABC-DEF-GHI-JKL", None),
        # Disallowed characters / suffixes
        ("TCS.NS", None),
        ("TCS.BO", None),
        ("RELIANCE#", None),
        ("INFY$", None),
        # Empty and null values
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_normalize_ticker_cases(raw_input, expected_output):
    assert normalize_ticker(raw_input) == expected_output
