"""
Curizx MCP Server
Intelligent Tools for AI-Powered Development
By Rayhan | Curizx AI Architecture

Entry point for the Model Context Protocol (MCP) server.
Connects Claude Desktop, Cursor, Windsurf and other AI agents to 12 development intelligence tools.
"""

import sys
from typing import Any, Dict, List, Optional

# Core configurations and logging
from core.config import settings
from core.logger import logger
from core.auth import mask_secret, validate_github_token

# Import all 12 intelligence tools
from tools.github_tools import (
    github_analyze_repo as _github_analyze_repo,
    github_review_pr as _github_review_pr,
    github_find_issues as _github_find_issues,
    github_generate_readme as _github_generate_readme,
)
from tools.code_tools import (
    code_analyze as _code_analyze,
    code_security_scan as _code_security_scan,
    code_suggest_tests as _code_suggest_tests,
)
from tools.search_tools import (
    web_search as _web_search,
    docs_search as _docs_search,
)
from tools.utility_tools import (
    summarize_text as _summarize_text,
    generate_docs as _generate_docs,
    explain_code as _explain_code,
)

# Initialize FastMCP Server
try:
    from fastmcp import FastMCP
    mcp = FastMCP(
        name=settings.PROJECT_NAME,
        instructions=(
            f"{settings.BRAND}\n"
            f"{settings.TAGLINE}\n"
            "Provides high-performance developer intelligence tools: GitHub analytics, "
            "code quality review, security scanning, web search, documentation, and AST insights."
        ),
    )
except ImportError:
    # Lightweight Fallback class if fastmcp is resolving or executing in mock test environment
    class FastMCP:  # type: ignore
        def __init__(self, name: str, instructions: str = ""):
            self.name = name
            self.instructions = instructions
            self.tools: Dict[str, Any] = {}

        def tool(self, name: Optional[str] = None):
            def decorator(fn):
                tool_name = name or fn.__name__
                self.tools[tool_name] = fn
                return fn
            return decorator

        def run(self, transport: str = "stdio"):
            logger.info(f"Starting {self.name} on transport: {transport}")

    mcp = FastMCP(name=settings.PROJECT_NAME)


# ==============================================================================
# GITHUB TOOLS (4)
# ==============================================================================

@mcp.tool()
def github_analyze_repo(repo: str) -> Dict[str, Any]:
    """
    Fetches repo info, detects tech stack, counts files, reads README summary.
    Input: repo (str) e.g. 'rayhan/my-project' or 'owner/repo'
    Returns: {name, description, tech_stack, file_count, stars, language, topics}
    """
    logger.info(f"Executing github_analyze_repo for: {repo}")
    return _github_analyze_repo(repo=repo)


@mcp.tool()
def github_review_pr(repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Gets PR diff, changed files, analyzes code quality issues.
    Input: repo (str), pr_number (int)
    Returns: {title, files_changed, additions, deletions, issues_found, suggestions}
    """
    logger.info(f"Executing github_review_pr for: {repo} #{pr_number}")
    return _github_review_pr(repo=repo, pr_number=pr_number)


@mcp.tool()
def github_find_issues(repo: str, path: Optional[str] = None) -> Dict[str, Any]:
    """
    Reads Python/TS files, finds: missing docstrings, complex functions, unused imports, TODO comments.
    Input: repo (str), path (str, optional)
    Returns: {files_scanned, issues, by_severity}
    """
    logger.info(f"Executing github_find_issues for: {repo} (path: {path or 'root'})")
    return _github_find_issues(repo=repo, path=path)


@mcp.tool()
def github_generate_readme(repo: str) -> Dict[str, Any]:
    """
    Reads repo structure + existing code, generates professional README.md content.
    Input: repo (str) e.g. 'owner/repo'
    Returns: {readme_content, sections_included}
    """
    logger.info(f"Executing github_generate_readme for: {repo}")
    return _github_generate_readme(repo=repo)


# ==============================================================================
# CODE TOOLS (3)
# ==============================================================================

@mcp.tool()
def code_analyze(code: str, language: str = "python") -> Dict[str, Any]:
    """
    AST analysis for Python, pattern analysis for TypeScript/JavaScript.
    Returns: {language, functions, complexity, issues, suggestions}
    """
    logger.info(f"Executing code_analyze for language: {language}")
    return _code_analyze(code=code, language=language)


@mcp.tool()
def code_security_scan(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Scans for: SQL injection patterns, hardcoded secrets, command injection, insecure imports, weak crypto.
    Returns: {findings, by_severity, safe: bool}
    NEVER returns actual secret values (automatically masks sensitive tokens).
    """
    logger.info(f"Executing code_security_scan for language: {language}")
    return _code_security_scan(code=code, language=language)


@mcp.tool()
def code_suggest_tests(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Finds untested functions, generates pytest templates marked # [REVIEW REQUIRED].
    Input: code (str), language (str)
    Returns: {untested_functions, test_templates}
    """
    logger.info(f"Executing code_suggest_tests for language: {language}")
    return _code_suggest_tests(code=code, language=language)


# ==============================================================================
# SEARCH TOOLS (2)
# ==============================================================================

@mcp.tool()
def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Performs DuckDuckGo web search with per-session rate limiting (10 req/min).
    Input: query (str), max_results (int=5)
    Returns: {results: [{title, url, snippet}]}
    """
    logger.info(f"Executing web_search for query: {query}")
    return _web_search(query=query, max_results=max_results)


@mcp.tool()
def docs_search(query: str, technology: str) -> Dict[str, Any]:
    """
    Searches official docs: Python, FastAPI, Next.js, React, PostgreSQL, Docker, GitHub.
    Input: query (str), technology (str)
    Returns: {results, source, technology}
    """
    logger.info(f"Executing docs_search for query: {query} [tech: {technology}]")
    return _docs_search(query=query, technology=technology)


# ==============================================================================
# UTILITY TOOLS (3)
# ==============================================================================

@mcp.tool()
def summarize_text(text: str, max_length: int = 200) -> Dict[str, Any]:
    """
    Extracts key points, removes fluff, and condenses text.
    Input: text (str), max_length (int=200)
    Returns: {summary, key_points, word_count}
    """
    logger.info("Executing summarize_text")
    return _summarize_text(text=text, max_length=max_length)


@mcp.tool()
def generate_docs(code: str, doc_type: str = "docstring") -> Dict[str, Any]:
    """
    Generates structured documentation ('docstring' | 'api' | 'readme').
    Input: code (str), doc_type (str)
    Returns: {documentation, format, sections}
    """
    logger.info(f"Executing generate_docs with type: {doc_type}")
    return _generate_docs(code=code, doc_type=doc_type)


@mcp.tool()
def explain_code(code: str, level: str = "intermediate") -> Dict[str, Any]:
    """
    Explains what code does, why it's written this way, potential improvements.
    Input: code (str), level ('beginner' | 'intermediate' | 'expert')
    Returns: {explanation, key_concepts, improvements}
    """
    logger.info(f"Executing explain_code for level: {level}")
    return _explain_code(code=code, level=level)


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

def main():
    """Main execution point for launching the FastMCP server."""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Brand: {settings.BRAND} | {settings.TAGLINE}")
    token_status = validate_github_token(settings.GITHUB_TOKEN)
    logger.info(f"GitHub Auth Status: {token_status['message']} (Masked: {token_status.get('masked', 'None')})")
    logger.info(f"Configured Tools: 12 total (GitHub: 4, Code: 3, Search: 2, Utility: 3)")
    logger.info("=" * 60)

    # Standard MCP STDIO Transport for Claude Desktop / Cursor / Windsurf
    mcp.run()


if __name__ == "__main__":
    main()
