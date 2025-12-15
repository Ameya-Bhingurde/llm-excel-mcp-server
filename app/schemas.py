from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExcelRequestBase(BaseModel):
    path: str = Field(..., description="Relative path to the Excel file inside sample_files")
    sheet: str = Field(..., description="Worksheet name")


class CleanExcelRequest(ExcelRequestBase):
    pass


class ProfileExcelRequest(ExcelRequestBase):
    pass


class PivotTableRequest(ExcelRequestBase):
    index: List[str] = Field(..., description="Columns to use as pivot index")
    values: List[str] = Field(..., description="Columns to aggregate")
    aggfunc: str = Field(default="sum", description="Aggregation function (sum, mean, count)")


class InsertFormulaRequest(ExcelRequestBase):
    cell: str = Field(..., description="Cell reference such as 'D2'")
    formula: str = Field(..., description="Excel formula string, e.g. '=A1+B1'")


class ExcelOperationResponse(BaseModel):
    success: bool
    message: str
    data_preview: Optional[list[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    app: str


