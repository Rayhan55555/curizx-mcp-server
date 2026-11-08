# Curizx MCP Server

[![Curizx AI](https://img.shields.io/badge/Curizx%20AI-by%20Rayhan-6366f1?style=for-the-badge&logo=probot&logoColor=white)](https://github.com/rayhan)
[![Protocol: Model Context Protocol](https://img.shields.io/badge/MCP-1.0%20Compliant-10b981?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f59e0b?style=for-the-badge)](LICENSE)
[![Tests: 17 Passed](https://img.shields.io/badge/Tests-17%20Passed-22c55e?style=for-the-badge&logo=pytest&logoColor=white)](tests/)

> **"Intelligent Tools for AI-Powered Development"**  
> *A standalone Model Context Protocol (MCP) server engineered by Rayhan | Curizx AI Architecture.*

---

## 💡 What it Does

**Curizx MCP Server** connects any AI assistant (Claude, Cursor, Windsurf) to enterprise-grade developer capabilities. It empowers coding agents with deep GitHub repository intelligence, static AST code analysis, real-time security vulnerability scanning, rate-limited web searches, official doc querying, and automated test generation.

---

## 🎬 Demo

```
┌───────────────────────────────────────────────────────────────┐
│                      CURIZX MCP SERVER                        │
│                                                               │
│   Claude / Cursor ──[ STDIO JSON-RPC ]──> FastMCP Server      │
│                                                │              │
│       ┌─────────────────┬──────────────────────┴───────┐      │
│       ▼                 ▼                             ▼      │
│   GitHub Tools     Code Intelligence             Search & Docs│
│   - Analyze Repo   - AST Complexity Analysis     - Web Search │
│   - Review PR      - Security Vulnerability Scan - Docs Search│
│   - Find Issues    - Automated Pytest Generator               │
│   - Gen README     - Code Explainer (3 levels)                │
└───────────────────────────────────────────────────────────────┘
```
*(Demo GIF: assets/curizx-demo.gif placeholder)*

---

## ⚡ Quick Install

Get up and running in 3 commands:

```bash
git clone https://github.com/rayhan/curizx-mcp-server.git
cd curizx-mcp-server && pip install -r requirements.txt
python server.py
```

---

## 🤖 Client Configurations

### 1. Claude Desktop Config
Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "curizx-intelligence": {
      "command": "python",
      "args": [
        "/ABSOLUTE/PATH/TO/curizx-mcp-server/server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 2. Cursor IDE Config
Add to `.cursor/mcp.json` or through Cursor Settings > MCP Servers:

```json
{
  "mcpServers": {
    "curizx": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

---

## 🛠️ All 12 MCP Tools

Every tool strictly returns execution time in milliseconds and never leaks secret credentials.

| Category | Tool | Input Parameters | What it Does |
|---|---|---|---|
| **GitHub** | `github_analyze_repo` | `repo` (str) | Fetches repo info, detects tech stack, counts files, reads README summary |
| **GitHub** | `github_review_pr` | `repo` (str), `pr_number` (int) | Gets PR diff, changed files, analyzes code quality issues and smells |
| **GitHub** | `github_find_issues` | `repo` (str), `path` (str, optional) | Scans for missing docstrings, complex functions, unused imports, TODOs |
| **GitHub** | `github_generate_readme` | `repo` (str) | Reads repo structure and produces professional standard README.md |
| **Code** | `code_analyze` | `code` (str), `language` (str) | Full AST cyclomatic complexity analysis, function metrics, code smells |
| **Code** | `code_security_scan` | `code` (str), `language` (str) | Scans for SQLi, hardcoded secrets, command injection (secrets masked) |
| **Code** | `code_suggest_tests` | `code` (str), `language` (str) | Generates comprehensive `pytest` templates marked `# [REVIEW REQUIRED]` |
| **Search** | `web_search` | `query` (str), `max_results` (int=5) | DuckDuckGo search with per-session rate limit (10 req/min) |
| **Search** | `docs_search` | `query` (str), `technology` (str) | Scoped search for Python, FastAPI, Next.js, React, Postgres, Docker, GitHub |
| **Utility** | `summarize_text` | `text` (str), `max_length` (int=200) | Extracts key points, strips conversational fluff, scores sentence importance |
| **Utility** | `generate_docs` | `code` (str), `doc_type` (str) | Generates Google-style `docstring`, REST `api` spec, or module `readme` |
| **Utility** | `explain_code` | `code` (str), `level` (str) | Explains code logic for `beginner`, `intermediate`, or `expert` developers |

---

## 🔒 Security Standards

1. **Zero Credential Exposure:** Secrets like OpenAI, Anthropic, or GitHub tokens are strictly masked (e.g. `sk-ab****`, `ghp_****`).
2. **Path Traversal Guards:** All file paths are sanitized against `../` directory escapes.
3. **No Shell Invocations:** Zero `shell=True` or arbitrary command executions.
4. **Rate Limiting:** Rolling 60-second window protecting search endpoints.

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env`:

```bash
# GitHub Personal Access Token (for private repos & 5000 req/hr rate limit)
GITHUB_TOKEN="ghp_your_token_here"

# Server Host and Port
MCP_HOST="0.0.0.0"
MCP_PORT=8000

# Logging Level
LOG_LEVEL="INFO"

# Environment
ENVIRONMENT="production"
```

---

## 🧪 Development & Testing

```bash
# Run standalone verification test suite
python run_tests.py

# Run pytest with async support
pytest -v --cov=tools
```

---

## 🐳 Docker Deployment

```bash
cd docker
docker-compose up -d --build
```

---

## 📜 License

Distributed under the **MIT License**. Created with excellence by **Rayhan** | *Curizx AI Architecture*.
