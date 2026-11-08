# Curizx MCP Server — Setup & Integration Guide

**Brand:** Curizx AI by Rayhan  
**Product:** `curizx-mcp-server`  
**Tagline:** "Intelligent Tools for AI-Powered Development"

This guide covers integrating the **Curizx MCP Server** into your development environments, including Claude Desktop, Cursor, Windsurf, Docker, and local Python environments.

---

## 📋 Prerequisites
- Python 3.11+
- Git
- (Optional) Docker & Docker Compose
- (Optional) GitHub Personal Access Token (for extended API limits)

---

## ⚡ 1. Local Python Setup

```bash
# 1. Clone repository
git clone https://github.com/rayhan/curizx-mcp-server.git
cd curizx-mcp-server

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your GITHUB_TOKEN if desired
```

---

## 🤖 2. Claude Desktop Integration

Locate your Claude Desktop configuration file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add `curizx` to the `mcpServers` object:

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

Restart Claude Desktop. The hammer 🔨 icon will show all 12 Curizx development intelligence tools available.

---

## 💻 3. Cursor IDE Integration

1. Open Cursor Settings (`Ctrl+Shift+J` or `Cmd+Shift+J`).
2. Navigate to **Features** > **MCP Servers**.
3. Click **Add New MCP Server**:
   - **Name:** `curizx-mcp`
   - **Type:** `command`
   - **Command:** `python /ABSOLUTE/PATH/TO/curizx-mcp-server/server.py`

Or add via `.cursor/mcp.json` in your workspace root:

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

## 🐳 4. Docker Deployment

```bash
# Build and run containerized server
cd docker
docker-compose up -d --build

# View server logs
docker-compose logs -f
```

---

## 🧪 5. Running Automated Verification

```bash
# Run full suite
python run_tests.py

# Or run pytest
pytest -v
```

All 17 core tests will verify AST analysis, token masking, security pattern scanning, rate limiting, and PR review heuristics.
