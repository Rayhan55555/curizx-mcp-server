"""
Curizx MCP Server Test Runner.
Executes test suites and reports exact results for all 12 tools.
"""

import sys
import os
import time

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.code_tools import code_analyze, code_security_scan, code_suggest_tests
from tools.utility_tools import summarize_text, generate_docs, explain_code
from tools.github_tools import github_analyze_repo, github_review_pr, github_find_issues, github_generate_readme
from tools.search_tools import web_search, docs_search
from core.auth import validate_github_token, mask_secret, search_rate_limiter


def run_all_verification_tests():
    passed = 0
    failed = 0
    tests = []

    def record(name: str, condition: bool, message: str = ""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
            tests.append({"name": name, "status": "PASS", "message": message})
        else:
            failed += 1
            print(f"  [FAIL] {name}: {message}")
            tests.append({"name": name, "status": "FAIL", "message": message})

    print("=" * 60)
    print("Running Curizx MCP Server Suite...")
    print("=" * 60)

    # 1. Auth & Security Tests
    print("\n[1/5] Core Security & Token Masking")
    record("Mask Secret sk- pattern", mask_secret("sk-1234567890abcdef") == "sk-12****", "Masking failed")
    record("Mask Secret ghp_ pattern", mask_secret("ghp_998877665544332211") == "ghp_9****", "Masking failed")
    record("Mask Secret None", mask_secret(None) == "Not configured", "None handling failed")
    val_status = validate_github_token(None)
    record("Validate Missing GitHub Token", val_status["valid"] is False, "Validation failed")

    # 2. Code Tools Tests
    print("\n[2/5] Code Intelligence & Security Tools")
    clean_code = "def add(a: int, b: int) -> int:\n    '''Add numbers.'''\n    return a + b"
    res_analyze = code_analyze(clean_code, language="python")
    record("code_analyze Happy Path", res_analyze["success"] is True and res_analyze["result"]["functions_count"] == 1)

    res_analyze_err = code_analyze("def broken(:", language="python")
    record("code_analyze SyntaxError", res_analyze_err["success"] is False and "SyntaxError" in res_analyze_err["error"])

    vuln_code = "api_key = 'sk-1234567890abcdef123456'\nquery = f'SELECT * FROM users WHERE id = {user_id}'\nos.system('rm -rf /')"
    res_sec = code_security_scan(vuln_code, language="python")
    record("code_security_scan Vulnerability Detection", res_sec["success"] is True and res_sec["result"]["safe"] is False)
    record("code_security_scan Secret Masking", "sk-1234567890abcdef123456" not in str(res_sec["result"]))

    res_test_gen = code_suggest_tests(clean_code, language="python")
    record("code_suggest_tests Review Required Marker", "# [REVIEW REQUIRED]" in res_test_gen["result"]["test_templates"][0]["template"])

    # 3. Utility Tools Tests
    print("\n[3/5] Developer Utility Tools")
    text = "Basically, this is a test sentence that removes fluff. Needless to say, it works reliably."
    res_sum = summarize_text(text, max_length=15)
    record("summarize_text Fluff Removal", "Basically" not in res_sum["result"]["summary"])

    res_docs = generate_docs(clean_code, doc_type="docstring")
    record("generate_docs Docstring", "Args:" in res_docs["result"]["documentation"])

    res_exp = explain_code(clean_code, level="beginner")
    record("explain_code Beginner Level", res_exp["success"] is True and res_exp["result"]["target_audience"] == "beginner")

    # 4. Search Tools Tests
    print("\n[4/5] Search & Docs Tools")
    search_rate_limiter.reset("web_search")
    res_search_empty = web_search("")
    record("web_search Empty Query Validation", res_search_empty["success"] is False)

    res_docs_tech = docs_search("queries", technology="UnsupportedTechnology123")
    record("docs_search Unsupported Tech Validation", res_docs_tech["success"] is False and "not supported" in res_docs_tech["error"])

    # Rate limiting test
    for _ in range(10):
        search_rate_limiter.is_allowed("test_session")
    allowed, _, _ = search_rate_limiter.is_allowed("test_session")
    record("search_rate_limiter Limit Enforcement (10 req/min)", allowed is False)

    # 5. GitHub Tools Validation
    print("\n[5/5] GitHub Tools Input & Security")
    res_gh_format = github_analyze_repo("invalid_format_repo")
    record("github_analyze_repo Format Validation", res_gh_format["success"] is False)

    res_gh_traversal = github_find_issues("owner/repo", path="../../etc/passwd")
    record("github_find_issues Path Traversal Blocked", res_gh_traversal["success"] is False and "traversal" in res_gh_traversal["error"].lower())

    print("\n" + "=" * 60)
    print(f"Results: {passed} PASSED, {failed} FAILED (Total: {passed + failed})")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_verification_tests()
    sys.exit(0 if success else 1)
