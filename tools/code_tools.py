"""
Code Intelligence & Security Tools for Curizx MCP Server.
Covers:
5. code_analyze
6. code_security_scan
7. code_suggest_tests
"""

import ast
import re
import time
from typing import Any, Dict, List, Optional
from core.logger import logger
from core.auth import mask_secret


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


def _calculate_python_complexity(node: ast.AST) -> int:
    """Calculates McCabe cyclomatic complexity for an AST function node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def code_analyze(code: str, language: str = "python") -> Dict[str, Any]:
    """
    AST analysis for Python and pattern analysis for TypeScript/JavaScript.
    Evaluates cyclomatic complexity, functions, potential code smells and suggestions.
    Input: code (str), language (str)
    Returns: {language, functions, complexity, issues, suggestions}
    """
    start_time = time.time()
    tool_name = "code_analyze"

    if not code or not code.strip():
        return _format_response(tool_name, start_time, error="Code parameter cannot be empty.")

    lang = language.lower().strip()
    functions_info: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    suggestions: List[str] = []

    if lang in ("python", "py"):
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            return _format_response(
                tool_name,
                start_time,
                error=f"Python SyntaxError at line {se.lineno}, col {se.offset}: {se.msg}",
            )

        total_complexity = 0

        # AST Walker for functions, classes, imports
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_complexity = _calculate_python_complexity(node)
                total_complexity += func_complexity
                has_docstring = ast.get_docstring(node) is not None
                args = [arg.arg for arg in node.args.args]
                
                # Check for *args, **kwargs
                if node.args.vararg:
                    args.append(f"*{node.args.vararg.arg}")
                if node.args.kwarg:
                    args.append(f"**{node.args.kwarg.arg}")

                func_data = {
                    "name": node.name,
                    "line": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "args": args,
                    "has_docstring": has_docstring,
                    "complexity": func_complexity,
                }
                functions_info.append(func_data)

                if func_complexity > 10:
                    issues.append({
                        "line": node.lineno,
                        "type": "high_cyclomatic_complexity",
                        "severity": "MEDIUM",
                        "message": f"Function '{node.name}' has cyclomatic complexity of {func_complexity} (threshold: 10). Consider decomposing into smaller helper functions.",
                    })

                if not has_docstring and not node.name.startswith("_"):
                    issues.append({
                        "line": node.lineno,
                        "type": "missing_docstring",
                        "severity": "LOW",
                        "message": f"Public function '{node.name}' has no docstring.",
                    })

                if len(args) > 5:
                    issues.append({
                        "line": node.lineno,
                        "type": "too_many_parameters",
                        "severity": "LOW",
                        "message": f"Function '{node.name}' accepts {len(args)} parameters. Consider grouping into a dataclass or Pydantic model.",
                    })

            # Check for bare except
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "line": node.lineno,
                        "type": "bare_except",
                        "severity": "HIGH",
                        "message": "Bare 'except:' caught. Catch specific exceptions (e.g. Exception or ValueError) instead.",
                    })

            # Check for wildcard imports
            elif isinstance(node, ast.ImportFrom):
                if any(alias.name == "*" for alias in node.names):
                    issues.append({
                        "line": node.lineno,
                        "type": "wildcard_import",
                        "severity": "MEDIUM",
                        "message": f"Wildcard import 'from {node.module} import *' pollutes the global namespace.",
                    })

        avg_complexity = round(total_complexity / max(1, len(functions_info)), 2)

        # General suggestions
        if not functions_info:
            suggestions.append("No functions detected. Consider structuring procedural script into modular functions.")
        if any(i["type"] == "bare_except" for i in issues):
            suggestions.append("Avoid bare except blocks to prevent swallowing SystemExit or KeyboardInterrupt.")
        if avg_complexity > 5:
            suggestions.append("Average function complexity is elevated. Increase unit test coverage for branching logic.")
        if not suggestions:
            suggestions.append("Code exhibits clean structural design and maintainable complexity levels.")

        result = {
            "language": "python",
            "functions_count": len(functions_info),
            "functions": functions_info,
            "complexity": {
                "total": total_complexity,
                "average": avg_complexity,
                "status": "Healthy" if avg_complexity <= 5 else "Needs Refactoring",
            },
            "issues": issues,
            "suggestions": suggestions,
        }
        return _format_response(tool_name, start_time, result=result)

    elif lang in ("typescript", "ts", "javascript", "js", "tsx", "jsx"):
        lines = code.splitlines()
        # Heuristic pattern analysis for TypeScript/JavaScript
        fn_pattern = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)")
        arrow_pattern = re.compile(r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>")
        
        for idx, line in enumerate(lines, 1):
            m = fn_pattern.search(line) or arrow_pattern.search(line)
            if m:
                fn_name = m.group(1)
                args = [a.strip() for a in m.group(2).split(",") if a.strip()]
                functions_info.append({
                    "name": fn_name,
                    "line": idx,
                    "args": args,
                    "complexity": 2 if "if" in line or "?" in line else 1,
                })

            if "console.log" in line:
                issues.append({
                    "line": idx,
                    "type": "console_log",
                    "severity": "LOW",
                    "message": "console.log found in source code.",
                })

            if "any" in line and (":" in line or "as" in line):
                issues.append({
                    "line": idx,
                    "type": "ts_any_type",
                    "severity": "LOW",
                    "message": "Use of explicit 'any' type weakens TypeScript type-safety.",
                })

        suggestions.append("Ensure strict TypeScript compilation (`--strict`) is enabled.")
        if any(i["type"] == "console_log" for i in issues):
            suggestions.append("Replace console.log with a production logger or strip in production build.")

        result = {
            "language": lang,
            "functions_count": len(functions_info),
            "functions": functions_info,
            "complexity": {
                "estimated_level": "Normal" if len(issues) < 4 else "Moderate",
            },
            "issues": issues,
            "suggestions": suggestions,
        }
        return _format_response(tool_name, start_time, result=result)

    else:
        return _format_response(
            tool_name,
            start_time,
            error=f"Unsupported language '{language}'. Supported: python, typescript, javascript.",
        )


def code_security_scan(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Scans for: SQL injection patterns, hardcoded secrets, command injection, insecure imports, weak crypto.
    Returns: {findings, by_severity, safe: bool}
    NEVER returns actual secret values (masks secrets safely).
    """
    start_time = time.time()
    tool_name = "code_security_scan"

    if not code or not code.strip():
        return _format_response(tool_name, start_time, error="Code parameter cannot be empty.")

    findings: List[Dict[str, Any]] = []
    lines = code.splitlines()

    # Security check patterns
    secret_patterns = [
        (re.compile(r"""(?:api_key|apikey|secret|token|password|passwd|auth_token)\s*=\s*['"]([a-zA-Z0-9_\-\.]{12,})['"]""", re.IGNORECASE), "HARDCODED_SECRET", "HIGH"),
        (re.compile(r"""(ghp_[a-zA-Z0-9]{20,})"""), "GITHUB_TOKEN", "CRITICAL"),
        (re.compile(r"""(sk-[a-zA-Z0-9]{20,})"""), "OPENAI_OR_AI_API_KEY", "CRITICAL"),
        (re.compile(r"""(AKIA[0-9A-Z]{16})"""), "AWS_ACCESS_KEY_ID", "CRITICAL"),
    ]

    sql_patterns = [
        (re.compile(r"""execute\s*\(\s*f["'].*SELECT.*\{.*\}""", re.IGNORECASE), "SQL_INJECTION", "CRITICAL", "f-string formatted raw SQL query in execute() call."),
        (re.compile(r"""execute\s*\(\s*["'].*%s.*["']\s*%\s*""", re.IGNORECASE), "SQL_INJECTION", "HIGH", "String interpolation % used in SQL execute statement."),
        (re.compile(r"""(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:request|input|param)""", re.IGNORECASE), "SQL_INJECTION", "CRITICAL", "String concatenation with user parameters in SQL query."),
    ]

    command_patterns = [
        (re.compile(r"""subprocess\.(?:Popen|run|call|check_output)\s*\(.*shell\s*=\s*True""", re.IGNORECASE), "COMMAND_INJECTION", "HIGH", "subprocess invocation with shell=True."),
        (re.compile(r"""os\.system\s*\(""", re.IGNORECASE), "COMMAND_INJECTION", "HIGH", "os.system() used for system command execution. Use subprocess with argument array instead."),
        (re.compile(r"""\beval\s*\(""", re.IGNORECASE), "CODE_INJECTION", "CRITICAL", "eval() execution of dynamic strings."),
        (re.compile(r"""\bexec\s*\(""", re.IGNORECASE), "CODE_INJECTION", "CRITICAL", "exec() execution of arbitrary code."),
    ]

    insecure_import_patterns = [
        (re.compile(r"""import\s+pickle\b|from\s+pickle\b"""), "INSECURE_DESERIALIZATION", "MEDIUM", "pickle is insecure against arbitrary code execution when untrusted data is loaded. Use JSON or safe serialization."),
        (re.compile(r"""import\s+telnetlib\b|from\s+telnetlib\b"""), "INSECURE_PROTOCOL", "HIGH", "telnetlib transmits unencrypted credentials over network."),
    ]

    crypto_patterns = [
        (re.compile(r"""hashlib\.md5\s*\("""), "WEAK_CRYPTO", "MEDIUM", "MD5 is cryptographically broken and prone to collision attacks. Use SHA256 or bcrypt/argon2 for passwords."),
        (re.compile(r"""hashlib\.sha1\s*\("""), "WEAK_CRYPTO", "MEDIUM", "SHA1 is weak against collision attacks. Use SHA256 or modern hash algorithm."),
        (re.compile(r"""from\s+Crypto\.Cipher\s+import\s+DES\b"""), "WEAK_CRYPTO", "HIGH", "DES uses a small 56-bit key space vulnerable to brute force."),
    ]

    # Run Line-by-Line Scans
    for idx, line in enumerate(lines, 1):
        # 1. Hardcoded Secrets (Crucial: Mask secrets, NEVER return raw value)
        for pattern, vuln_type, severity in secret_patterns:
            matches = pattern.finditer(line)
            for m in matches:
                raw_secret = m.group(1) if m.groups() else m.group(0)
                masked_val = mask_secret(raw_secret)
                findings.append({
                    "line": idx,
                    "type": vuln_type,
                    "severity": severity,
                    "description": f"Potential hardcoded secret or token detected: '{masked_val}'.",
                    "remediation": "Store all secrets in environment variables or a secure secret manager (e.g., Vault, AWS Secrets Manager).",
                })

        # 2. SQL Injection
        for pattern, vuln_type, severity, desc in sql_patterns:
            if pattern.search(line):
                findings.append({
                    "line": idx,
                    "type": vuln_type,
                    "severity": severity,
                    "description": desc,
                    "remediation": "Use parameterized queries or an ORM (e.g. SQLAlchemy, Prisma, Drizzle) with prepared statements.",
                })

        # 3. Command & Code Injection
        for pattern, vuln_type, severity, desc in command_patterns:
            if pattern.search(line):
                findings.append({
                    "line": idx,
                    "type": vuln_type,
                    "severity": severity,
                    "description": desc,
                    "remediation": "Pass commands as an argument list (e.g. ['git', 'status']) and avoid shell=True.",
                })

        # 4. Insecure Imports
        for pattern, vuln_type, severity, desc in insecure_import_patterns:
            if pattern.search(line):
                findings.append({
                    "line": idx,
                    "type": vuln_type,
                    "severity": severity,
                    "description": desc,
                    "remediation": "Replace with safe protocols or safe serialization formats (JSON, Protobuf).",
                })

        # 5. Weak Crypto
        for pattern, vuln_type, severity, desc in crypto_patterns:
            if pattern.search(line):
                findings.append({
                    "line": idx,
                    "type": vuln_type,
                    "severity": severity,
                    "description": desc,
                    "remediation": "Upgrade to SHA-256/SHA-512 or Argon2/bcrypt for credential hashing.",
                })

    by_severity = {
        "CRITICAL": sum(1 for f in findings if f["severity"] == "CRITICAL"),
        "HIGH": sum(1 for f in findings if f["severity"] == "HIGH"),
        "MEDIUM": sum(1 for f in findings if f["severity"] == "MEDIUM"),
        "LOW": sum(1 for f in findings if f["severity"] == "LOW"),
    }

    safe = len(findings) == 0

    result = {
        "scanned_lines": len(lines),
        "safe": safe,
        "findings_count": len(findings),
        "findings": findings,
        "by_severity": by_severity,
    }
    return _format_response(tool_name, start_time, result=result)


def code_suggest_tests(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Finds untested functions and generates pytest templates.
    Input: code (str), language (str)
    Returns: {untested_functions, test_templates}
    Templates marked: # [REVIEW REQUIRED]
    """
    start_time = time.time()
    tool_name = "code_suggest_tests"

    if not code or not code.strip():
        return _format_response(tool_name, start_time, error="Code parameter cannot be empty.")

    lang = language.lower().strip()
    untested_functions: List[str] = []
    test_templates: List[Dict[str, Any]] = []

    if lang in ("python", "py"):
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            return _format_response(
                tool_name,
                start_time,
                error=f"Python SyntaxError at line {se.lineno}: {se.msg}",
            )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Ignore private dunder methods like __init__
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                fn_name = node.name
                untested_functions.append(fn_name)
                args = [a.arg for a in node.args.args if a.arg != "self" and a.arg != "cls"]

                is_async = isinstance(node, ast.AsyncFunctionDef)
                async_keyword = "async " if is_async else ""
                await_keyword = "await " if is_async else ""
                pytest_mark = "@pytest.mark.asyncio\n" if is_async else ""

                sample_args_happy = ", ".join([f"{a}=None" if "id" in a or "key" in a else f"{a}='sample'" for a in args])
                sample_args_call = ", ".join([f"sample_{a}" for a in args]) if args else ""

                template_code = f"""# [REVIEW REQUIRED] Automatically generated test template for {fn_name}
import pytest

{pytest_mark}{async_keyword}def test_{fn_name}_happy_path():
    \"\"\"Verify {fn_name} executes successfully with expected inputs.\"\"\"
    # Arrange
    # [REVIEW REQUIRED]: Provide actual fixture or mock inputs
    {chr(10).join([f"    sample_{a} = 'test_value'" for a in args]) if args else "    # No parameters required"}

    # Act
    result = {await_keyword}{fn_name}({sample_args_call})

    # Assert
    # [REVIEW REQUIRED]: Verify assertions match expected output schema
    assert result is not None


{pytest_mark}{async_keyword}def test_{fn_name}_invalid_input_edge_case():
    \"\"\"Verify {fn_name} properly handles invalid or empty inputs.\"\"\"
    # Act & Assert
    with pytest.raises((ValueError, TypeError, Exception)):
        # [REVIEW REQUIRED]: Pass known invalid edge-case parameter
        {await_keyword}{fn_name}({", ".join(["None" for _ in args])})
"""
                test_templates.append({
                    "function_name": fn_name,
                    "is_async": is_async,
                    "parameters": args,
                    "review_required": True,
                    "template": template_code.strip(),
                })

        result = {
            "language": "python",
            "untested_functions_count": len(untested_functions),
            "untested_functions": untested_functions,
            "test_templates": test_templates,
            "notice": "All generated templates are marked # [REVIEW REQUIRED] and require domain-specific fixtures.",
        }
        return _format_response(tool_name, start_time, result=result)

    else:
        # Fallback regex for JavaScript / TypeScript
        lines = code.splitlines()
        fn_pattern = re.compile(r"(?:function\s+|const\s+)([a-zA-Z0-9_$]+)")
        for line in lines:
            m = fn_pattern.search(line)
            if m and m.group(1) not in ("require", "import"):
                fn_name = m.group(1)
                untested_functions.append(fn_name)
                template_code = f"""// [REVIEW REQUIRED] Automated Vitest/Jest template for {fn_name}
import {{ describe, it, expect }} from 'vitest';

describe('{fn_name}', () => {{
  it('should execute successfully with valid parameters', async () => {{
    // [REVIEW REQUIRED]: Setup test inputs
    const result = await {fn_name}();
    expect(result).toBeDefined();
  }});

  it('should handle edge cases and throw on invalid input', async () => {{
    // [REVIEW REQUIRED]: Test failure case
    expect(() => {fn_name}(null as any)).toThrow();
  }});
}});"""
                test_templates.append({
                    "function_name": fn_name,
                    "review_required": True,
                    "template": template_code,
                })

        result = {
            "language": lang,
            "untested_functions_count": len(untested_functions),
            "untested_functions": untested_functions,
            "test_templates": test_templates,
        }
        return _format_response(tool_name, start_time, result=result)
