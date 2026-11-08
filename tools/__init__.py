"""
Curizx MCP Server Tools Package
Intelligent Tools for AI-Powered Development
"""

from .github_tools import (
    github_analyze_repo,
    github_review_pr,
    github_find_issues,
    github_generate_readme,
)
from .code_tools import (
    code_analyze,
    code_security_scan,
    code_suggest_tests,
)
from .search_tools import (
    web_search,
    docs_search,
)
from .utility_tools import (
    summarize_text,
    generate_docs,
    explain_code,
)

__all__ = [
    # GitHub tools (4)
    "github_analyze_repo",
    "github_review_pr",
    "github_find_issues",
    "github_generate_readme",
    # Code tools (3)
    "code_analyze",
    "code_security_scan",
    "code_suggest_tests",
    # Search tools (2)
    "web_search",
    "docs_search",
    # Utility tools (3)
    "summarize_text",
    "generate_docs",
    "explain_code",
]
