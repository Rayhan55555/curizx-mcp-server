"""
Curizx MCP Server - Pytest Fixtures and Global Setup.
Configures test harness for unit and integration testing.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.auth import search_rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset all in-memory rate limiters before every test run."""
    search_rate_limiter.reset("web_search")
    search_rate_limiter.reset("docs_search")
    search_rate_limiter.reset("default")
    yield


@pytest.fixture
def sample_clean_python_code():
    """Clean, well-structured Python code fixture."""
    return '''"""Sample clean module."""

def calculate_discount(price: float, percentage: float) -> float:
    """Calculate the discounted total price."""
    if percentage < 0 or percentage > 100:
        raise ValueError("Invalid percentage")
    return price * (1.0 - percentage / 100.0)
'''


@pytest.fixture
def sample_vulnerable_python_code():
    """Vulnerable Python code fixture containing security anti-patterns."""
    return '''import os
import hashlib
import pickle

def authenticate(username, password):
    # Hardcoded secret
    api_key = "sk-abcdef1234567890abcdef123456"
    # Weak crypto
    h = hashlib.md5(password.encode()).hexdigest()
    # SQL injection pattern
    query = f"SELECT * FROM users WHERE user = '{username}'"
    # Command injection
    os.system(f"echo Logged in {username}")
    # Bare except
    try:
        return True
    except:
        return False
'''


# [MOCK] Mock PyGithub Repository
@pytest.fixture
def mock_github_repo():
    """Creates a mock PyGithub repository with complete attributes."""
    repo = MagicMock()
    repo.name = "curizx-demo"
    repo.full_name = "rayhan/curizx-demo"
    repo.description = "A demo intelligent development repository."
    repo.stargazers_count = 142
    repo.language = "Python"
    repo.open_issues_count = 3
    repo.default_branch = "main"
    repo.get_topics.return_value = ["ai", "mcp", "python"]
    repo.get_languages.return_value = {"Python": 12000, "TypeScript": 4000}

    # Mock file contents
    f1 = MagicMock()
    f1.name = "server.py"
    f1.path = "server.py"
    f1.type = "file"
    f1.decoded_content = b"def test_func():\n    return True\n"

    f2 = MagicMock()
    f2.name = "package.json"
    f2.path = "package.json"
    f2.type = "file"

    repo.get_contents.return_value = [f1, f2]

    # Mock readme
    readme_mock = MagicMock()
    readme_mock.decoded_content = b"# curizx-demo\n\nIntelligent Tools for Development."
    repo.get_readme.return_value = readme_mock

    # Mock pull request
    pr_mock = MagicMock()
    pr_mock.title = "feat: Add high-speed caching"
    pr_mock.state = "open"
    pr_mock.user.login = "contributor-rayhan"
    pr_mock.additions = 45
    pr_mock.deletions = 12
    pr_mock.body = "This PR introduces a Redis caching layer for API responses."

    pr_file1 = MagicMock()
    pr_file1.filename = "cache.py"
    pr_file1.status = "added"
    pr_file1.additions = 45
    pr_file1.deletions = 0
    pr_file1.changes = 45
    pr_file1.patch = "+# TODO: optimize memory limit\n+def cache():\n+    print('debug')"
    pr_mock.get_files.return_value = [pr_file1]

    repo.get_pull.return_value = pr_mock
    return repo
