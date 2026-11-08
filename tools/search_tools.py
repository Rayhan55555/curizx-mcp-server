"""
Web & Documentation Search Tools for Curizx MCP Server.
Covers:
8. web_search (Rate limit: 10/min)
9. docs_search (Python, FastAPI, Next.js, React, PostgreSQL, Docker, GitHub)
"""

import time
import urllib.request
import urllib.parse
from typing import Any, Dict, List, Optional
from re import findall

from core.logger import logger
from core.auth import search_rate_limiter

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None  # type: ignore

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

OFFICIAL_DOCS_DOMAINS: Dict[str, Dict[str, str]] = {
    "python": {
        "domain": "docs.python.org/3",
        "name": "Python 3 Documentation",
        "base_url": "https://docs.python.org/3/",
    },
    "fastapi": {
        "domain": "fastapi.tiangolo.com",
        "name": "FastAPI Documentation",
        "base_url": "https://fastapi.tiangolo.com/",
    },
    "next.js": {
        "domain": "nextjs.org/docs",
        "name": "Next.js Documentation",
        "base_url": "https://nextjs.org/docs",
    },
    "nextjs": {
        "domain": "nextjs.org/docs",
        "name": "Next.js Documentation",
        "base_url": "https://nextjs.org/docs",
    },
    "react": {
        "domain": "react.dev",
        "name": "React Official Documentation",
        "base_url": "https://react.dev/",
    },
    "postgresql": {
        "domain": "postgresql.org/docs",
        "name": "PostgreSQL Documentation",
        "base_url": "https://www.postgresql.org/docs/",
    },
    "postgres": {
        "domain": "postgresql.org/docs",
        "name": "PostgreSQL Documentation",
        "base_url": "https://www.postgresql.org/docs/",
    },
    "docker": {
        "domain": "docs.docker.com",
        "name": "Docker Documentation",
        "base_url": "https://docs.docker.com/",
    },
    "github": {
        "domain": "docs.github.com",
        "name": "GitHub Documentation",
        "base_url": "https://docs.github.com/",
    },
}


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


def _raw_ddg_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Performs search via duckduckgo_search, httpx, or standard urllib."""
    results: List[Dict[str, str]] = []
    
    # 1. Try duckduckgo_search package
    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=max_results)
                for item in ddg_gen:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("href", item.get("link", "")),
                        "snippet": item.get("body", item.get("snippet", "")),
                    })
                if results:
                    return results
        except Exception as e:
            logger.warning(f"DDGS class failed, trying fallback: {e}")

    # 2. Try httpx if available
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CurizxMCPServer/0.1.0",
    }

    if httpx is not None:
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(url, data={"q": query}, headers=headers)
                if resp.status_code == 200:
                    matches = findall(
                        r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>',
                        resp.text,
                    )
                    for link, snip in matches[:max_results]:
                        clean_snip = snip.replace("<b>", "").replace("</b>", "").strip()
                        results.append({
                            "title": query,
                            "url": link.strip(),
                            "snippet": clean_snip,
                        })
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"httpx DDG search failed: {e}")

    # 3. Standard library urllib fallback
    try:
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            matches = findall(
                r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>',
                html,
            )
            for link, snip in matches[:max_results]:
                clean_snip = snip.replace("<b>", "").replace("</b>", "").strip()
                results.append({
                    "title": query,
                    "url": link.strip(),
                    "snippet": clean_snip,
                })
    except Exception as e:
        logger.error(f"urllib search fallback failed: {e}")

    return results


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    DuckDuckGo web search with per-session rate limiting (10 req/min).
    Input: query (str), max_results (int=5)
    Returns: {results: [{title, url, snippet}], query, total_found}
    """
    start_time = time.time()
    tool_name = "web_search"

    if not query or not query.strip():
        return _format_response(tool_name, start_time, error="Query parameter cannot be empty.")

    clean_query = query.strip()
    clamped_max = max(1, min(max_results, 20))

    # Enforce Rate Limiting (10/min per session)
    allowed, remaining, reset_in = search_rate_limiter.is_allowed(client_or_session="web_search")
    if not allowed:
        return _format_response(
            tool_name,
            start_time,
            error=f"Rate limit exceeded (10 requests/minute). Please retry in {reset_in} seconds.",
        )

    try:
        results = _raw_ddg_search(clean_query, max_results=clamped_max)
        result = {
            "query": clean_query,
            "total_found": len(results),
            "results": results,
            "rate_limit": {
                "remaining_requests": remaining,
                "window": "60s",
            },
        }
        return _format_response(tool_name, start_time, result=result)

    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Search failed: {str(e)}")


def docs_search(query: str, technology: str) -> Dict[str, Any]:
    """
    Searches official documentation: Python, FastAPI, Next.js, React, PostgreSQL, Docker, GitHub.
    Input: query (str), technology (str)
    Returns: {results, source, technology, official_url}
    """
    start_time = time.time()
    tool_name = "docs_search"

    if not query or not query.strip():
        return _format_response(tool_name, start_time, error="Query parameter cannot be empty.")

    if not technology or not technology.strip():
        return _format_response(tool_name, start_time, error="Technology parameter cannot be empty.")

    clean_tech = technology.lower().strip()
    target_info = OFFICIAL_DOCS_DOMAINS.get(clean_tech)

    supported_list = ["Python", "FastAPI", "Next.js", "React", "PostgreSQL", "Docker", "GitHub"]

    if not target_info:
        return _format_response(
            tool_name,
            start_time,
            error=f"Technology '{technology}' is not supported. Supported: {', '.join(supported_list)}",
        )

    clean_query = query.strip()
    scoped_query = f"site:{target_info['domain']} {clean_query}"

    # Rate limiting applies to search category
    allowed, remaining, reset_in = search_rate_limiter.is_allowed(client_or_session="docs_search")
    if not allowed:
        return _format_response(
            tool_name,
            start_time,
            error=f"Rate limit exceeded. Please retry in {reset_in} seconds.",
        )

    try:
        search_results = _raw_ddg_search(scoped_query, max_results=5)

        official_results = [
            r for r in search_results if target_info["domain"] in r.get("url", "")
        ]
        final_results = official_results if official_results else search_results

        result = {
            "technology": target_info["name"],
            "query": clean_query,
            "source": target_info["base_url"],
            "total_found": len(final_results),
            "results": final_results,
            "rate_limit_remaining": remaining,
        }
        return _format_response(tool_name, start_time, result=result)

    except Exception as e:
        logger.error(f"Error in {tool_name}: {str(e)}")
        return _format_response(tool_name, start_time, error=f"Docs search failed: {str(e)}")
