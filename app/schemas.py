from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ExcelRequestBase(BaseModel):
    path: str = Field(..., description="Relative path to the Excel file inside sample_files")
    sheet: str = Field(..., description="Worksheet name")


class CleanExcelRequest(ExcelRequestBase):
    pass


class ProfileExcelRequest(ExcelRequestBase):
    pass
    
class AnalyzeDataRequest(ExcelRequestBase):
    pass


class PivotTableRequest(ExcelRequestBase):
    index: List[str] = Field(..., description="Columns to use as pivot index")
    values: List[str] = Field(..., description="Columns to aggregate")
    aggfunc: str = Field(default="sum", description="Aggregation function (sum, mean, count)")


class InsertFormulaRequest(ExcelRequestBase):
    cell: str = Field(..., description="Cell reference such as 'D2'")
    formula: Optional[str] = Field(None, description="Explicit Excel formula")
    intent: Optional[str] = Field(None, description="Natural language intent to generate formula")


class QueryDataRequest(ExcelRequestBase):
    query: str = Field(..., description="Natural language question about the data")


class ExcelOperationResponse(BaseModel):
    success: bool
    message: str
    data_preview: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    # Enhanced fields for "Smart" UI
    cleaning_summary: Optional[Dict[str, Any]] = None  # For Clean Tool
    chart_data: Optional[Dict[str, Any]] = None        # For Analyze Tool
    qa_result: Optional[str] = None                    # For Query Tool


class HealthResponse(BaseModel):
    status: str
    app: str
