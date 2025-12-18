from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from . import excel_ops, llm_service


# FastMCP instance that owns the tool registry for MCP clients.
server = FastMCP("excel-excel-mcp-server")


def _preview(df, limit: int = 5) -> List[Dict[str, Any]]:
    """Return a small preview of a DataFrame as list-of-dicts."""
    return df.head(limit).to_dict(orient="records")


@server.tool(name="clean_excel", description="Clean an Excel sheet by removing empty rows and trimming columns")
def clean_excel(path: str, sheet: str) -> Dict[str, Any]:
    """
    Load and clean an Excel worksheet.
    Returns cleaning summary statistics.
    """
    try:
        df = excel_ops.load_excel(path, sheet)
        cleaned, summary = excel_ops.clean_sheet(df)
        
        # Overwrite original sheet with cleaned data
        excel_ops.save_excel(cleaned, path, sheet_name=sheet)
        profile = excel_ops.profile_data(cleaned)
        
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": f"Sheet '{sheet}' cleaned successfully.",
        "profile": profile,
        "preview": _preview(cleaned),
        "cleaning_summary": summary 
    }


@server.tool(name="analyze_data", description="Analyze/Profile an Excel sheet for visualization")
def analyze_data(path: str, sheet: str) -> Dict[str, Any]:
    """
    Profile an Excel worksheet and return data suitable for visualization.
    """
    try:
        df = excel_ops.load_excel(path, sheet)
        # We can implement a more complex 'prepare_chart_data' here
        chart_data = excel_ops.prepare_chart_data(df)
        
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": f"Analyzed worksheet '{sheet}'.",
        "chart_data": chart_data,
    }


@server.tool(
    name="create_pivot_table",
    description="Create a pivot table from an Excel sheet and return a JSON preview. Supports cleaning column names.",
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
    Auto-corrects column names using LLM if needed.
    """
    try:
        df = excel_ops.load_excel(path, sheet)
        schema = list(df.columns.astype(str))
        
        # LLM Intelligent Correction
        normalized_index = llm_service.normalize_columns(index, schema)
        normalized_values = llm_service.normalize_columns(values, schema)
        
        pivot = excel_ops.create_pivot_table(
            df, 
            index=normalized_index, 
            values=normalized_values, 
            aggfunc=aggfunc
        )
    except ValueError as exc:
        return {"success": False, "message": str(exc)}

    return {
        "success": True,
        "message": "Pivot table created successfully.",
        "pivot_preview": _preview(pivot, limit=100), # Return larger preview for UI
        "pivot_rows": len(pivot),
        "index": normalized_index,
        "values": normalized_values,
        "aggfunc": aggfunc,
        "full_data": pivot.to_dict(orient="records"), # Send full data for UI table
    }


@server.tool(
    name="insert_excel_formula",
    description="Insert a formula into an Excel cell, supporting natural language intent.",
)
def insert_excel_formula(
    path: str, 
    sheet: str, 
    cell: str, 
    formula: Optional[str] = None, 
    intent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Insert an Excel formula. Can generate formula from 'intent' if 'formula' not provided.
    """
    try:
        if not formula and not intent:
            raise ValueError("Must provide either 'formula' or 'intent'.")

        if not formula and intent:
            # Load schema context
            df = excel_ops.load_excel(path, sheet)
            schema = list(df.columns.astype(str))
            
            generated = llm_service.generate_formula_from_intent(intent, schema, cell)
            if not generated:
                raise ValueError("Could not generate formula from intent.")
            formula = generated

        excel_ops.insert_formula(path, sheet, cell, formula)
    except Exception as exc: # Catching all exceptions from the attempt block
        return {"success": False, "message": str(exc)}
    
    # Try to calculate the value for display (Direct calculation, no LLM)
    # We parse the formula we just generated and execute it directly
    calculated_value = None
    try:
        # Load the data
        df = excel_ops.load_excel(path, sheet)
        
        # Parse the formula to extract function and column
        import re
        import pandas as pd
        
        # Extract function name and range from formula (e.g., "=AVERAGE(H2:H100)")
        formula_match = re.match(r'=([A-Z]+)\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)', formula)
        
        if formula_match:
            func_name = formula_match.group(1)
            col_letter = formula_match.group(2)
            
            # Convert column letter to index (A=0, B=1, etc.)
            col_index = ord(col_letter) - ord('A')
            
            if col_index < len(df.columns):
                column_data = df.iloc[:, col_index]
                
                # Apply the function
                if func_name == 'AVERAGE':
                    result = column_data.mean()
                elif func_name == 'SUM':
                    result = column_data.sum()
                elif func_name == 'COUNT':
                    result = column_data.count()
                elif func_name == 'MAX':
                    result = column_data.max()
                elif func_name == 'MIN':
                    result = column_data.min()
                else:
                    result = None
                
                if result is not None:
                    # Format the result nicely
                    if isinstance(result, (int, float)):
                        if isinstance(result, float):
                            calculated_value = f"{result:,.2f}"
                        else:
                            calculated_value = f"{result:,}"
                    else:
                        calculated_value = str(result)
        
        # Handle multiplication/division formulas (e.g., "=A2*B2")
        elif '*' in formula or '/' in formula:
            calculated_value = "Formula inserted (calculation requires specific row)"
            
    except Exception as e:
        # Show the error for debugging
        calculated_value = f"Error: {str(e)}"

    return {
        "success": True,
        "message": f"Inserted formula into {sheet}!{cell}.",
        "cell": cell,
        "formula": formula,
        "calculated_value": calculated_value
    }


@server.tool(name="query_data", description="Ask a natural language question about the Excel data")
def query_data(path: str, sheet: str, query: str) -> Dict[str, Any]:
    """
    Answer a natural language question about the data by generating and running python code.
    args:
        path: Absolute path to the excel file
        sheet_name: Name of the sheet to query
        query: User's question (e.g. "What is the average of Quantity?")
    """
    try:
        # 1. Load Data
        df = excel_ops.load_excel(path, sheet)
        schema = list(df.columns.astype(str))
        
        # 2. Generate Code
        # We need to access the new function in llm_service
        code_str = llm_service.generate_data_analysis_code(query, schema)
        
        # 3. Execute Code
        # We create a local scope with 'df' and 'pd'
        import pandas as pd
        local_scope = {"df": df, "pd": pd}
        
        try:
            # Dangerous in production, safe for local tool
            exec(code_str, {}, local_scope)
            
            # Check for result
            result = local_scope.get("result", "No 'result' variable found in generated code.")
            
            # Convert numpy types to python native
            if hasattr(result, "item"): 
                result = result.item()
            
            return {
                "success": True,
                "message": "Question answered successfully",
                "qa_result": str(result),
                "generated_code": code_str
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Execution Error: {str(e)}",
                "qa_result": f"Failed to execute code: {str(e)}",
                "generated_code": code_str
            }

    except Exception as e:
        return {"success": False, "message": str(e)}


