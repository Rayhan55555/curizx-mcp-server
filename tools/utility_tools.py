"""
Utility & Developer Intelligence Tools for Curizx MCP Server.
Covers:
10. summarize_text
11. generate_docs
12. explain_code
"""

import ast
import re
import time
from typing import Any, Dict, List, Optional
from core.logger import logger


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


# Common conversational fluff phrases to clean up
FLUFF_PATTERNS = [
    re.compile(r"\b(it goes without saying that|needless to say|as a matter of fact|at the end of the day)\b,?", re.IGNORECASE),
    re.compile(r"\b(basically|essentially|literally|virtually|obviously|actually)\b\s*", re.IGNORECASE),
    re.compile(r"\b(in order to)\b", re.IGNORECASE),
    re.compile(r"\b(for all intents and purposes)\b,?", re.IGNORECASE),
]


def summarize_text(text: str, max_length: int = 200) -> Dict[str, Any]:
    """
    Extracts key points, removes fluff, and condenses text.
    Input: text (str), max_length (int=200)
    Returns: {summary, key_points, word_count, original_word_count, compression_ratio}
    """
    start_time = time.time()
    tool_name = "summarize_text"

    if not text or not text.strip():
        return _format_response(tool_name, start_time, error="Text parameter cannot be empty.")

    original_words = text.strip().split()
    original_word_count = len(original_words)

    # Clean fluff
    cleaned_text = text
    for pattern in FLUFF_PATTERNS:
        cleaned_text = pattern.sub("", cleaned_text)
    # Normalize spaces
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    # Split into sentences
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned_text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

    if not sentences:
        sentences = [cleaned_text]

    # Calculate word frequency weights for extractive summary
    words = [w.lower() for w in re.findall(r"\b\w{4,}\b", cleaned_text)]
    stopwords = {"that", "with", "from", "this", "these", "those", "have", "been", "were", "what", "which", "will", "would", "there", "their", "about", "more", "when"}
    freq: Dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1

    # Score sentences
    scored_sentences = []
    for idx, s in enumerate(sentences):
        s_words = [w.lower() for w in re.findall(r"\b\w{4,}\b", s)]
        score = sum(freq.get(w, 0) for w in s_words)
        # Position bonus for lead sentences
        if idx == 0:
            score += 5
        elif idx == 1:
            score += 2
        scored_sentences.append((score, idx, s))

    # Sort by score descending to pick top sentences
    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    selected_sentences = []
    current_word_count = 0
    max_len = max(30, max_length)

    # Pick sentences preserving chronological flow
    chosen_indices = set()
    for _, idx, s in scored_sentences:
        s_wc = len(s.split())
        if current_word_count + s_wc <= max_len or not chosen_indices:
            chosen_indices.add(idx)
            current_word_count += s_wc
            if current_word_count >= max_len:
                break

    for idx, s in enumerate(sentences):
        if idx in chosen_indices:
            selected_sentences.append(s)

    summary = " ".join(selected_sentences)
    final_words = summary.split()

    # Key points: Top 3-5 concise bullets
    key_points = []
    for s in selected_sentences[:4]:
        # Condense sentence to a key point
        clean_bullet = s.rstrip(".")
        if len(clean_bullet) > 120:
            clean_bullet = clean_bullet[:117] + "..."
        key_points.append(clean_bullet)

    compression_ratio = round((len(final_words) / max(1, original_word_count)) * 100, 1)

    result = {
        "summary": summary,
        "key_points": key_points,
        "word_count": len(final_words),
        "original_word_count": original_word_count,
        "compression_ratio": f"{compression_ratio}%",
    }
    return _format_response(tool_name, start_time, result=result)


def generate_docs(code: str, doc_type: str = "docstring") -> Dict[str, Any]:
    """
    Generates structured documentation for code.
    Input: code (str), doc_type (str: "docstring" | "api" | "readme")
    Returns: {documentation, format, sections, functions_documented}
    """
    start_time = time.time()
    tool_name = "generate_docs"

    if not code or not code.strip():
        return _format_response(tool_name, start_time, error="Code parameter cannot be empty.")

    clean_type = doc_type.lower().strip()
    if clean_type not in ("docstring", "api", "readme"):
        return _format_response(
            tool_name,
            start_time,
            error=f"Invalid doc_type '{doc_type}'. Allowed types: 'docstring', 'api', 'readme'",
        )

    # Parse code structure
    functions = []
    classes = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
                functions.append({
                    "name": node.name,
                    "args": args,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "returns": getattr(node.returns, "id", "Any") if node.returns else "Any",
                })
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
    except Exception:
        # Fallback regex for non-Python or partial snippets
        for match in re.finditer(r"(?:def|function)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", code):
            fn_name = match.group(1)
            raw_args = [a.strip() for a in match.group(2).split(",") if a.strip()]
            functions.append({
                "name": fn_name,
                "args": raw_args,
                "is_async": "async" in code,
                "returns": "Any",
            })

    sections = []
    doc_output = ""

    if clean_type == "docstring":
        sections = ["Function Purpose", "Parameters (Args)", "Returns", "Raises", "Example Usage"]
        generated_blocks = []
        for fn in functions or [{"name": "process_data", "args": ["data", "options"], "returns": "dict"}]:
            args_doc = "\n".join([f"    {arg} (Any): Description and constraints for `{arg}`." for arg in fn["args"]]) or "    None"
            block = f'''def {fn["name"]}({", ".join(fn["args"])}):
    """
    Execute {fn["name"]} logic with validated parameters.

    Args:
{args_doc}

    Returns:
        {fn.get("returns", "Any")}: Result of the operation with execution state.

    Raises:
        ValueError: If input arguments fail validation criteria.
        RuntimeError: If execution encounters unexpected operational errors.

    Example:
        >>> result = {fn["name"]}({", ".join(["..." for _ in fn["args"]])})
        >>> print(result)
    """'''
            generated_blocks.append(block)

        doc_output = "\n\n".join(generated_blocks)

    elif clean_type == "api":
        sections = ["Endpoint / Method Definition", "Request Headers & Schema", "Response Schema", "Status Codes", "Curl Example"]
        endpoints_doc = []
        for fn in functions or [{"name": "process_handler", "args": ["payload"], "returns": "JSON"}]:
            route_path = f"/api/v1/{fn['name'].replace('_', '-')}"
            block = f"""### `POST {route_path}`

**Description:** Invokes `{fn['name']}` processing routine.

#### Request Headers
| Header | Type | Required | Description |
|---|---|---|---|
| `Content-Type` | string | Yes | `application/json` |
| `Authorization` | string | Yes | Bearer token authorization |

#### Request Body
```json
{{
{chr(10).join([f'  "{arg}": "sample_value",' for arg in fn["args"]]).rstrip(',')}
}}
```

#### Responses
- **`200 OK`**: Operation completed successfully.
```json
{{
  "success": true,
  "result": {{}},
  "timestamp": "2026-01-01T00:00:00Z"
}}
```
- **`400 Bad Request`**: Malformed payload or validation error.
- **`500 Internal Error`**: Unhandled server exception.
"""
            endpoints_doc.append(block)
        doc_output = "\n\n---\n\n".join(endpoints_doc)

    elif clean_type == "readme":
        sections = ["Component Overview", "Installation", "Integration & Usage", "Error Handling"]
        fn_list = ", ".join([f"`{f['name']}()`" for f in functions]) or "`main()`"
        doc_output = f"""# Module Reference

## Overview
This module exposes core operational utilities: {fn_list}.

## Installation & Setup
```bash
pip install -r requirements.txt
```

## Usage Example
```python
# Import the components
from module import {functions[0]['name'] if functions else 'execute'}

# Call function with validated parameters
result = {functions[0]['name'] if functions else 'execute'}()
print("Execution output:", result)
```

## Security & Best Practices
- Never pass unvalidated user inputs directly into internal calls.
- Enforce structured logging with secret masking.
"""

    result = {
        "format": clean_type,
        "sections": sections,
        "functions_documented": [f["name"] for f in functions],
        "classes_detected": classes,
        "documentation": doc_output.strip(),
    }
    return _format_response(tool_name, start_time, result=result)


def explain_code(code: str, level: str = "intermediate") -> Dict[str, Any]:
    """
    Explains what code does, why it's written this way, and potential improvements.
    Input: code (str), level ("beginner" | "intermediate" | "expert")
    Returns: {explanation, key_concepts, improvements, target_audience}
    """
    start_time = time.time()
    tool_name = "explain_code"

    if not code or not code.strip():
        return _format_response(tool_name, start_time, error="Code parameter cannot be empty.")

    clean_level = level.lower().strip()
    if clean_level not in ("beginner", "intermediate", "expert"):
        return _format_response(
            tool_name,
            start_time,
            error=f"Invalid level '{level}'. Allowed levels: 'beginner', 'intermediate', 'expert'",
        )

    # Detect features in code
    has_async = "async " in code or "await " in code
    has_classes = "class " in code
    has_decorators = "@" in code
    has_exceptions = "try:" in code or "except" in code
    has_typing = "->" in code or ": int" in code or ": str" in code

    key_concepts: List[str] = []
    improvements: List[str] = []
    explanation_parts: List[str] = []

    if has_async:
        key_concepts.append("Asynchronous Non-blocking I/O (async/await)")
    if has_classes:
        key_concepts.append("Object-Oriented Architecture (Classes & Encapsulation)")
    if has_decorators:
        key_concepts.append("Higher-Order Decorators & Metadata Wrappers")
    if has_exceptions:
        key_concepts.append("Defensive Exception Handling & Error Boundaries")
    if has_typing:
        key_concepts.append("Static Type Hinting (PEP 484)")

    if not key_concepts:
        key_concepts.append("Modular Procedural Control Flow")

    if clean_level == "beginner":
        explanation_parts.append(
            "Here is how this code works in simple terms:\n"
            "1. **Input & Setup:** It prepares variables and functions to carry out a specific task step-by-step.\n"
            "2. **Processing:** The logic processes data and makes decisions using conditional checks (if/else) or loops.\n"
            "3. **Output:** It packages the computed result and returns it safely so other parts of your program can use it."
        )
        if has_async:
            explanation_parts.append("💡 *Note on Async:* 'async' and 'await' mean your program doesn't freeze while waiting for slow things like network calls or file reads.")
        improvements.extend([
            "Add friendly comments above tricky lines to explain the 'why'.",
            "Give variables clear, descriptive names (e.g., `user_account_list` instead of `data`).",
            "Include basic checks to verify the input isn't empty or invalid.",
        ])

    elif clean_level == "intermediate":
        explanation_parts.append(
            "**Architectural Summary:**\n"
            "This component implements a structured data pipeline. It encapsulates business logic into callable interfaces, "
            "handling state transitions and ensuring functional separation of concerns."
        )
        if has_async:
            explanation_parts.append(
                "**Concurrency Model:** Utilizes event-loop coroutines via async/await, allowing cooperative multitasking without OS thread overhead."
            )
        improvements.extend([
            "Enforce runtime validation using Pydantic models for domain entities.",
            "Replace generic exceptions with dedicated domain-specific error classes.",
            "Add automated unit and regression tests with pytest fixtures and mocks.",
        ])

    else:  # expert
        explanation_parts.append(
            "**Deep Technical Analysis:**\n"
            "The implementation provides execution boundaries with predictable algorithmic complexity. "
            "Data flow is strictly routed through defined entrypoints with explicit parameter binding."
        )
        if has_async:
            explanation_parts.append(
                "**Runtime Characteristics:** Coroutines suspend execution on I/O wait, yielding control back to the event loop. "
                "Ensure CPU-intensive tasks do not block the single-threaded event loop (offload to `run_in_executor`)."
            )
        improvements.extend([
            "Evaluate memory allocation profiles and consider utilizing `__slots__` for data-heavy class instances.",
            "Benchmark hot code paths using cProfile or py-spy to eliminate overhead.",
            "Verify thread-safety and reentrancy if invoked within multi-worker server environments (e.g. Uvicorn/Gunicorn).",
        ])

    result = {
        "target_audience": clean_level,
        "explanation": "\n\n".join(explanation_parts),
        "key_concepts": key_concepts,
        "improvements": improvements,
    }
    return _format_response(tool_name, start_time, result=result)
