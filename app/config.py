from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="LLM Excel MCP Server")
    environment: str = Field(default="local")
    debug: bool = Field(default=False)

    # FastAPI / server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=10000)

    # LLM / demo client
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


