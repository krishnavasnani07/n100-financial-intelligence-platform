from src.etl.normalizer import normalize_year


def test_normalize_year_valid_yyyymm():
    assert normalize_year("2023-03") == "2023-03"


def test_normalize_year_valid_yyyymm_dec():
    assert normalize_year("2022-12") == "2022-12"


def test_normalize_year_whitespace_strip():
    assert normalize_year("  2023-03  ") == "2023-03"


def test_normalize_year_month_year_hyphen_short():
    assert normalize_year("Mar-23") == "2023-03"


def test_normalize_year_month_year_hyphen_full():
    assert normalize_year("December-2022") == "2022-12"


def test_normalize_year_month_year_space_short():
    assert normalize_year("Jun 23") == "2023-06"


def test_normalize_year_month_year_space_full():
    assert normalize_year("March 2023") == "2023-03"


def test_normalize_year_year_month_hyphen():
    assert normalize_year("2023-Mar") == "2023-03"


def test_normalize_year_year_month_space():
    assert normalize_year("23 Dec") == "2023-12"


def test_normalize_year_fy_prefix_no_space():
    assert normalize_year("FY23") == "2023-03"


def test_normalize_year_fy_prefix_space():
    assert normalize_year("fy 2025") == "2025-03"


def test_normalize_year_integer_input():
    assert normalize_year(2023) == "2023-03"


def test_normalize_year_float_input():
    assert normalize_year(2022.0) == "2022-03"


def test_normalize_year_float_string():
    assert normalize_year("2023.0") == "2023-03"


def test_normalize_year_invalid_month_oob():
    assert normalize_year("2023-13") is None


def test_normalize_year_invalid_month_zero():
    assert normalize_year("2023-00") is None


def test_normalize_year_garbage_text():
    assert normalize_year("garbage") is None


def test_normalize_year_empty_string():
    assert normalize_year("") is None


def test_normalize_year_none_input():
    assert normalize_year(None) is None


def test_normalize_year_too_short():
    assert normalize_year("2") is None
