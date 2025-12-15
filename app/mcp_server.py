from __future__ import annotations

from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

from . import excel_ops


# FastMCP instance that owns the tool registry for MCP clients.
server = FastMCP("excel-excel-mcp-server")


def _preview(df, limit: int = 5) -> List[Dict[str, Any]]:
    """Return a small preview of a DataFrame as list-of-dicts."""

    return df.head(limit).to_dict(orient="records")


@server.tool(name="clean_excel", description="Clean an Excel sheet by removing empty rows and trimming columns")
def clean_excel(path: str, sheet: str) -> Dict[str, Any]:
    """
    Load and clean an Excel worksheet.

    This tool:
    - loads the given sheet
    - drops empty rows
    - normalises column names
    - attempts dtype normalisation
    """

    try:
        df = excel_ops.load_excel(path, sheet)
        cleaned = excel_ops.clean_sheet(df)
        # Overwrite original sheet with cleaned data for deterministic behaviour
        excel_ops.save_excel(cleaned, path, sheet_name=sheet)
        profile = excel_ops.profile_data(cleaned)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": f"Sheet '{sheet}' cleaned successfully.",
        "profile": profile,
        "preview": _preview(cleaned),
    }


@server.tool(name="profile_excel", description="Profile an Excel sheet and return metadata")
def profile_excel(path: str, sheet: str) -> Dict[str, Any]:
    """
    Profile an Excel worksheet.

    Returns:
    - row / column counts
    - columns
    - null counts
    """

    try:
        df = excel_ops.load_excel(path, sheet)
        profile = excel_ops.profile_data(df)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": f"Profiled worksheet '{sheet}'.",
        "profile": profile,
        "preview": _preview(df),
    }


@server.tool(
    name="create_pivot_table",
    description="Create a pivot table from an Excel sheet and return a JSON preview",
)
def create_pivot_table(
    path: str,
    sheet: str,
    index: List[str],
    values: List[str],
    aggfunc: str = "sum",
) -> Dict[str, Any]:
    """
    Create a pivot table for the given worksheet.

    The pivot table is NOT written back to Excel; instead it is returned as JSON.
    """

    try:
        df = excel_ops.load_excel(path, sheet)
        pivot = excel_ops.create_pivot_table(df, index=index, values=values, aggfunc=aggfunc)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": "Pivot table created successfully.",
        "pivot_preview": _preview(pivot),
        "pivot_rows": len(pivot),
        "index": index,
        "values": values,
        "aggfunc": aggfunc,
    }


@server.tool(
    name="insert_excel_formula",
    description="Insert a formula into an Excel cell",
)
def insert_excel_formula(path: str, sheet: str, cell: str, formula: str) -> Dict[str, Any]:
    """
    Insert an Excel formula into a specific cell.

    Example:
    - cell=\"D2\", formula=\"=B2*C2\"
    """

    try:
        excel_ops.insert_formula(path, sheet, cell, formula)
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": f"Inserted formula into {sheet}!{cell}.",
        "cell": cell,
        "formula": formula,
    }


