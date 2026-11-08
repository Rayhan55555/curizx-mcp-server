"""
Unit and Integration Tests for Code Intelligence & Security Tools.
Tests:
- code_analyze
- code_security_scan
- code_suggest_tests
"""

import pytest
from tools.code_tools import code_analyze, code_security_scan, code_suggest_tests


# ==============================================================================
# 1. code_analyze Tests
# ==============================================================================

# [REAL API] Happy path AST analysis
def test_code_analyze_happy_path(sample_clean_python_code):
    response = code_analyze(sample_clean_python_code, language="python")

    assert response["success"] is True
    assert response["tool"] == "code_analyze"
    result = response["result"]
    assert result["language"] == "python"
    assert result["functions_count"] == 1
    func = result["functions"][0]
    assert func["name"] == "calculate_discount"
    assert "price" in func["args"]
    assert func["has_docstring"] is True
    assert result["complexity"]["status"] == "Healthy"


# [REAL API] Syntax error handling
def test_code_analyze_syntax_error():
    broken_code = "def invalid_syntax(x\n    return x +"
    response = code_analyze(broken_code, language="python")

    assert response["success"] is False
    assert "SyntaxError" in response["error"]


# [REAL API] Empty input test
def test_code_analyze_empty_input():
    response = code_analyze("", language="python")
    assert response["success"] is False
    assert "cannot be empty" in response["error"]


# [REAL API] TypeScript analysis
def test_code_analyze_typescript():
    ts_code = """
    export function fetchUserProfile(userId: string) {
        console.log("Fetching user: " + userId);
        const data: any = { id: userId };
        return data;
    }
    """
    response = code_analyze(ts_code, language="typescript")
    assert response["success"] is True
    result = response["result"]
    assert result["functions_count"] >= 1
    assert any(i["type"] == "console_log" for i in result["issues"])
    assert any(i["type"] == "ts_any_type" for i in result["issues"])


# ==============================================================================
# 2. code_security_scan Tests
# ==============================================================================

# [REAL API] Clean code test (Safe = True)
def test_code_security_scan_clean_code(sample_clean_python_code):
    response = code_security_scan(sample_clean_python_code, language="python")

    assert response["success"] is True
    assert response["result"]["safe"] is True
    assert response["result"]["findings_count"] == 0


# [REAL API] Vulnerabilities detected & secrets strictly masked
def test_code_security_scan_vulnerabilities(sample_vulnerable_python_code):
    response = code_security_scan(sample_vulnerable_python_code, language="python")

    assert response["success"] is True
    result = response["result"]
    assert result["safe"] is False
    assert result["findings_count"] >= 3

    # Check that secrets are MASKED and raw key is NEVER exposed
    raw_secret = "sk-abcdef1234567890abcdef123456"
    for finding in result["findings"]:
        assert raw_secret not in finding["description"]
        assert raw_secret not in finding["remediation"]

    # Verify SQL injection, hardcoded secret, and command injection are detected
    types_found = {f["type"] for f in result["findings"]}
    assert "OPENAI_OR_AI_API_KEY" in types_found or "HARDCODED_SECRET" in types_found
    assert "SQL_INJECTION" in types_found
    assert "COMMAND_INJECTION" in types_found
    assert "WEAK_CRYPTO" in types_found


# ==============================================================================
# 3. code_suggest_tests Tests
# ==============================================================================

# [REAL API] Happy path test generation with # [REVIEW REQUIRED]
def test_code_suggest_tests_happy_path(sample_clean_python_code):
    response = code_suggest_tests(sample_clean_python_code, language="python")

    assert response["success"] is True
    result = response["result"]
    assert "calculate_discount" in result["untested_functions"]
    assert len(result["test_templates"]) >= 1

    template_entry = result["test_templates"][0]
    template_code = template_entry["template"]
    assert "# [REVIEW REQUIRED]" in template_code
    assert "def test_calculate_discount_happy_path():" in template_code
    assert "def test_calculate_discount_invalid_input_edge_case():" in template_code


# [REAL API] Empty input test
def test_code_suggest_tests_empty_input():
    response = code_suggest_tests("   ", language="python")
    assert response["success"] is False
    assert "cannot be empty" in response["error"]
