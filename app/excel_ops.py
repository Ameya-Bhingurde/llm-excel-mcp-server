from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from openpyxl import load_workbook


def load_excel(path: str | Path, sheet_name: str) -> pd.DataFrame:
    """
    Load an Excel worksheet into a pandas DataFrame.

    Raises a ValueError with a human-readable message on error.
    """

    path = Path(path)
    if not path.exists():
        raise ValueError(f"Excel file not found at '{path}'.")

    try:
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except ValueError as exc:
        # pandas uses ValueError when sheet is missing
        raise ValueError(f"Worksheet '{sheet_name}' not found in '{path.name}'.") from exc
    except Exception as exc:  # pragma: no cover - catch-all for safety
        raise ValueError(f"Failed to load Excel file: {exc}") from exc
    return df


def clean_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a DataFrame representing an Excel sheet.

    - Drop fully empty rows
    - Strip whitespace from column names
    - Try to infer better dtypes
    """

    if df.empty:
        return df

    # Drop rows that are entirely NaN
    cleaned = df.dropna(how="all")

    # Normalise column names
    cleaned = cleaned.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)

    # Let pandas try to infer numeric / datetime types
    cleaned = cleaned.convert_dtypes()
    return cleaned


def profile_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Produce a light-weight profile of the DataFrame.

    Returns row count, column list, and per-column null counts.
    """

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns.astype(str)),
        "null_counts": {str(col): int(df[col].isna().sum()) for col in df.columns},
    }


def create_pivot_table(
    df: pd.DataFrame,
    index: List[str],
    values: List[str],
    aggfunc: str = "sum",
) -> pd.DataFrame:
    """
    Create a pivot table from the given DataFrame.

    Supported aggregation functions are: sum, mean, count.
    """

    supported_agg = {"sum", "mean", "count"}
    if aggfunc not in supported_agg:
        raise ValueError(f"Unsupported aggfunc '{aggfunc}'. Use one of {sorted(supported_agg)}.")

    missing_index = [col for col in index if col not in df.columns]
    missing_values = [col for col in values if col not in df.columns]
    if missing_index or missing_values:
        raise ValueError(
            f"Missing columns - index: {missing_index or 'OK'}, values: {missing_values or 'OK'}"
        )

    pivot = pd.pivot_table(
        df,
        index=index,
        values=values,
        aggfunc=aggfunc,
    ).reset_index()
    return pivot


def insert_formula(path: str | Path, sheet: str, cell: str, formula: str) -> None:
    """
    Insert a formula into a specific cell in an Excel worksheet.

    This modifies the workbook in-place.
    """

    path = Path(path)
    if not path.exists():
        raise ValueError(f"Excel file not found at '{path}'.")

    try:
        wb = load_workbook(path)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"Failed to open workbook: {exc}") from exc

    if sheet not in wb.sheetnames:
        raise ValueError(f"Worksheet '{sheet}' not found in '{path.name}'.")

    ws = wb[sheet]
    ws[cell] = formula
    wb.save(path)


def save_excel(df: pd.DataFrame, path: str | Path, sheet_name: str = "Sheet1") -> None:
    """
    Save a DataFrame back to an Excel file.

    Overwrites the file at the given path.
    """

    path = Path(path)
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"Failed to save Excel file: {exc}") from exc


