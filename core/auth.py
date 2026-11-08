"""
Authentication, Token Validation, Secret Masking, and Security Utilities.
Curizx MCP Server | Curizx AI by Rayhan
"""

import os
import re
import time
from typing import Optional, Dict
from pathlib import PurePosixPath


def mask_secret(secret: Optional[str], visible_chars: int = 5) -> str:
    """
    Mask a sensitive token or API key for safe logging or reporting.
    e.g. 'ghp_1234567890abcdef' -> 'ghp_12****'
         'sk-abcdef123456' -> 'sk-ab****'
    NEVER returns the full secret or more than visible_chars characters.
    """
    if not secret:
        return "Not configured"
    
    clean_secret = secret.strip()
    if len(clean_secret) <= visible_chars:
        return "****"
    
    # Check if there is a known prefix like 'sk-' or 'ghp_'
    prefix_match = re.match(r"^([a-zA-Z0-9_-]{2,5})", clean_secret)
    prefix = prefix_match.group(1) if prefix_match else clean_secret[:visible_chars]
    
    return f"{prefix}****"


def validate_github_token(token: Optional[str] = None) -> Dict[str, any]:
    """
    Validates GitHub token format without making network calls.
    Returns safe validation status.
    """
    if not token:
        return {
            "valid": False,
            "configured": False,
            "message": "GitHub token not provided. Public endpoints will be used (subject to strict 60 req/hr rate limit).",
        }
    
    token = token.strip()
    # Typical GitHub tokens: classic 'ghp_', fine-grained 'github_pat_', or OAuth
    is_standard_prefix = token.startswith(("ghp_", "github_pat_", "gho_", "ghu_"))
    is_length_valid = len(token) >= 30

    return {
        "valid": is_standard_prefix or is_length_valid,
        "configured": True,
        "masked": mask_secret(token),
        "message": "GitHub token format valid.",
    }


def sanitize_input_path(path_str: Optional[str]) -> str:
    """
    Guards against path traversal attacks (e.g., '../', '../../etc/passwd').
    Normalizes path to a safe relative posix path.
    """
    if not path_str or not path_str.strip():
        return ""
    
    clean = path_str.strip()
    # Normalize separators
    clean = clean.replace("\\", "/")
    
    # Disallow absolute filesystem paths and traversal sequences
    if clean.startswith("/") or ".." in clean.split("/"):
        raise ValueError(f"Invalid path traversal detected in '{path_str}'. Only relative repository paths are allowed.")
    
    posix_path = PurePosixPath(clean)
    return str(posix_path)


class RateLimiter:
    """
    In-memory rate limiter per key using a rolling 60-second window.
    Default limit is 10 requests per minute.
    """
    def __init__(self, limit_per_minute: int = 10):
        self.limit = limit_per_minute
        self.history: Dict[str, list[float]] = {}

    def is_allowed(self, client_or_session: str = "default") -> tuple[bool, int, float]:
        """
        Checks if request is allowed.
        Returns: (allowed: bool, remaining: int, reset_in_seconds: float)
        """
        now = time.time()
        window_start = now - 60.0

        if client_or_session not in self.history:
            self.history[client_or_session] = []

        # Filter out timestamps older than 60 seconds
        self.history[client_or_session] = [
            t for t in self.history[client_or_session] if t > window_start
        ]

        current_count = len(self.history[client_or_session])
        if current_count >= self.limit:
            oldest = self.history[client_or_session][0]
            retry_after = max(1.0, round(60.0 - (now - oldest), 1))
            return False, 0, retry_after

        self.history[client_or_session].append(now)
        remaining = self.limit - len(self.history[client_or_session])
        return True, remaining, 0.0

    def reset(self, client_or_session: str = "default") -> None:
        if client_or_session in self.history:
            self.history[client_or_session] = []


# Search tool rate limiter (10 per minute)
search_rate_limiter = RateLimiter(limit_per_minute=10)
