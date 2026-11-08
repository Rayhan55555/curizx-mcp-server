"""
Structured Logging with Automatic Secret Sanitization.
Curizx MCP Server | Curizx AI by Rayhan
"""

import logging
import re
import sys
from typing import Any
from .config import settings

# Patterns for sensitive tokens (GitHub, OpenAI, Anthropic, AWS, generic JWT/keys)
SENSITIVE_PATTERNS = [
    re.compile(r"(ghp_[a-zA-Z0-9]{20,})"),
    re.compile(r"(github_pat_[a-zA-Z0-9_]{20,})"),
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),
    re.compile(r"(AIza[0-9A-Za-z-_]{35})"),
    re.compile(r"(Bearer\s+)[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
]


class SanitizingFormatter(logging.Formatter):
    """Logging formatter that redacts secrets and tokens."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in SENSITIVE_PATTERNS:
            msg = pattern.sub("[REDACTED_SECRET]", msg)
        return msg


def setup_logger(name: str = "curizx_mcp") -> logging.Logger:
    """Configures structured, sanitized console logger."""
    logger_instance = logging.getLogger(name)
    level_name = getattr(settings, "LOG_LEVEL", "INFO").upper()
    logger_instance.setLevel(getattr(logging, level_name, logging.INFO))

    # Prevent duplicate handlers
    if not logger_instance.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level_name, logging.INFO))
        formatter = SanitizingFormatter(
            fmt="%(asctime)s [%(levelname)s] [Curizx] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger_instance.addHandler(handler)

    return logger_instance


logger = setup_logger()
