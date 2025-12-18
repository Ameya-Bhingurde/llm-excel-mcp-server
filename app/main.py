from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .mcp_server import clean_excel, analyze_data, create_pivot_table, insert_excel_formula
from .schemas import (
    CleanExcelRequest,
    ExcelOperationResponse,
    HealthResponse,
    InsertFormulaRequest,
    PivotTableRequest,
    AnalyzeDataRequest,
    QueryDataRequest,
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
    return HealthResponse(status="ok", app=settings.app_name)


@app.get("/")
def root():
    return {
        "message": "LLM Excel MCP Server is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "clean_excel": "/mcp/clean-excel",
            "analyze_data": "/mcp/analyze-data",
            "create_pivot": "/mcp/create-pivot-table",
            "insert_formula": "/mcp/insert-formula",
            "query_data": "/mcp/query-data"
        }
    }



@app.post("/mcp/clean-excel", response_model=ExcelOperationResponse)
def clean_excel_endpoint(payload: CleanExcelRequest) -> ExcelOperationResponse:
    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = clean_excel(str(path), payload.sheet)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        data_preview=result.get("preview"),
        metadata={"profile": result.get("profile")},
        cleaning_summary=result.get("cleaning_summary")
    )


@app.post("/mcp/analyze-data", response_model=ExcelOperationResponse)
def analyze_data_endpoint(payload: AnalyzeDataRequest) -> ExcelOperationResponse:
    path = ensure_path_within_workspace(payload.path)

    result: Dict[str, Any] = analyze_data(str(path), payload.sheet)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        chart_data=result.get("chart_data")
    )


@app.post("/mcp/create-pivot-table")
def create_pivot_table_endpoint(payload: PivotTableRequest) -> JSONResponse:
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
    path = ensure_path_within_workspace(payload.path)

    # Allow intent OR formula
    result: Dict[str, Any] = insert_excel_formula(
        str(path),
        payload.sheet,
        payload.cell,
        payload.formula,
        payload.intent
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        data_preview=None,
        metadata={
            "cell": result.get("cell"), 
            "formula": result.get("formula"),
            "calculated_value": result.get("calculated_value")
        },
    )


@app.post("/mcp/query-data", response_model=ExcelOperationResponse)
def query_data_endpoint(payload: QueryDataRequest) -> ExcelOperationResponse:
    path = ensure_path_within_workspace(payload.path)

    # We need to import query_data from mcp_server inside here or at top
    # Avoiding circular imports or just ensuring it's available.
    # It is in mcp_server.py which we import at top.
    # But we need to update the import list in main.py first.
    # I will do that via a separate edit or just assume I can add it to the import line?
    # No, I can't edit the import line in this chunk. I will assume it is imported or I will import it inside.
    
    from .mcp_server import query_data as mcp_query_data
    
    result: Dict[str, Any] = mcp_query_data(str(path), payload.sheet, payload.query)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unknown error"))

    return ExcelOperationResponse(
        success=True,
        message=result["message"],
        qa_result=result.get("qa_result")
    )
