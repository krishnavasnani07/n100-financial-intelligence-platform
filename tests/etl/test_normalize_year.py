import pytest
from src.etl.normalizer import normalize_year


@pytest.mark.parametrize(
    "raw_input, expected_output",
    [
        # Standard YYYY-MM
        ("2023-03", "2023-03"),
        ("2022-12", "2022-12"),
        # Month-Year formats with hyphens
        ("Mar-23", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("Jan-21", "2021-01"),
        ("Sep-20", "2020-09"),
        # Month-Year formats with spaces
        ("Mar 23", "2023-03"),
        ("Dec 22", "2022-12"),
        ("Jun 23", "2023-06"),
        # Full month names
        ("March-2023", "2023-03"),
        ("December-2022", "2022-12"),
        ("June-2023", "2023-06"),
        ("March 2023", "2023-03"),
        # Financial Year prefixes
        ("FY23", "2023-03"),
        ("fy22", "2022-03"),
        ("FY 24", "2024-03"),
        ("fy 2025", "2025-03"),
        # Standalone numeric years
        ("2023", "2023-03"),
        ("2022", "2022-03"),
        (2023, "2023-03"),
        (2022.0, "2022-03"),
        ("2023.0", "2023-03"),
        # Out of bounds / invalid months
        ("2023-13", None),
        ("2023-00", None),
        # Empty and invalid inputs
        ("garbage", None),
        ("", None),
        ("   ", None),
        (None, None),
        ("Mar-20234", None),
        ("123", None),
    ],
)
def test_normalize_year_cases(raw_input, expected_output):
    assert normalize_year(raw_input) == expected_output
