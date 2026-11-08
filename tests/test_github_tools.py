"""
Unit and Integration Tests for GitHub Intelligence Tools.
Tests:
- github_analyze_repo
- github_review_pr
- github_find_issues
- github_generate_readme
"""

from unittest.mock import patch, MagicMock
from github import GithubException
import pytest

from tools.github_tools import (
    github_analyze_repo,
    github_review_pr,
    github_find_issues,
    github_generate_readme,
)


# ==============================================================================
# 1. github_analyze_repo Tests
# ==============================================================================

# [MOCK] Happy path test
def test_github_analyze_repo_happy_path(mock_github_repo):
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.return_value = mock_github_repo
        response = github_analyze_repo("rayhan/curizx-demo")

        assert response["success"] is True
        assert response["tool"] == "github_analyze_repo"
        assert response["error"] is None
        result = response["result"]
        assert result["name"] == "rayhan/curizx-demo"
        assert result["stars"] == 142
        assert "Python" in result["tech_stack"]
        assert response["execution_ms"] >= 0


# [REAL API] Invalid input validation (format check)
def test_github_analyze_repo_invalid_input():
    # Invalid format should fail instantly without calling API
    res1 = github_analyze_repo("invalid_format_repo")
    assert res1["success"] is False
    assert "Invalid repository format" in res1["error"]

    res2 = github_analyze_repo("")
    assert res2["success"] is False
    assert "Invalid repository format" in res2["error"]


# [MOCK] Missing repo / 404 test
def test_github_analyze_repo_not_found():
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.side_effect = GithubException(
            status=404, data={"message": "Not Found"}
        )
        response = github_analyze_repo("rayhan/nonexistent-repo")
        assert response["success"] is False
        assert "not found or is private" in response["error"]


# [MOCK] Rate limit / credential failure test
def test_github_analyze_repo_rate_limit_exceeded():
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.side_effect = GithubException(
            status=403, data={"message": "API rate limit exceeded"}
        )
        response = github_analyze_repo("rayhan/curizx-demo")
        assert response["success"] is False
        assert "rate limit exceeded" in response["error"].lower()


# ==============================================================================
# 2. github_review_pr Tests
# ==============================================================================

# [MOCK] Happy path test
def test_github_review_pr_happy_path(mock_github_repo):
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.return_value = mock_github_repo
        response = github_review_pr("rayhan/curizx-demo", pr_number=42)

        assert response["success"] is True
        assert response["tool"] == "github_review_pr"
        result = response["result"]
        assert result["pr_number"] == 42
        assert result["title"] == "feat: Add high-speed caching"
        # Should detect the TODO and print() statements from the patch
        assert any(i["type"] == "incomplete_work" for i in result["issues_found"])


# [REAL API] Invalid input tests
def test_github_review_pr_invalid_input():
    res = github_review_pr("invalid-repo", pr_number=1)
    assert res["success"] is False
    assert "Invalid repository format" in res["error"]

    res_neg = github_review_pr("rayhan/demo", pr_number=-5)
    assert res_neg["success"] is False
    assert "Invalid pr_number" in res_neg["error"]


# ==============================================================================
# 3. github_find_issues Tests
# ==============================================================================

# [MOCK] Happy path test
def test_github_find_issues_happy_path(mock_github_repo):
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.return_value = mock_github_repo
        response = github_find_issues("rayhan/curizx-demo", path="src")

        assert response["success"] is True
        assert response["tool"] == "github_find_issues"
        result = response["result"]
        assert result["files_scanned"] >= 1
        assert "by_severity" in result


# [REAL API] Path traversal security test
def test_github_find_issues_path_traversal_blocked():
    response = github_find_issues("rayhan/curizx-demo", path="../../etc/passwd")
    assert response["success"] is False
    assert "Invalid path traversal" in response["error"]


# ==============================================================================
# 4. github_generate_readme Tests
# ==============================================================================

# [MOCK] Happy path test
def test_github_generate_readme_happy_path(mock_github_repo):
    with patch("tools.github_tools._get_github_client") as mock_client:
        mock_client.return_value.get_repo.return_value = mock_github_repo
        response = github_generate_readme("rayhan/curizx-demo")

        assert response["success"] is True
        assert response["tool"] == "github_generate_readme"
        result = response["result"]
        assert "# curizx-demo" in result["readme_content"]
        assert "Quick Start" in result["readme_content"]
        assert len(result["sections_included"]) >= 5
