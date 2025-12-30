"""Controlled web research tool (read-only fetch + summarize)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from src.utils.logging import get_logger

logger = get_logger(__name__)


_DEFAULT_ALLOW_HOSTS = {
    "en.wikipedia.org",
    "developer.mozilla.org",
    "docs.python.org",
    "fastapi.tiangolo.com",
}


def _is_public_http_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.scheme in {"http", "https"} and bool(u.netloc)
    except Exception:
        return False


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


async def fetch_url(url: str, timeout_s: float = 10.0, max_bytes: int = 2_000_000) -> str:
    if not _is_public_http_url(url):
        raise ValueError("Invalid URL")
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s, headers={"User-Agent": "GodfatherAssistant/1.0"}) as client:
        r = await client.get(url)
        r.raise_for_status()
        content = r.text
        if len(content.encode("utf-8", errors="ignore")) > max_bytes:
            content = content[: max_bytes]
        return content


def strip_html(text: str) -> str:
    # Extremely simple HTML stripping for v1 (good enough for short summaries).
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<.*?>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def web_research(url: str, allow_hosts_csv: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch a URL (allowlisted by host) and return clean text suitable for summarization.
    """
    host = _host(url)
    allow = set(_DEFAULT_ALLOW_HOSTS)
    if allow_hosts_csv:
        allow |= {h.strip().lower() for h in allow_hosts_csv.split(",") if h.strip()}
    if host not in allow:
        raise ValueError(f"Host not allowlisted: {host}")

    html = await fetch_url(url)
    text = strip_html(html)
    logger.info("web_research_fetched", url=url, host=host, chars=len(text))
    return {"url": url, "host": host, "text": text[:20000]}


