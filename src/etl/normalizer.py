import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

def normalize_year(val) -> str | None:
    """
    Standardizes a raw year/date input to the YYYY-MM format.
    
    Args:
        val: Raw input representing the financial/calendar year.
        
    Returns:
        str | None: The normalized YYYY-MM string, or None if parsing fails.
    """
    if val is None:
        return None
        
    # Convert to string and remove whitespace
    val_str = str(val).strip()
    if not val_str:
        return None
        
    # If it is already in the YYYY-MM format
    if re.match(r'^\d{4}-\d{2}$', val_str):
        parts = val_str.split('-')
        month = int(parts[1])
        if 1 <= month <= 12:
            return val_str
        return None

    # Handle float representation (e.g. 2023.0 -> "2023")
    try:
        float_val = float(val_str)
        if float_val.is_integer():
            val_str = str(int(float_val))
    except ValueError:
        pass

    # Remove 'FY' prefix (case-insensitive)
    val_str = re.sub(r'^fy\s*', '', val_str, flags=re.IGNORECASE)

    # 4-digit year alone (e.g., "2023") -> default to March ("2023-03")
    if re.match(r'^\d{4}$', val_str):
        return f"{val_str}-03"

    # 2-digit year alone (e.g., "23") -> default to March ("2023-03")
    if re.match(r'^\d{2}$', val_str):
        return f"20{val_str}-03"

    # Month name to two-digit string mapping
    months_map = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02',
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }

    # Match Month-Year (e.g., "Mar-23", "Mar 23", "March-2023", "Dec-22")
    m1 = re.match(r'^([a-zA-Z]+)[- ]+(\d{2,4})$', val_str)
    if m1:
        month_name = m1.group(1).lower()
        year_part = m1.group(2)
        if month_name in months_map:
            month_str = months_map[month_name]
            year_str = f"20{year_part}" if len(year_part) == 2 else year_part
            return f"{year_str}-{month_str}"

    # Match Year-Month (e.g., "2023-Mar", "23-Mar")
    m2 = re.match(r'^(\d{2,4})[- ]+([a-zA-Z]+)$', val_str)
    if m2:
        year_part = m2.group(1)
        month_name = m2.group(2).lower()
        if month_name in months_map:
            month_str = months_map[month_name]
            year_str = f"20{year_part}" if len(year_part) == 2 else year_part
            return f"{year_str}-{month_str}"

    # Log rejection for DQ-07 tracking
    logger.warning(f"Year parsing failed for raw value: '{val}'")
    return None

def normalize_ticker(val) -> str | None:
    """
    Standardizes a ticker symbol.
    
    Args:
        val: Raw input ticker symbol.
        
    Returns:
        str | None: The normalized ticker, or None if validation fails.
    """
    if val is None:
        return None
        
    ticker_str = str(val).strip().upper()
    if not ticker_str:
        return None
        
    # Validate length between 2 and 12 characters (DQ-08)
    if len(ticker_str) < 2 or len(ticker_str) > 12:
        logger.warning(f"Ticker validation failed (length out of bounds 2-12) for: '{val}'")
        return None
        
    # Validate allowed characters: alphanumeric, hyphen, and ampersand
    if not re.match(r'^[A-Z0-9\-&]+$', ticker_str):
        logger.warning(f"Ticker validation failed (invalid characters) for: '{val}'")
        return None
        
    return ticker_str
