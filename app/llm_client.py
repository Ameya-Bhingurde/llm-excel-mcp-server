from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .config import get_settings


settings = get_settings()


async def call_ollama(prompt: str, model: str | None = None) -> str:
    """
    Call a local Ollama model with the given prompt and return the raw response text.

    This is a minimal async client used only for local demos; it is NOT used on Render.
    """

    model_name = model or settings.ollama_model
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=60) as client:
        resp = await client.post(
            "/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")


def build_tool_prompt(instruction: str, tools: List[Dict[str, Any]]) -> str:
    """
    Build a simple system-style prompt that teaches the LLM how to call MCP tools.

    This is intentionally lightweight – just enough for a local demo.
    """

    tool_descriptions = "\n".join(
        f"- {t['name']}: {t['description']} (schema: {t['schema']})" for t in tools
    )
    return (
        "You are an AI that decides which Excel MCP tools to call.\n"
        "Always respond with a single JSON object containing `tool` and `arguments`.\n"
        "Available tools:\n"
        f"{tool_descriptions}\n\n"
        f"User instruction: {instruction}\n"
        "Respond with JSON only."
    )


