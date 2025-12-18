import re
import json
import logging
import httpx
from typing import List, Optional, Dict, Any
from .config import get_settings

logger = logging.getLogger("llm_excel_mcp")
settings = get_settings()

def _clean_json_response(response: str) -> str:
    """
    Robust cleaning of LLM response to ensure valid JSON.
    Removes markdown code blocks, explanatory text, etc.
    """
    if not response:
        return "{}"
        
    # 1. Try extracting content inside ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 2. Try extracting content inside the first { and last }
    match_loose = re.search(r"(\{.*\})", response, flags=re.DOTALL)
    if match_loose:
        return match_loose.group(1).strip()
        
    # 3. Last resort: Return raw (might fail JSON parse)
    return response.strip()

def _call_ollama_sync(prompt: str, model: str | None = None) -> str:
    """Sync wrapper to call Ollama from FastAPI sync endpoints."""
    model_name = model or settings.ollama_model
    url = f"{settings.ollama_base_url}/api/generate"
    
    logger.info(f"Ollama Call. Prompt len: {len(prompt)}")
    
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                url,
                json={
                    "model": model_name, 
                    "prompt": prompt, 
                    "stream": False, 
                    "format": "json", # Force JSON mode if supported by model
                    "options": {"temperature": 0.1} # Low temp for deterministic logic
                },
            )
            resp.raise_for_status()
            data = resp.json()
            raw_response = data.get("response", "")
            logger.info(f"Ollama Raw Response: {raw_response[:200]}...")
            return raw_response
    except Exception as exc:
        logger.error(f"Ollama call failed: {exc}")
        return ""

def normalize_columns(columns: List[str], schema: List[str]) -> List[str]:
    """
    Use LLM to fuzzy match user-provided column names to the actual schema.
    """
    if not columns:
        return []

    # Simple deterministic cleanup first
    schema_map = {c.lower(): c for c in schema}
    normalized = []
    
    unknowns = []
    
    for col in columns:
        if col.lower() in schema_map:
            normalized.append(schema_map[col.lower()])
        else:
            unknowns.append(col)
            
    if not unknowns:
        return normalized

    # Text-based schema for prompt
    schema_str = ", ".join(schema)
    
    prompt = (
        f"You are a data normalizer. Map options to valid columns.\n"
        f"Valid Columns: [{schema_str}]\n"
        f"Input Options: {json.dumps(unknowns)}\n"
        "Return strictly JSON: {\"mapping\": {\"input_option\": \"Valid Column\"}}\n"
        "If no close match, map to null."
    )
    
    resp = _call_ollama_sync(prompt)
    try:
        cleaned_resp = _clean_json_response(resp)
        mapping = json.loads(cleaned_resp).get("mapping", {})
        for u in unknowns:
            if mapping.get(u) and mapping[u] in schema:
                normalized.append(mapping[u])
            else:
                normalized.append(u)
    except Exception as e:
        logger.error(f"Normalization Parse Error: {e}")
        normalized.extend(unknowns)
        
    return normalized

def generate_formula_from_intent(intent: str, schema: List[str], cell: str) -> Optional[str]:
    """
    Generate an Excel formula from natural language intent using rule-based detection + LLM fallback.
    """
    import re
    
    intent_lower = intent.lower().strip()
    
    # RULE-BASED DETECTION: Handle common statistical operations
    # This ensures correct formulas regardless of LLM quality
    
    # Extract column name from intent
    column_match = None
    
    # First, try exact match (case-insensitive)
    for col in schema:
        if col.lower() in intent_lower:
            column_match = col
            break
    
    # If no match, try partial word matching (e.g., "unit price" matches "UnitPrice")
    if not column_match:
        # Remove spaces from both intent and column names for comparison
        intent_no_space = intent_lower.replace(" ", "")
        for col in schema:
            col_no_space = col.lower().replace(" ", "")
            if col_no_space in intent_no_space or intent_no_space in col_no_space:
                column_match = col
                break
    
    if not column_match:
        # Try to find quoted column or last word
        quoted = re.search(r"['\"]([^'\"]+)['\"]", intent)
        if quoted:
            column_match = quoted.group(1)
        else:
            # Use last capitalized word as column guess
            words = intent.split()
            for word in reversed(words):
                if word and word[0].isupper() and word in schema:
                    column_match = word
                    break
    
    # Determine the function based on keywords
    function_name = None
    
    if any(kw in intent_lower for kw in ['mean', 'average', 'avg']):
        function_name = 'AVERAGE'
    elif any(kw in intent_lower for kw in ['sum', 'total', 'add up']):
        function_name = 'SUM'
    elif any(kw in intent_lower for kw in ['count', 'number of', 'how many']):
        function_name = 'COUNT'
    elif any(kw in intent_lower for kw in ['max', 'maximum', 'highest', 'largest']):
        function_name = 'MAX'
    elif any(kw in intent_lower for kw in ['min', 'minimum', 'lowest', 'smallest']):
        function_name = 'MIN'
    elif any(kw in intent_lower for kw in ['multiply', 'product', '*']):
        # Handle multiplication (e.g., "Multiply Quantity by Unit Price")
        cols = [c for c in schema if c.lower() in intent_lower]
        if len(cols) >= 2:
            return f"={cols[0]}2*{cols[1]}2"
    elif any(kw in intent_lower for kw in ['divide', 'ratio', '/']):
        cols = [c for c in schema if c.lower() in intent_lower]
        if len(cols) >= 2:
            return f"={cols[0]}2/{cols[1]}2"
    
    # If we detected a function and column, generate the formula
    if function_name and column_match:
        # Find column letter (assuming standard Excel layout)
        try:
            col_index = schema.index(column_match)
            col_letter = chr(65 + col_index)  # A=65, B=66, etc.
            # Use a reasonable range (2 to 100)
            return f"={function_name}({col_letter}2:{col_letter}100)"
        except (ValueError, IndexError):
            pass
    
    # FALLBACK: Use LLM if rule-based detection failed
    logger.info(f"Rule-based detection failed for intent: '{intent}'. Falling back to LLM.")
    
    schema_str = ", ".join(schema)
    prompt = (
        f"You are an Excel Expert. Create an Excel formula for cell {cell}.\n"
        f"Columns: [{schema_str}]\n"
        f"User Intent: {intent}\n\n"
        "Rules:\n"
        "1. Return ONLY the formula text starting with =.\n"
        "2. Do NOT explain.\n"
        "3. Do NOT use markdown.\n"
        "Example: =AVERAGE(C2:C100)"
    )
    
    resp = _call_ollama_text(prompt)
    if not resp or "Error connecting" in resp:
        logger.error(f"LLM Error in formula gen: {resp}")
        return None
    
    # Parse LLM response
    cleaned = resp.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        if len(parts) > 1:
            cleaned = parts[1]
            if cleaned.startswith("excel") or cleaned.startswith("vb"):
                 cleaned = cleaned.split("\n", 1)[1]
    
    cleaned = cleaned.strip()
    
    # Extract formula
    match = re.search(r"(=[A-Z0-9_]+[\(\[][^\n]+[\)\]])|(=[A-Z0-9_]+\s*[\+\-\*/]\s*[A-Z0-9_]+)", cleaned, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    
    match_no_eq = re.search(r"([A-Z0-9_]+\([^\n]+\))", cleaned, re.IGNORECASE)
    if match_no_eq:
        found = match_no_eq.group(0).strip()
        if any(x in found.upper() for x in ["SUM", "AVG", "AVERAGE", "COUNT", "MIN", "MAX"]):
            return "=" + found
    
    if cleaned.startswith("="):
        return cleaned
        
    return None

def answer_question(query: str, schema: List[str], data_preview: List[Dict[str, Any]]) -> str:
    """
    Answer a natural language question about the data given the schema and a small preview.
    """
    schema_str = ", ".join(schema)
    preview_str = json.dumps(data_preview)
    
    prompt = (
        f"You are a Data Analyst. Answer the user's question based on the provided data context.\n"
        f"Columns: [{schema_str}]\n"
        f"Data Preview (First 5 rows): {preview_str}\n"
        f"User Question: {query}\n"
        "IMPORTANT RULES:\n"
        "1. Do NOT write any Python code, SQL, or programming scripts.\n"
        "2. Do NOT explain how to write code to solve it.\n"
        "3. Provide the direct answer in plain text.\n"
        "4. If the answer is a number found in the preview, state it directly.\n"
        "5. If you need to estimate based on the preview, do so.\n"
        "Example acceptable answer: 'The average quantity is 45.2 based on the preview.'\n"
        "Example acceptable answer: 'The highest revenue comes from Electronics.'\n"
    )
    
    # Use raw string mode, no JSON forced
    try:
        pass 
    except Exception:
        pass
        

def generate_data_analysis_code(query: str, schema: List[str]) -> str:
    """
    Generate Python pandas code to answer a question about the data.
    """
    schema_str = ", ".join(schema)
    prompt = (
        f"You are a Python Data Analyst. You have a pandas DataFrame named `df` loaded with data.\n"
        f"The available columns are: [{schema_str}].\n"
        f"User Question: {query}\n\n"
        "Write a Python script to calculate the answer.\n"
        "Requirements:\n"
        "1. Assume `df` is already created. Do NOT read any file.\n"
        "2. Perform the necessary cleaning or calculation on `df`.\n"
        "3. Store the final single string or numeric answer in a variable named `result`.\n"
        "4. Return ONLY valid Python code. No markdown, no comments, no explanations.\n"
        "5. Do NOT use the 'return' keyword. Just assign to `result`.\n"
        "6. Do NOT print anything. Just assign to `result`.\n\n"
        "Example:\n"
        "result = df['Quantity'].mean()"
    )
    
    # We use the text wrapper
    raw_response = _call_ollama_text(prompt)
    
    # Clean code
    import re
    # Remove markdown blocks
    cleaned = re.sub(r"```python", "", raw_response, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


def _call_ollama_text(prompt: str, model: str | None = None) -> str:
    """Sync wrapper for text-only response (no JSON mode)."""
    model_name = model or settings.ollama_model
    url = f"{settings.ollama_base_url}/api/generate"
    
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                url,
                json={
                    "model": model_name, 
                    "prompt": prompt, 
                    "stream": False, 
                    # "format": "json",  <-- REMOVED
                    "options": {"temperature": 0.3} 
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except Exception as exc:
        logger.error(f"Ollama text call failed: {exc}")
        return f"Error connecting to AI: {str(exc)}"
