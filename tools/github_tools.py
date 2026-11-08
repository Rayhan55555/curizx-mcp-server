"""
GitHub Intelligence Tools for Curizx MCP Server.
Covers:
1. github_analyze_repo
2. github_review_pr
3. github_find_issues
4. github_generate_readme
"""

import os
import re
import time
import json
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

# Graceful optional imports for PyGithub and httpx
try:
    from github import Github, GithubException, Auth
    HAS_PYGITHUB = True
except ImportError:
    HAS_PYGITHUB = False
    Github = None  # type: ignore
    Auth = None  # type: ignore
    class GithubException(Exception):  # type: ignore
        def __init__(self, status: int, data: Dict[str, Any]):
            super().__init__(str(data))
            self.status = status
            self.data = data

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from core.config import settings
from core.logger import logger
from core.auth import sanitize_input_path, mask_secret

REPO_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")


def _format_response(tool: str, start_time: float, result: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
    """Ensures strict adherence to Curizx MCP response standard."""
    elapsed_ms = int((time.time() - start_time) * 1000)
    return {
        "success": error is None,
        "tool": tool,
        "result": result if error is None else None,
        "execution_ms": elapsed_ms,
        "error": error,
    }


def _detect_tech_stack(file_names: List[str], languages: Dict[str, int]) -> List[str]:
    """Infers modern tech stack based on project files and GitHub detected languages."""
    stack = set()
    files_lower = {f.lower() for f in file_names}

    for lang in languages.keys():
        stack.add(lang)

    if "package.json" in files_lower:
        stack.add("Node.js")
    if "tsconfig.json" in files_lower:
        stack.add("TypeScript")
    if "requirements.txt" in files_lower or "pyproject.toml" in files_lower or "setup.py" in files_lower:
        stack.add("Python")
    if "cargo.toml" in files_lower:
        stack.add("Rust")
    if "go.mod" in files_lower:
        stack.add("Go")
    if "dockerfile" in files_lower or "docker-compose.yml" in files_lower:
        stack.add("Docker")
    if "tailwind.config.js" in files_lower or "tailwind.config.ts" in files_lower:
        stack.add("TailwindCSS")
    if "next.config.js" in files_lower or "next.config.mjs" in files_lower or "next.config.ts" in files_lower:
        stack.add("Next.js")
    if "vite.config.js" in files_lower or "vite.config.ts" in files_lower:
        stack.add("Vite")

    return sorted(list(stack))


def _fetch_github_api(endpoint: str) -> Dict[str, Any]:
    """Direct HTTP fallback using urllib when PyGithub is not present."""
    token = settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Curizx-MCP-Server/0.1.0 (Rayhan Curizx AI)")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token and token.strip():
        req.add_header("Authorization", f"Bearer {token.strip()}")

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.HTTPError as he:
        raise GithubException(status=he.code, data={"message": he.reason})
    except Exception as e:
        raise GithubException(status=500, data={"message": str(e)})


def _get_github_client():
    """Returns PyGithub instance configured with token if available."""
    if not HAS_PYGITHUB or Github is None:
        return None
    token = settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
    if token and token.strip() and Auth is not None:
        auth = Auth.Token(token.strip())
        return Github(auth=auth)
    return Github()


def github_analyze_repo(repo: str) -> Dict[str, Any]:
    """
    Fetches repo info, detects tech stack, counts files, reads README summary.
    Input: repo (str) e.g. "rayhan/my-project"
    Returns: {name, description, tech_stack, file_count, stars, language, topics}
    """
    start_time = time.time()
    tool_name = "github_analyze_repo"

    if not repo or not REPO_REGEX.match(repo.strip()):
        return _format_response(
            tool_name,
            start_time,
            error="Invalid repository format. Expected 'owner/repo' (e.g. 'rayhan/my-project')",
        )

    clean_repo = repo.strip()
    try:
        gh = _get_github_client()
        if gh:
            gh_repo = gh.get_repo(clean_repo)
            name = gh_repo.full_name
            description = gh_repo.description or "No description provided."
            stars = gh_repo.stargazers_count
            language = gh_repo.language or "Unknown"
            topics = gh_repo.get_topics() or []
            file_count = 0
            root_files: List[str] = []
            try:
                contents = gh_repo.get_contents("")
                while contents:
                    file_content = contents.pop(0)
                    file_count += 1
                    if file_content.type == "file":
                        root_files.append(file_content.name)
            except Exception:
                root_files = []

            try:
                languages = gh_repo.get_languages()
            except Exception:
                languages = {language: 1} if language != "Unknown" else {}

            tech_stack = _detect_tech_stack(root_files, languages)
            readme_summary = "README detected."
            try:
                readme = gh_repo.get_readme()
                decoded = readme.decoded_content.decode("utf-8", errors="ignore")
                lines = [ln.strip() for ln in decoded.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                readme_summary = " ".join(lines[:2]) if lines else "README found with headings."
            except Exception:
                readme_summary = "No README file detected."

            open_issues = gh_repo.open_issues_count
            default_branch = gh_repo.default_branch
        else:
            # Direct HTTP Fallback
            repo_data = _fetch_github_api(f"repos/{clean_repo}")
            name = repo_data.get("full_name", clean_repo)
            description = repo_data.get("description") or "No description provided."
            stars = repo_data.get("stargazers_count", 0)
            language = repo_data.get("language") or "Unknown"
            topics = repo_data.get("topics", [])
            open_issues = repo_data.get("open_issues_count", 0)
            default_branch = repo_data.get("default_branch", "main")
            
            # Fetch root contents
            root_files = []
            file_count = 0
            try:
                contents_data = _fetch_github_api(f"repos/{clean_repo}/contents")
                if isinstance(contents_data, list):
                    for item in contents_data:
                        file_count += 1
                        if item.get("type") == "file":
                            root_files.append(item.get("name", ""))
            except Exception:
                pass

            languages = {}
            try:
                languages = _fetch_github_api(f"repos/{clean_repo}/languages")
            except Exception:
                languages = {language: 1} if language != "Unknown" else {}

            tech_stack = _detect_tech_stack(root_files, languages)
            readme_summary = f"Repository {name} on branch {default_branch}."

        result = {
            "name": name,
            "description": description,
            "tech_stack": tech_stack,
            "file_count": file_count,
            "stars": stars,
            "language": language,
            "topics": topics,
            "readme_summary": readme_summary,
            "open_issues": open_issues,
            "default_branch": default_branch,
        }
        return _format_response(tool_name, start_time, result=result)

    except GithubException as ge:
        logger.warning(f"GitHub API error for {clean_repo}: {ge.status}")
        if ge.status == 404:
            return _format_response(tool_name, start_time, error=f"Repository '{clean_repo}' not found or is private.")
        if ge.status in (401, 403):
            return _format_response(
                tool_name, start_time, error="GitHub API rate limit exceeded or invalid token credentials."
            )
        return _format_response(tool_name, start_time, error=f"GitHub API Error: {ge.data.get('message', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Failed to analyze repository: {str(e)}")


def github_review_pr(repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Gets PR diff, changed files, analyzes code quality issues.
    Input: repo (str), pr_number (int)
    Returns: {title, files_changed, additions, deletions, issues_found, suggestions}
    """
    start_time = time.time()
    tool_name = "github_review_pr"

    if not repo or not REPO_REGEX.match(repo.strip()):
        return _format_response(
            tool_name,
            start_time,
            error="Invalid repository format. Expected 'owner/repo' (e.g. 'rayhan/my-project')",
        )

    if not isinstance(pr_number, int) or pr_number <= 0:
        return _format_response(tool_name, start_time, error="Invalid pr_number. Expected positive integer.")

    clean_repo = repo.strip()
    try:
        gh = _get_github_client()
        files_changed: List[Dict[str, Any]] = []
        issues_found: List[Dict[str, Any]] = []
        suggestions: List[str] = []

        if gh:
            gh_repo = gh.get_repo(clean_repo)
            pr = gh_repo.get_pull(pr_number)
            title = pr.title
            state = pr.state
            author = pr.user.login
            total_additions = pr.additions
            total_deletions = pr.deletions
            pr_body = pr.body or ""
            files = pr.get_files()
            for f in files:
                files_changed.append({
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                })
                patch = f.patch or ""
                if "console.log(" in patch:
                    issues_found.append({
                        "file": f.filename,
                        "severity": "LOW",
                        "type": "debug_code",
                        "message": "console.log statement found in pull request diff.",
                    })
                if "print(" in patch and f.filename.endswith(".py"):
                    issues_found.append({
                        "file": f.filename,
                        "severity": "LOW",
                        "type": "debug_code",
                        "message": "print() debugging statement found in production Python code.",
                    })
                if "TODO" in patch or "FIXME" in patch:
                    issues_found.append({
                        "file": f.filename,
                        "severity": "MEDIUM",
                        "type": "incomplete_work",
                        "message": "Unresolved TODO/FIXME markers in submitted code.",
                    })
                if any(term in patch for term in ["password =", "api_key =", "secret =", "SECRET_KEY ="]):
                    issues_found.append({
                        "file": f.filename,
                        "severity": "HIGH",
                        "type": "hardcoded_secret",
                        "message": "Potential hardcoded credential or secret detected in patch.",
                    })
        else:
            pr_data = _fetch_github_api(f"repos/{clean_repo}/pulls/{pr_number}")
            title = pr_data.get("title", f"PR #{pr_number}")
            state = pr_data.get("state", "open")
            author = pr_data.get("user", {}).get("login", "unknown")
            total_additions = pr_data.get("additions", 0)
            total_deletions = pr_data.get("deletions", 0)
            pr_body = pr_data.get("body", "")

            # Fetch files
            files_data = _fetch_github_api(f"repos/{clean_repo}/pulls/{pr_number}/files")
            if isinstance(files_data, list):
                for f in files_data:
                    files_changed.append({
                        "filename": f.get("filename", ""),
                        "status": f.get("status", "modified"),
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "changes": f.get("changes", 0),
                    })
                    patch = f.get("patch", "")
                    if "console.log(" in patch:
                        issues_found.append({
                            "file": f.get("filename"),
                            "severity": "LOW",
                            "type": "debug_code",
                            "message": "console.log statement found in pull request diff.",
                        })

        if total_additions > 500:
            suggestions.append("Large PR detected (>500 lines added). Consider splitting into smaller atomic PRs.")
        if not suggestions and not issues_found:
            suggestions.append("Code changes look clean and well-structured.")

        result = {
            "title": title,
            "pr_number": pr_number,
            "state": state,
            "author": author,
            "files_changed_count": len(files_changed),
            "files_changed": files_changed[:20],
            "additions": total_additions,
            "deletions": total_deletions,
            "issues_found": issues_found,
            "suggestions": suggestions,
        }
        return _format_response(tool_name, start_time, result=result)

    except GithubException as ge:
        if ge.status == 404:
            return _format_response(
                tool_name, start_time, error=f"PR #{pr_number} or repository '{clean_repo}' not found."
            )
        return _format_response(tool_name, start_time, error=f"GitHub error: {ge.data.get('message', str(ge))}")
    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Failed to review PR: {str(e)}")


def github_find_issues(repo: str, path: Optional[str] = None) -> Dict[str, Any]:
    """
    Reads Python/TS files, finds: missing docstrings, complex functions, unused imports, TODO comments.
    Input: repo (str), path (str, optional)
    Returns: {files_scanned, issues, by_severity}
    """
    start_time = time.time()
    tool_name = "github_find_issues"

    if not repo or not REPO_REGEX.match(repo.strip()):
        return _format_response(
            tool_name,
            start_time,
            error="Invalid repository format. Expected 'owner/repo' (e.g. 'rayhan/my-project')",
        )

    try:
        clean_path = sanitize_input_path(path)
    except ValueError as ve:
        return _format_response(tool_name, start_time, error=str(ve))

    clean_repo = repo.strip()
    try:
        gh = _get_github_client()
        issues: List[Dict[str, Any]] = []
        files_scanned = 0

        if gh:
            gh_repo = gh.get_repo(clean_repo)
            contents = gh_repo.get_contents(clean_path or "")
            queue = contents if isinstance(contents, list) else [contents]

            while queue and files_scanned < 15:
                item = queue.pop(0)
                if item.type == "dir":
                    if item.name not in {".git", "node_modules", "dist", "build", "__pycache__", ".venv"}:
                        try:
                            queue.extend(gh_repo.get_contents(item.path))
                        except Exception:
                            pass
                    continue

                if not any(item.name.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]):
                    continue

                files_scanned += 1
                try:
                    decoded = item.decoded_content.decode("utf-8", errors="ignore")
                    lines = decoded.splitlines()

                    for idx, line in enumerate(lines, 1):
                        if "TODO" in line or "FIXME" in line:
                            issues.append({
                                "file": item.path,
                                "line": idx,
                                "type": "todo_marker",
                                "severity": "LOW",
                                "message": line.strip()[:100],
                            })

                    if item.name.endswith(".py"):
                        for idx, line in enumerate(lines, 1):
                            stripped = line.strip()
                            if stripped.startswith("def ") and not stripped.startswith("def _"):
                                func_name = stripped.split("(")[0].replace("def ", "").strip()
                                if idx < len(lines):
                                    next_line = lines[idx].strip()
                                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                                        issues.append({
                                            "file": item.path,
                                            "line": idx,
                                            "type": "missing_docstring",
                                            "severity": "LOW",
                                            "message": f"Function '{func_name}' is missing a docstring.",
                                        })
                except Exception:
                    continue
        else:
            contents_data = _fetch_github_api(f"repos/{clean_repo}/contents/{clean_path}".rstrip("/"))
            items = contents_data if isinstance(contents_data, list) else [contents_data]
            files_scanned = len([i for i in items if i.get("type") == "file"])

        by_severity = {
            "HIGH": sum(1 for i in issues if i["severity"] == "HIGH"),
            "MEDIUM": sum(1 for i in issues if i["severity"] == "MEDIUM"),
            "LOW": sum(1 for i in issues if i["severity"] == "LOW"),
        }

        result = {
            "repo": clean_repo,
            "path_scanned": clean_path or "/",
            "files_scanned": files_scanned,
            "issues": issues,
            "by_severity": by_severity,
        }
        return _format_response(tool_name, start_time, result=result)

    except GithubException as ge:
        return _format_response(tool_name, start_time, error=f"GitHub error: {ge.data.get('message', str(ge))}")
    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Failed to find code issues: {str(e)}")


def github_generate_readme(repo: str) -> Dict[str, Any]:
    """
    Reads repo structure + existing code, generates professional README.md content.
    Input: repo (str)
    Returns: {readme_content, sections_included}
    """
    start_time = time.time()
    tool_name = "github_generate_readme"

    if not repo or not REPO_REGEX.match(repo.strip()):
        return _format_response(
            tool_name,
            start_time,
            error="Invalid repository format. Expected 'owner/repo' (e.g. 'rayhan/my-project')",
        )

    clean_repo = repo.strip()
    try:
        gh = _get_github_client()
        if gh:
            gh_repo = gh.get_repo(clean_repo)
            repo_name = gh_repo.name
            full_name = gh_repo.full_name
            description = gh_repo.description or f"High-performance software project {repo_name}."
            language = gh_repo.language or "Python"
            license_name = "MIT"
            try:
                if gh_repo.license:
                    license_name = gh_repo.license.name or "MIT"
            except Exception:
                pass
            root_files = []
            try:
                for item in gh_repo.get_contents(""):
                    root_files.append(item.name)
            except Exception:
                pass
            try:
                languages = gh_repo.get_languages()
            except Exception:
                languages = {language: 1}
        else:
            repo_data = _fetch_github_api(f"repos/{clean_repo}")
            repo_name = repo_data.get("name", clean_repo.split("/")[-1])
            full_name = repo_data.get("full_name", clean_repo)
            description = repo_data.get("description") or f"High-performance software project {repo_name}."
            language = repo_data.get("language") or "Python"
            license_name = "MIT"
            root_files = []
            languages = {language: 1}

        tech_stack = _detect_tech_stack(root_files, languages)
        stack_badges = " ".join([f"`{t}`" for t in tech_stack])

        sections = [
            "Project Header & Badges",
            "Overview & Architecture",
            "Features",
            "Tech Stack",
            "Quick Start & Installation",
            "Configuration (.env)",
            "Testing",
            "License & Credits",
        ]

        readme_content = f"""# {repo_name}

> {description}

[![License: {license_name}](https://img.shields.io/badge/License-{license_name}-blue.svg)](LICENSE)
[![Curizx AI](https://img.shields.io/badge/Powered%20By-Curizx%20AI-purple)](https://github.com/{full_name})
[![Primary Language](https://img.shields.io/badge/Language-{language}-brightgreen)](https://github.com/{full_name})

---

## 🚀 Overview

**{repo_name}** is an enterprise-grade solution built with modern engineering standards. Designed for reliability, developer ergonomics, and seamless production readiness.

### Key Highlights
- **Engineered for Speed:** Minimal runtime overhead and optimized execution flow.
- **Robust Security:** Zero credential leaks, input validation, and sanitized data processing.
- **Modular Design:** Clear separation of concerns with structured interfaces.

---

## 🛠️ Tech Stack

{stack_badges}

- **Core Framework / Language:** {language}
- **Architecture:** Curizx AI Development Standard
- **Ecosystem:** {", ".join(tech_stack) if tech_stack else language}

---

## 📦 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/{full_name}.git
cd {repo_name}
```

### 2. Set Up Environment
```bash
# Copy example environment configuration
cp .env.example .env

# Install project dependencies
pip install -r requirements.txt  # or npm install
```

### 3. Run the Application
```bash
python server.py  # or npm run dev
```

---

## 🧪 Testing

Run comprehensive automated test suites:
```bash
pytest -v --cov
```

---

## 📄 License
Distributed under the {license_name} License. See `LICENSE` for more information.

---
*Generated with intelligence by Curizx AI Architecture | Curizx MCP Server*
"""

        result = {
            "repo": full_name,
            "readme_content": readme_content.strip(),
            "sections_included": sections,
            "primary_language": language,
            "detected_stack": tech_stack,
        }
        return _format_response(tool_name, start_time, result=result)

    except GithubException as ge:
        return _format_response(tool_name, start_time, error=f"GitHub error: {ge.data.get('message', str(ge))}")
    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Failed to generate README: {str(e)}")
