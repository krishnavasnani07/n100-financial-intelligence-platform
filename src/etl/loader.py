import os
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

def load_excel(file_path: Path | str, sheet_name=0, **kwargs) -> pd.DataFrame | None:
    """
    Safely reads an Excel file into a pandas DataFrame.
    
    Verifies file existence, handles exceptions gracefully, and logs status/metrics.
    
    Args:
        file_path (Path | str): Absolute or relative path to the Excel file.
        sheet_name (int | str): Sheet index or sheet name to parse. Defaults to 0.
        **kwargs: Additional parameters to pass to pandas.read_excel().
        
    Returns:
        pd.DataFrame | None: The loaded DataFrame, or None if loading failed.
    """
    path = Path(file_path)
    logger.info(f"Initiating load for Excel file: '{path.name}' (Target path: {path.resolve()})")
    
    if not path.exists():
        logger.error(f"File verification failed. File does not exist: {path.resolve()}")
        return None
        
    if not path.is_file():
        logger.error(f"File verification failed. Path is not a file: {path.resolve()}")
        return None
        
    try:
        # Load the sheet using openpyxl engine by default
        df = pd.read_excel(path, sheet_name=sheet_name, engine='openpyxl', **kwargs)
        logger.info(f"Successfully parsed Excel file: '{path.name}'. Shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Exception occurred while loading Excel file '{path.name}': {str(e)}", exc_info=True)
        return None
