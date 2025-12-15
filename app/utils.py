from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, status


logger = logging.getLogger("llm_excel_mcp")


def init_logging() -> None:
    """Configure basic structured logging for the application."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def ensure_path_within_workspace(path: str, base_dir: str = "sample_files") -> Path:
    """
    Ensure that the provided path is within the allowed workspace directory.

    This is a simple safety measure so the MCP tools don't touch arbitrary files.
    """

    base = Path(base_dir).resolve()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()

    if not str(target).startswith(str(base)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path must be within the sample_files directory.",
        )
    return target


def format_error(message: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Standard error payload used by HTTP and MCP responses."""

    payload: Dict[str, Any] = {"error": message}
    if details:
        payload["details"] = details
    return payload


