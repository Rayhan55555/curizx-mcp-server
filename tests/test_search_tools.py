"""
Unit and Integration Tests for Search & Docs Tools.
Tests:
- web_search
- docs_search
- Rate Limiting Enforcement
"""

from unittest.mock import patch
import pytest
from tools.search_tools import web_search, docs_search
from core.auth import search_rate_limiter


# ==============================================================================
# 1. web_search Tests
# ==============================================================================

# [MOCK] Happy path test
def test_web_search_happy_path():
    mock_results = [
        {"title": "FastAPI Framework", "url": "https://fastapi.tiangolo.com", "snippet": "High performance async web framework."}
    ]
    with patch("tools.search_tools._raw_ddg_search", return_value=mock_results):
        response = web_search("FastAPI tutorial", max_results=3)

        assert response["success"] is True
        assert response["tool"] == "web_search"
        result = response["result"]
        assert result["total_found"] == 1
        assert result["results"][0]["title"] == "FastAPI Framework"


# [REAL API] Invalid input test
def test_web_search_invalid_input():
    res1 = web_search("")
    assert res1["success"] is False
    assert "Query parameter cannot be empty" in res1["error"]

    res2 = web_search("   ")
    assert res2["success"] is False


# [REAL API] Rate limit enforcement test (10 requests per minute)
def test_web_search_rate_limit_exceeded():
    search_rate_limiter.reset("web_search")

    with patch("tools.search_tools._raw_ddg_search", return_value=[]):
        # Fire 10 allowed requests
        for _ in range(10):
            res = web_search("test query")
            assert res["success"] is True

        # 11th request MUST be blocked by rate limiter
        blocked_res = web_search("test query 11")
        assert blocked_res["success"] is False
        assert "Rate limit exceeded" in blocked_res["error"]


# ==============================================================================
# 2. docs_search Tests
# ==============================================================================

# [MOCK] Happy path test
def test_docs_search_happy_path():
    mock_results = [
        {"title": "asyncio — Asynchronous I/O", "url": "https://docs.python.org/3/library/asyncio.html", "snippet": "Asynchronous I/O documentation."}
    ]
    with patch("tools.search_tools._raw_ddg_search", return_value=mock_results):
        response = docs_search("asyncio event loop", technology="Python")

        assert response["success"] is True
        assert response["tool"] == "docs_search"
        result = response["result"]
        assert result["technology"] == "Python 3 Documentation"
        assert len(result["results"]) == 1


# [REAL API] Unsupported technology test
def test_docs_search_unsupported_technology():
    response = docs_search("queries", technology="SomeUnknownTech123")

    assert response["success"] is False
    assert "is not supported" in response["error"]
    assert "Python, FastAPI, Next.js" in response["error"]


# [REAL API] Empty inputs
def test_docs_search_empty_input():
    res1 = docs_search("", technology="Python")
    assert res1["success"] is False
    assert "Query parameter cannot be empty" in res1["error"]

    res2 = docs_search("models", technology="")
    assert res2["success"] is False
    assert "Technology parameter cannot be empty" in res2["error"]
