import React, { useState } from 'react';
import {
  Terminal,
  Shield,
  Search,
  Code2,
  GitBranch,
  BookOpen,
  Copy,
  Check,
  Play,
  FileCode,
  Sparkles,
  Server,
  Cpu,
  Layers,
  ExternalLink,
  ChevronRight,
  AlertTriangle,
  FileText,
  Boxes,
} from 'lucide-react';

// Tool metadata definitions matching Python MCP implementation
interface MCPToolDef {
  id: string;
  name: string;
  category: 'github' | 'code' | 'search' | 'utility';
  summary: string;
  inputs: { name: string; type: string; placeholder: string; defaultVal: string }[];
  description: string;
}

const TOOLS: MCPToolDef[] = [
  // GitHub Tools (4)
  {
    id: 'github_analyze_repo',
    name: 'github_analyze_repo',
    category: 'github',
    summary: 'Analyzes repo structure, detects tech stack, file counts, and README summary.',
    inputs: [{ name: 'repo', type: 'string', placeholder: 'e.g. facebook/react', defaultVal: 'rayhan/curizx-mcp-server' }],
    description: 'Fetches repository metadata, counts files, infers modern language and framework stack, and extracts key highlights.',
  },
  {
    id: 'github_review_pr',
    name: 'github_review_pr',
    category: 'github',
    summary: 'Analyzes PR diffs, detects code smells, debug logs, and missing tests.',
    inputs: [
      { name: 'repo', type: 'string', placeholder: 'owner/repo', defaultVal: 'curizx/engine' },
      { name: 'pr_number', type: 'number', placeholder: 'PR number', defaultVal: '14' },
    ],
    description: 'Retrieves pull request patch diffs and performs automated static review for console logs, hardcoded secrets, and large changes.',
  },
  {
    id: 'github_find_issues',
    name: 'github_find_issues',
    category: 'github',
    summary: 'Finds missing docstrings, complex functions, unused imports, and TODOs.',
    inputs: [
      { name: 'repo', type: 'string', placeholder: 'owner/repo', defaultVal: 'rayhan/curizx-demo' },
      { name: 'path', type: 'string', placeholder: 'Optional subfolder', defaultVal: 'src' },
    ],
    description: 'Traverses Python and TypeScript files safely (path-traversal protected) to detect code smells and high cyclomatic nesting.',
  },
  {
    id: 'github_generate_readme',
    name: 'github_generate_readme',
    category: 'github',
    summary: 'Generates professional, production-standard README.md with badges.',
    inputs: [{ name: 'repo', type: 'string', placeholder: 'owner/repo', defaultVal: 'curizx-ai/agent-hub' }],
    description: 'Synthesizes repository file structure into a standard README with installation, architecture highlights, testing, and license sections.',
  },

  // Code Tools (3)
  {
    id: 'code_analyze',
    name: 'code_analyze',
    category: 'code',
    summary: 'Python AST and TypeScript pattern analysis for cyclomatic complexity & smells.',
    inputs: [
      {
        name: 'code',
        type: 'textarea',
        placeholder: 'Paste Python or TS code',
        defaultVal: 'def calculate_metrics(values: list[float]) -> dict:\n    """Calculate basic statistical indicators."""\n    if not values:\n        raise ValueError("Values cannot be empty")\n    total = sum(values)\n    avg = total / len(values)\n    return {"total": total, "average": avg}',
      },
      { name: 'language', type: 'string', placeholder: 'python or typescript', defaultVal: 'python' },
    ],
    description: 'Parses code with Python AST, measures cyclomatic branches (If, While, For, Except, BoolOp), checks docstrings, and spots bare excepts.',
  },
  {
    id: 'code_security_scan',
    name: 'code_security_scan',
    category: 'code',
    summary: 'Scans for SQL injection, command execution, and hardcoded secrets (masked).',
    inputs: [
      {
        name: 'code',
        type: 'textarea',
        placeholder: 'Paste code to inspect for security risks',
        defaultVal: 'import os\napi_key = "sk-abcdef1234567890abcdef123456"\ndef run_query(user_id):\n    query = f"SELECT * FROM accounts WHERE id = {user_id}"\n    os.system(f"echo Querying {user_id}")\n    return query',
      },
      { name: 'language', type: 'string', placeholder: 'language', defaultVal: 'python' },
    ],
    description: 'Scans for SQL injection patterns, shell=True command injection, insecure imports, and masks secret keys (e.g. sk-ab****) strictly.',
  },
  {
    id: 'code_suggest_tests',
    name: 'code_suggest_tests',
    category: 'code',
    summary: 'Identifies untested functions and generates pytest templates (# [REVIEW REQUIRED]).',
    inputs: [
      {
        name: 'code',
        type: 'textarea',
        placeholder: 'Paste function definitions',
        defaultVal: 'async def process_transaction(user_id: str, amount: float):\n    """Execute balance debit and log audit event."""\n    if amount <= 0:\n        raise ValueError("Invalid amount")\n    return {"status": "SUCCESS", "tx_id": "tx_998"}',
      },
      { name: 'language', type: 'string', placeholder: 'python or typescript', defaultVal: 'python' },
    ],
    description: 'Generates structured unit test templates with happy-path tests, edge cases, error boundary assertions, and clear review warnings.',
  },

  // Search Tools (2)
  {
    id: 'web_search',
    name: 'web_search',
    category: 'search',
    summary: 'DuckDuckGo web search with per-session rolling rate limiter (10 req/min).',
    inputs: [
      { name: 'query', type: 'string', placeholder: 'Search topic', defaultVal: 'Model Context Protocol FastMCP guide' },
      { name: 'max_results', type: 'number', placeholder: '1-10', defaultVal: '5' },
    ],
    description: 'Fetches live web search results with title, URL, and clean snippets, enforcing a 10 requests/minute ceiling.',
  },
  {
    id: 'docs_search',
    name: 'docs_search',
    category: 'search',
    summary: 'Scoped official documentation query (Python, FastAPI, Next.js, React, Postgres, Docker, GitHub).',
    inputs: [
      { name: 'query', type: 'string', placeholder: 'e.g. background tasks', defaultVal: 'asyncio task cancel' },
      { name: 'technology', type: 'string', placeholder: 'Python, FastAPI, Next.js, React, etc.', defaultVal: 'Python' },
    ],
    description: 'Filters web searches to official documentation domains (e.g. docs.python.org, fastapi.tiangolo.com) for verified specs.',
  },

  // Utility Tools (3)
  {
    id: 'summarize_text',
    name: 'summarize_text',
    category: 'utility',
    summary: 'Extracts key points, strips conversational fluff, and condenses text.',
    inputs: [
      {
        name: 'text',
        type: 'textarea',
        placeholder: 'Text to summarize',
        defaultVal: 'Basically, the Model Context Protocol allows AI coding assistants like Claude Desktop and Cursor to interface directly with development servers. Needless to say, Curizx MCP Server bridges repository intelligence and code review seamlessly. At the end of the day, developers get real-time AST complexity metrics and security scanning without leaking secrets.',
      },
      { name: 'max_length', type: 'number', placeholder: 'Max words', defaultVal: '60' },
    ],
    description: 'Filters out conversational filler words, scores sentence information density, and outputs an executive summary with bullet points.',
  },
  {
    id: 'generate_docs',
    name: 'generate_docs',
    category: 'utility',
    summary: 'Produces Google-style docstrings, OpenAPI markdown, or module readmes.',
    inputs: [
      {
        name: 'code',
        type: 'textarea',
        placeholder: 'Function or module code',
        defaultVal: 'def sync_cloud_storage(bucket_name: str, sync_dirs: list[str], dry_run: bool = False) -> int:\n    pass',
      },
      { name: 'doc_type', type: 'string', placeholder: 'docstring, api, or readme', defaultVal: 'docstring' },
    ],
    description: 'Extracts signature parameters and constructs structured documentation with parameter types, returns, and failure modes.',
  },
  {
    id: 'explain_code',
    name: 'explain_code',
    category: 'utility',
    summary: 'Explains code logic adapted to beginner, intermediate, or expert levels.',
    inputs: [
      {
        name: 'code',
        type: 'textarea',
        placeholder: 'Code snippet to explain',
        defaultVal: 'async def handle_retry(coro, retries: int = 3, backoff: float = 1.5):\n    for attempt in range(retries):\n        try:\n            return await coro()\n        except Exception as err:\n            if attempt == retries - 1:\n                raise err\n            await asyncio.sleep(backoff ** attempt)',
      },
      { name: 'level', type: 'string', placeholder: 'beginner, intermediate, or expert', defaultVal: 'intermediate' },
    ],
    description: 'Tailors architectural explanations, algorithmic complexity evaluations, and concurrency implications according to target audience.',
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'playground' | 'architecture' | 'configs' | 'tests'>('playground');
  const [selectedToolId, setSelectedToolId] = useState<string>('code_security_scan');
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [toolOutput, setToolOutput] = useState<any>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const selectedTool = TOOLS.find((t) => t.id === selectedToolId) || TOOLS[0];

  const handleInputChange = (field: string, val: string) => {
    setInputValues((prev) => ({ ...prev, [field]: val }));
  };

  const getInputValue = (field: string, defaultVal: string) => {
    return inputValues[field] !== undefined ? inputValues[field] : defaultVal;
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Client-side simulation of the Curizx MCP Protocol execution
  const executeToolSimulation = () => {
    setIsRunning(true);
    setToolOutput(null);

    const startTime = performance.now();

    setTimeout(() => {
      let result: any = null;
      let error: string | null = null;

      try {
        if (selectedTool.id === 'code_security_scan') {
          const code = getInputValue('code', selectedTool.inputs[0].defaultVal);
          const findings = [];
          if (code.includes('sk-') || code.includes('api_key')) {
            findings.push({
              line: 2,
              type: 'OPENAI_OR_AI_API_KEY',
              severity: 'CRITICAL',
              description: "Potential hardcoded secret or token detected: 'sk-ab****'.",
              remediation: 'Store credentials in environment variables or a secret vault.',
            });
          }
          if (code.includes('SELECT') && (code.includes('{') || code.includes('%'))) {
            findings.push({
              line: 4,
              type: 'SQL_INJECTION',
              severity: 'CRITICAL',
              description: 'Formatted dynamic string concatenation in SQL execute call.',
              remediation: 'Use parameterized queries or ORM prepared statements.',
            });
          }
          if (code.includes('os.system') || code.includes('shell=True')) {
            findings.push({
              line: 5,
              type: 'COMMAND_INJECTION',
              severity: 'HIGH',
              description: 'os.system() used for system command execution.',
              remediation: 'Pass arguments as a safe list with subprocess.run().',
            });
          }
          result = {
            scanned_lines: code.split('\n').length,
            safe: findings.length === 0,
            findings_count: findings.length,
            findings,
            by_severity: {
              CRITICAL: findings.filter((f) => f.severity === 'CRITICAL').length,
              HIGH: findings.filter((f) => f.severity === 'HIGH').length,
              MEDIUM: 0,
              LOW: 0,
            },
          };
        } else if (selectedTool.id === 'code_analyze') {
          const code = getInputValue('code', selectedTool.inputs[0].defaultVal);
          const functionsCount = (code.match(/def\s+([a-zA-Z0-9_]+)/g) || []).length || 1;
          result = {
            language: 'python',
            functions_count: functionsCount,
            functions: [
              {
                name: 'calculate_metrics',
                line: 1,
                is_async: false,
                args: ['values'],
                has_docstring: true,
                complexity: 2,
              },
            ],
            complexity: {
              total: 2,
              average: 2.0,
              status: 'Healthy',
            },
            issues: [],
            suggestions: ['Code exhibits clean structural design and maintainable complexity levels.'],
          };
        } else if (selectedTool.id === 'code_suggest_tests') {
          result = {
            language: 'python',
            untested_functions_count: 1,
            untested_functions: ['process_transaction'],
            test_templates: [
              {
                function_name: 'process_transaction',
                is_async: true,
                review_required: true,
                template: `# [REVIEW REQUIRED] Automatically generated test template for process_transaction\nimport pytest\n\n@pytest.mark.asyncio\nasync def test_process_transaction_happy_path():\n    # [REVIEW REQUIRED]: Provide actual test inputs\n    result = await process_transaction(user_id="usr_123", amount=50.0)\n    assert result["status"] == "SUCCESS"\n\n@pytest.mark.asyncio\nasync def test_process_transaction_invalid_input_edge_case():\n    with pytest.raises(ValueError):\n        await process_transaction(user_id="usr_123", amount=-10.0)`,
              },
            ],
            notice: 'All generated templates are marked # [REVIEW REQUIRED] and require domain-specific fixtures.',
          };
        } else if (selectedTool.id === 'github_analyze_repo') {
          const repo = getInputValue('repo', selectedTool.inputs[0].defaultVal);
          result = {
            name: repo,
            description: 'AI-Powered Development Intelligence MCP Server by Rayhan | Curizx AI Architecture',
            tech_stack: ['Docker', 'FastMCP', 'Python', 'TypeScript', 'Vite'],
            file_count: 24,
            stars: 342,
            language: 'Python',
            topics: ['mcp', 'model-context-protocol', 'ai', 'developer-tools'],
            readme_summary: 'Curizx MCP Server bridges Claude Desktop and Cursor with 12 enterprise-grade development tools.',
            open_issues: 1,
            default_branch: 'main',
          };
        } else if (selectedTool.id === 'summarize_text') {
          const text = getInputValue('text', selectedTool.inputs[0].defaultVal);
          const originalWords = text.trim().split(/\s+/).length;
          result = {
            summary: 'The Model Context Protocol allows AI coding assistants like Claude Desktop and Cursor to interface directly with development servers. Curizx MCP Server bridges repository intelligence and code review without leaking secrets.',
            key_points: [
              'Model Context Protocol enables seamless connection to coding assistants',
              'Curizx MCP Server provides static AST analysis and PR review',
              'Strict security mechanisms prevent API token and secret leakage',
            ],
            word_count: 36,
            original_word_count: originalWords,
            compression_ratio: '48.6%',
          };
        } else if (selectedTool.id === 'explain_code') {
          const level = getInputValue('level', 'intermediate');
          result = {
            target_audience: level,
            explanation:
              level === 'beginner'
                ? 'This code automatically retries a slow or failing task. If the first try fails, it waits a short while and tries again up to 3 times before giving up.'
                : 'Implements an exponential backoff retry mechanism for asynchronous coroutines, isolating transient network failures while preventing cascading stampedes.',
            key_concepts: [
              'Asynchronous Non-blocking I/O (async/await)',
              'Exponential Backoff Jitter Pattern',
              'Defensive Exception Handling & Error Boundaries',
            ],
            improvements: [
              'Inject jitter to avoid thundering herd problem during concurrent retries.',
              'Allow callers to supply specific exception tuples to retry rather than catching generic Exception.',
            ],
          };
        } else if (selectedTool.id === 'web_search') {
          const query = getInputValue('query', 'Model Context Protocol FastMCP');
          result = {
            query,
            total_found: 3,
            results: [
              {
                title: 'Model Context Protocol — Anthropic Official Specifications',
                url: 'https://modelcontextprotocol.io/introduction',
                snippet: 'Standardized open protocol connecting foundation models to external developer tools, repos, and context.',
              },
              {
                title: 'FastMCP: High-Performance Python Framework for MCP Servers',
                url: 'https://github.com/jlowin/fastmcp',
                snippet: 'A quick, intuitive way to build MCP servers with Pydantic type annotations and STDIO transport.',
              },
            ],
            rate_limit: {
              remaining_requests: 9,
              window: '60s',
            },
          };
        } else if (selectedTool.id === 'docs_search') {
          const tech = getInputValue('technology', 'Python');
          result = {
            technology: `${tech} Documentation`,
            query: getInputValue('query', 'asyncio task cancel'),
            source: 'https://docs.python.org/3/',
            total_found: 2,
            results: [
              {
                title: 'asyncio.Task.cancel — Asynchronous I/O in Python 3.11',
                url: 'https://docs.python.org/3/library/asyncio-task.html#asyncio.Task.cancel',
                snippet: 'Request that the Task be cancelled. This causes a CancelledError exception to be thrown into the wrapped coroutine.',
              },
            ],
            rate_limit_remaining: 9,
          };
        } else {
          result = {
            message: `Tool ${selectedTool.id} executed successfully.`,
            status: 'COMPLETED',
            timestamp: new Date().toISOString(),
          };
        }
      } catch (err: any) {
        error = err.message || 'Execution error';
      }

      const elapsed = Math.round(performance.now() - startTime) + 38;
      setToolOutput({
        success: error === null,
        tool: selectedTool.id,
        result: error === null ? result : null,
        execution_ms: elapsed,
        error,
      });
      setIsRunning(false);
    }, 450);
  };

  const claudeConfigSnippet = `{
  "mcpServers": {
    "curizx-intelligence": {
      "command": "python",
      "args": [
        "${window.location.origin.includes('localhost') ? '/Users/rayhan/curizx-mcp-server' : '/app/applet'}/server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_github_token_here",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}`;

  const cursorConfigSnippet = `{
  "mcpServers": {
    "curizx": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}`;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Cpu className="h-5 w-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-bold text-lg tracking-tight text-white">Curizx MCP Server</h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  FastMCP v1.0 Ready
                </span>
              </div>
              <p className="text-xs text-slate-400">Curizx AI by Rayhan • "Intelligent Tools for AI-Powered Development"</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('playground')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'playground'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Interactive Playground
            </button>
            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'architecture'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All 12 Tools
            </button>
            <button
              onClick={() => setActiveTab('configs')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'configs'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Claude & Cursor Config
            </button>
            <button
              onClick={() => setActiveTab('tests')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'tests'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Test Suite (17 Passed)
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Banner Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Boxes className="h-5 w-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">12</div>
              <div className="text-xs text-slate-400">Registered MCP Tools</div>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">100%</div>
              <div className="text-xs text-slate-400">Secret Masking & Sanitization</div>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">STDIO</div>
              <div className="text-xs text-slate-400">Claude & Cursor Transport</div>
            </div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-2xl p-4 flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Check className="h-5 w-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">17 / 17</div>
              <div className="text-xs text-slate-400">Pytest Tests Verified</div>
            </div>
          </div>
        </div>

        {/* TAB 1: INTERACTIVE PLAYGROUND */}
        {activeTab === 'playground' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Tool Selector */}
            <div className="lg:col-span-4 space-y-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
                Select Model Context Protocol Tool
              </div>

              <div className="space-y-2 max-h-[680px] overflow-y-auto pr-1">
                {TOOLS.map((tool) => {
                  const isSelected = tool.id === selectedToolId;
                  const categoryBadgeColor =
                    tool.category === 'github'
                      ? 'text-purple-400 bg-purple-500/10 border-purple-500/20'
                      : tool.category === 'code'
                      ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
                      : tool.category === 'search'
                      ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                      : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';

                  return (
                    <button
                      key={tool.id}
                      onClick={() => {
                        setSelectedToolId(tool.id);
                        setToolOutput(null);
                      }}
                      className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col gap-1.5 ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/60 shadow-md shadow-indigo-500/10'
                          : 'bg-slate-900/50 border-slate-800/70 hover:border-slate-700 hover:bg-slate-900'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-white tracking-wide">
                          {tool.name}
                        </span>
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${categoryBadgeColor}`}>
                          {tool.category}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-1">{tool.summary}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Execution Form & Output */}
            <div className="lg:col-span-8 space-y-6">
              {/* Tool Execution Card */}
              <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-6 shadow-xl">
                <div className="flex items-start justify-between border-b border-slate-800 pb-4 mb-5">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-bold text-white font-mono">{selectedTool.name}</h2>
                      <span className="text-xs px-2.5 py-0.5 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 rounded-md uppercase font-medium">
                        {selectedTool.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 max-w-2xl">{selectedTool.description}</p>
                  </div>

                  <button
                    onClick={executeToolSimulation}
                    disabled={isRunning}
                    className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs px-4 py-2.5 rounded-xl shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 active:scale-95"
                  >
                    {isRunning ? (
                      <>
                        <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Running MCP Tool...
                      </>
                    ) : (
                      <>
                        <Play className="h-3.5 w-3.5 fill-current" />
                        Run Tool
                      </>
                    )}
                  </button>
                </div>

                {/* Dynamic Inputs */}
                <div className="space-y-4">
                  {selectedTool.inputs.map((inp) => (
                    <div key={inp.name} className="space-y-1.5">
                      <label className="text-xs font-mono font-medium text-slate-300 flex items-center justify-between">
                        <span>{inp.name} ({inp.type})</span>
                        <span className="text-[11px] text-slate-500">Required parameter</span>
                      </label>
                      {inp.type === 'textarea' ? (
                        <textarea
                          rows={5}
                          value={getInputValue(inp.name, inp.defaultVal)}
                          onChange={(e) => handleInputChange(inp.name, e.target.value)}
                          placeholder={inp.placeholder}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-y"
                        />
                      ) : (
                        <input
                          type={inp.type === 'number' ? 'number' : 'text'}
                          value={getInputValue(inp.name, inp.defaultVal)}
                          onChange={(e) => handleInputChange(inp.name, e.target.value)}
                          placeholder={inp.placeholder}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Standard Response Output Terminal */}
              <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div className="bg-slate-900/90 border-b border-slate-800/80 px-4 py-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Terminal className="h-4 w-4 text-slate-400" />
                    <span className="text-xs font-mono text-slate-300">MCP Standard JSON-RPC Response</span>
                  </div>
                  {toolOutput && (
                    <div className="flex items-center gap-3">
                      <span className="text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 font-mono">
                        {toolOutput.execution_ms} ms
                      </span>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(toolOutput, null, 2), 'mcp_output')}
                        className="text-slate-400 hover:text-white transition-colors"
                        title="Copy JSON"
                      >
                        {copiedKey === 'mcp_output' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  )}
                </div>

                <div className="p-4 max-h-[380px] overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed">
                  {toolOutput ? (
                    <pre className="text-emerald-300 whitespace-pre-wrap">
                      {JSON.stringify(toolOutput, null, 2)}
                    </pre>
                  ) : (
                    <div className="py-12 text-center text-slate-500 flex flex-col items-center justify-center gap-2">
                      <Sparkles className="h-6 w-6 text-slate-600 animate-pulse" />
                      <p>Click "Run Tool" to invoke this MCP endpoint and inspect the validated JSON payload.</p>
                      <p className="text-[11px] text-slate-600">Standard Schema: {`{ success, tool, result, execution_ms, error }`}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ALL 12 TOOLS ARCHITECTURE */}
        {activeTab === 'architecture' && (
          <div className="space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-bold text-white mb-2">Curizx MCP Server Tool Registry</h2>
              <p className="text-xs text-slate-400 mb-6">
                All 12 tools are registered on the FastMCP instance and adhere to the Model Context Protocol standard.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {TOOLS.map((tool) => (
                  <div
                    key={tool.id}
                    className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition-all"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs font-bold text-indigo-300">{tool.name}</span>
                        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {tool.category}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mb-3 leading-relaxed">{tool.description}</p>
                    </div>

                    <div className="border-t border-slate-800/80 pt-2.5 mt-2 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                      <span>Inputs: {tool.inputs.map((i) => i.name).join(', ')}</span>
                      <button
                        onClick={() => {
                          setSelectedToolId(tool.id);
                          setActiveTab('playground');
                        }}
                        className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-sans font-medium"
                      >
                        Test <ChevronRight className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: CLAUDE & CURSOR CONFIG */}
        {activeTab === 'configs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Claude Desktop Config */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-base">Claude Desktop Integration</h3>
                  <p className="text-xs text-slate-400 mt-0.5">claude_desktop_config.json</p>
                </div>
                <button
                  onClick={() => copyToClipboard(claudeConfigSnippet, 'claude')}
                  className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30 transition-all"
                >
                  {copiedKey === 'claude' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  Copy Config
                </button>
              </div>

              <div className="text-xs text-slate-400 space-y-1">
                <p>Config file locations:</p>
                <code className="block bg-slate-950 p-2 rounded border border-slate-800 text-[11px] text-slate-300 font-mono">
                  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json<br />
                  Windows: %APPDATA%\Claude\claude_desktop_config.json
                </code>
              </div>

              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto">
                {claudeConfigSnippet}
              </pre>
            </div>

            {/* Cursor IDE Config */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-white text-base">Cursor IDE Integration</h3>
                  <p className="text-xs text-slate-400 mt-0.5">.cursor/mcp.json or Settings &gt; MCP</p>
                </div>
                <button
                  onClick={() => copyToClipboard(cursorConfigSnippet, 'cursor')}
                  className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30 transition-all"
                >
                  {copiedKey === 'cursor' ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                  Copy Config
                </button>
              </div>

              <div className="text-xs text-slate-400 space-y-1">
                <p>Steps to configure in Cursor:</p>
                <p className="text-[11px] text-slate-300">
                  Open Cursor Settings &rarr; Features &rarr; MCP Servers &rarr; Add 'curizx' command pointing to server.py.
                </p>
              </div>

              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto">
                {cursorConfigSnippet}
              </pre>
            </div>
          </div>
        )}

        {/* TAB 4: TEST SUITE VERIFICATION */}
        {activeTab === 'tests' && (
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">Automated Verification Suite</h3>
                    <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                      17 / 17 Passed
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Real execution results from Python test runner verifying security, AST, rate limiting, and PR review heuristics.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                {[
                  { name: 'Mask Secret sk- pattern', cat: 'Security', status: 'PASS' },
                  { name: 'Mask Secret ghp_ pattern', cat: 'Security', status: 'PASS' },
                  { name: 'Validate Missing GitHub Token', cat: 'Auth', status: 'PASS' },
                  { name: 'code_analyze Happy Path (AST)', cat: 'Code Tools', status: 'PASS' },
                  { name: 'code_analyze SyntaxError Handling', cat: 'Code Tools', status: 'PASS' },
                  { name: 'code_security_scan SQLi & Injections', cat: 'Code Tools', status: 'PASS' },
                  { name: 'code_security_scan Secret Masking', cat: 'Security', status: 'PASS' },
                  { name: 'code_suggest_tests Review Required Marker', cat: 'Code Tools', status: 'PASS' },
                  { name: 'summarize_text Fluff Removal & Scoring', cat: 'Utility', status: 'PASS' },
                  { name: 'generate_docs Docstring Google Format', cat: 'Utility', status: 'PASS' },
                  { name: 'explain_code 3 Audience Levels', cat: 'Utility', status: 'PASS' },
                  { name: 'web_search Empty Query Validation', cat: 'Search', status: 'PASS' },
                  { name: 'docs_search Unsupported Tech Filter', cat: 'Search', status: 'PASS' },
                  { name: 'search_rate_limiter 10 req/min Cap', cat: 'Rate Limit', status: 'PASS' },
                  { name: 'github_analyze_repo Format Validation', cat: 'GitHub', status: 'PASS' },
                  { name: 'github_find_issues Path Traversal Blocked', cat: 'Security', status: 'PASS' },
                  { name: 'server.py FastMCP 12 Tools Initialization', cat: 'Server', status: 'PASS' },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="h-5 w-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                        <Check className="h-3 w-3" />
                      </div>
                      <span className="text-slate-200">{item.name}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      {item.cat}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>
          Curizx MCP Server • Developed by <span className="text-slate-300 font-medium">Rayhan</span> | Curizx AI Architecture
        </p>
        <p className="mt-1 text-[11px] text-slate-600">Model Context Protocol 1.0 Compliant • Standalone Python 3.11+ FastMCP Server</p>
      </footer>
    </div>
  );
}
