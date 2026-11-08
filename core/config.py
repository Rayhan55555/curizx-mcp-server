"""
Core configuration and environment variables management using Pydantic v2.
Curizx MCP Server | Curizx AI by Rayhan
"""

from typing import Optional, Any
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    # Minimal fallback to read .env file manually if python-dotenv is not installed
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator
    HAS_PYDANTIC = True
except ImportError:
    try:
        from pydantic import BaseModel as BaseSettings, Field, field_validator  # type: ignore
        SettingsConfigDict = dict  # type: ignore
        HAS_PYDANTIC = True
    except ImportError:
        HAS_PYDANTIC = False
        class BaseSettings:  # type: ignore
            pass
        def Field(default=None, default_factory=None):  # type: ignore
            return default_factory() if default_factory else default
        def field_validator(*args, **kwargs):  # type: ignore
            return lambda fn: fn
        SettingsConfigDict = dict  # type: ignore


class Settings(BaseSettings):
    """Server and tool settings with validation."""
    if HAS_PYDANTIC:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

    # Brand & Server Identity
    PROJECT_NAME: str = "curizx-mcp-server"
    VERSION: str = "0.1.0"
    BRAND: str = "Curizx AI by Rayhan"
    TAGLINE: str = "Intelligent Tools for AI-Powered Development"

    # Server Networking
    MCP_HOST: str = Field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    MCP_PORT: int = Field(default_factory=lambda: int(os.getenv("MCP_PORT", "8000")))

    # Environment & Logging
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # GitHub Access Token
    GITHUB_TOKEN: Optional[str] = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))

    # Rate Limiting & Timeouts
    RATE_LIMIT_SEARCH_PER_MINUTE: int = 10
    REQUEST_TIMEOUT_SECONDS: float = 15.0

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            return "INFO"
        return upper_v


# Global singleton instance
settings = Settings()
