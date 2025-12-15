from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .mcp_server import clean_excel, profile_excel, create_pivot_table, insert_excel_formula
from .schemas import (
    CleanExcelRequest,
    ExcelOperationResponse,
    HealthResponse,
    InsertFormulaRequest,
    PivotTableRequest,
    ProfileExcelRequest,
)
from .utils import ensure_path_within_workspace, init_logging


settings = get_settings()
init_logging()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LLM-driven Excel Automation MCP Server built with FastAPI.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Simple health check used by Render and local diagnostics."""

    return HealthResponse(status="ok", app=settings.app_name)


@app.post("/mcp/clean-excel", response_model=ExcelOperationResponse)
def clean_excel_endpoint(payload: CleanExcelRequest) -> ExcelOperationResponse:
    """HTTP wrapper around the MCP `clean_excel` tool."""

    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = clean_excel(str(path), payload.sheet)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        data_preview=result.get("preview"),
        metadata={"profile": result.get("profile")},
    )


@app.post("/mcp/profile-excel", response_model=ExcelOperationResponse)
def profile_excel_endpoint(payload: ProfileExcelRequest) -> ExcelOperationResponse:
    """HTTP wrapper around the MCP `profile_excel` tool."""

    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = profile_excel(str(path), payload.sheet)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        data_preview=result.get("preview"),
        metadata={"profile": result.get("profile")},
    )


@app.post("/mcp/create-pivot-table")
def create_pivot_table_endpoint(payload: PivotTableRequest) -> JSONResponse:
    """HTTP wrapper around the MCP `create_pivot_table` tool."""

    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = create_pivot_table(
        str(path),
        payload.sheet,
        index=payload.index,
        values=payload.values,
        aggfunc=payload.aggfunc,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return JSONResponse(result)


@app.post("/mcp/insert-formula", response_model=ExcelOperationResponse)
def insert_formula_endpoint(payload: InsertFormulaRequest) -> ExcelOperationResponse:
    """HTTP wrapper around the MCP `insert_excel_formula` tool."""

    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = insert_excel_formula(
        str(path),
        payload.sheet,
        payload.cell,
        payload.formula,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        data_preview=None,
        metadata={"cell": result.get("cell"), "formula": result.get("formula")},
    )

