from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelLoader:
    """
    Robust Excel data loading class with validation for existence, extensions, readability, non-emptiness, and required columns.
    """

    ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

    def validate_file(self, file_path: Path | str) -> bool:
        """
        Verifies that the target file exists and is a regular readable file.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(
                f"File verification failed. File does not exist: {path.resolve()}"
            )
            return False
        if not path.is_file():
            logger.error(
                f"File verification failed. Path is not a file: {path.resolve()}"
            )
            return False
        return True

    def validate_extension(self, file_path: Path | str) -> bool:
        """
        Verifies that the target file has an allowed Excel extension (.xlsx, .xls).
        """
        path = Path(file_path)
        if path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            logger.error(
                f"Extension validation failed for '{path.name}'. Extension '{path.suffix}' not in allowed list {self.ALLOWED_EXTENSIONS}."
            )
            return False
        return True

    def validate_required_columns(
        self, df: pd.DataFrame, required_columns: list[str]
    ) -> bool:
        """
        Verifies that all specified required columns exist in the DataFrame.
        """
        if df is None:
            return False
        clean_cols = [str(c).strip().lower() for c in df.columns]
        missing = [
            req
            for req in required_columns
            if str(req).strip().lower() not in clean_cols
        ]
        if missing:
            logger.error(f"Required columns missing in dataset: {missing}")
            return False
        return True

    def load_excel(
        self,
        file_path: Path | str,
        sheet_name: str | int = 0,
        required_columns: list[str] | None = None,
        **kwargs,
    ) -> pd.DataFrame | None:
        """
        Safely loads an Excel file into a pandas DataFrame with validation and logging.
        """
        path = Path(file_path)
        logger.info(f"Loading '{path.name}' (Target path: {path.resolve()})")

        if not self.validate_file(path):
            return None

        if not self.validate_extension(path):
            return None

        try:
            df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", **kwargs)

            if df is None or df.empty:
                logger.warning(f"File '{path.name}' loaded but is empty.")
                return None

            if required_columns and not self.validate_required_columns(
                df, required_columns
            ):
                logger.error(
                    f"Validation failed for required columns in '{path.name}'."
                )
                return None

            logger.info(
                f"SUCCESS Loaded {len(df)} rows from '{path.name}' (Shape: {df.shape})"
            )
            return df
        except Exception as e:
            logger.error(
                f"Exception occurred while loading Excel file '{path.name}': {e!s}",
                exc_info=True,
            )
            return None

    def load_all_files(
        self, data_dir: Path | str, file_mappings: dict[str, Any]
    ) -> dict[str, pd.DataFrame]:
        """
        Batch loads multiple Excel files according to a mapping dictionary.
        Returns a mapping of dataset keys to DataFrames.
        """
        target_dir = Path(data_dir)
        loaded_datasets: dict[str, pd.DataFrame] = {}

        for filename, config in file_mappings.items():
            if isinstance(config, tuple):
                sheet_name = config[0]
                header = config[1] if len(config) > 1 else 0
                key = config[2] if len(config) > 2 else filename.split(".")[0]
            else:
                sheet_name = 0
                header = 0
                key = filename.split(".")[0]

            file_path = target_dir / filename
            df = self.load_excel(file_path, sheet_name=sheet_name, header=header)
            if df is not None:
                loaded_datasets[key] = df

        return loaded_datasets


# Top-level standalone function for backward compatibility
def load_excel(file_path: Path | str, sheet_name=0, **kwargs) -> pd.DataFrame | None:
    """Load excel."""
    loader = ExcelLoader()
    return loader.load_excel(file_path, sheet_name=sheet_name, **kwargs)
