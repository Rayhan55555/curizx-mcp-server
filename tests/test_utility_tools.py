"""
Unit and Integration Tests for Utility Tools.
Tests:
- summarize_text
- generate_docs
- explain_code
"""

import pytest
from tools.utility_tools import summarize_text, generate_docs, explain_code


# ==============================================================================
# 1. summarize_text Tests
# ==============================================================================

# [REAL API] Happy path test
def test_summarize_text_happy_path():
    long_text = (
        "Basically, artificial intelligence is transforming software engineering at an unprecedented pace. "
        "Needless to say, developer tools are adopting Model Context Protocol to empower coding assistants. "
        "At the end of the day, Curizx MCP Server bridges agents to production workflows seamlessly. "
        "It provides AST code inspection, pull request review, and security pattern detection in real time."
    )
    response = summarize_text(long_text, max_length=50)

    assert response["success"] is True
    assert response["tool"] == "summarize_text"
    result = response["result"]
    assert result["word_count"] > 0
    assert result["original_word_count"] > result["word_count"]
    assert len(result["key_points"]) >= 1
    # Check that fluff words like 'Basically' and 'Needless to say' were stripped
    assert "Basically," not in result["summary"]


# [REAL API] Empty text test
def test_summarize_text_empty_input():
    response = summarize_text("")
    assert response["success"] is False
    assert "cannot be empty" in response["error"]


# ==============================================================================
# 2. generate_docs Tests
# ==============================================================================

# [REAL API] Happy path docstring generation
def test_generate_docs_docstring():
    code = "def process_payment(amount: float, currency: str = 'USD'): return True"
    response = generate_docs(code, doc_type="docstring")

    assert response["success"] is True
    result = response["result"]
    assert result["format"] == "docstring"
    assert "Args:" in result["documentation"]
    assert "Returns:" in result["documentation"]
    assert "process_payment" in result["functions_documented"]


# [REAL API] Happy path API spec generation
def test_generate_docs_api():
    code = "def create_user(username, email): pass"
    response = generate_docs(code, doc_type="api")

    assert response["success"] is True
    assert "### `POST /api/v1/create-user`" in response["result"]["documentation"]


# [REAL API] Invalid doc_type test
def test_generate_docs_invalid_type():
    response = generate_docs("def f(): pass", doc_type="invalid_format")
    assert response["success"] is False
    assert "Invalid doc_type" in response["error"]


# ==============================================================================
# 3. explain_code Tests
# ==============================================================================

# [REAL API] Levels test (beginner, intermediate, expert)
@pytest.mark.parametrize("level", ["beginner", "intermediate", "expert"])
def test_explain_code_levels(level):
    code = """
    async def fetch_metrics(service_id: str):
        try:
            return await api_client.get(f"/services/{service_id}")
        except ConnectionError:
            return None
    """
    response = explain_code(code, level=level)

    assert response["success"] is True
    result = response["result"]
    assert result["target_audience"] == level
    assert len(result["improvements"]) >= 1
    assert any("Async" in c for c in result["key_concepts"])


# [REAL API] Invalid level test
def test_explain_code_invalid_level():
    response = explain_code("x = 1", level="alien")
    assert response["success"] is False
    assert "Invalid level" in response["error"]
