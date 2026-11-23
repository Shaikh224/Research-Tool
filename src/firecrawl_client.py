"""Thin, SDK-version-independent Firecrawl client over the v1 REST API.

Every raw response is cached to disk keyed by a hash of the request, so
re-runs, the critic pass, and site rebuilds cost ZERO Firecrawl credits.
This is the single most important cost-control decision in the project.
"""
from __future__ import annotations

import hashlib
import json
import time

import requests

import config

_TIMEOUT = 90


def _cache_path(kind: str, payload: dict):
    key = hashlib.sha1(
        (kind + json.dumps(payload, sort_keys=True)).encode()
    ).hexdigest()[:20]
    return config.RAW_CACHE / f"{kind}_{key}.json"


def _load_cache(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save_cache(path, data):
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _post(endpoint: str, payload: dict, kind: str, use_cache: bool = True):
    path = _cache_path(kind, payload)
    if use_cache:
        cached = _load_cache(path)
        if cached is not None:
            return cached

    # Offline: never touch the network. Cache miss -> empty, no retries, no hang.
    if config.OFFLINE:
        return {"success": False, "offline": True, "data": []}

    if not config.FIRECRAWL_API_KEY:
        raise RuntimeError(
            "FIRECRAWL_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    url = f"{config.FIRECRAWL_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json",
    }

    last_err = None
    for attempt in range(4):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=_TIMEOUT)
            if resp.status_code == 429:  # rate limited
                time.sleep(2 ** attempt + 1)
                continue
            resp.raise_for_status()
            data = resp.json()
            _save_cache(path, data)
            return data
        except requests.RequestException as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    # Give back a shaped error instead of crashing the whole run.
    return {"success": False, "error": str(last_err)}


def search(query: str, limit: int | None = None) -> list[dict]:
    """Return a list of {url, title, description} search results."""
    limit = limit or config.SEARCH_LIMIT
    data = _post("search", {"query": query, "limit": limit}, "search")
    results = (data or {}).get("data") or []
    out = []
    for r in results:
        out.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "description": r.get("description", ""),
        })
    return out


def scrape(url: str, extract: bool = False, fresh: bool = False) -> dict:
    """Scrape a URL. If extract=True, also run Firecrawl JSON extraction with
    our schema/prompt (server-side LLM) and return it under 'json'.

    Returns {markdown, json, metadata, url}.
    """
    import schema  # local import to avoid a cycle

    payload: dict = {"url": url, "onlyMainContent": True}
    formats = ["markdown"]
    if extract:
        formats.append("json")
        payload["jsonOptions"] = {
            "prompt": schema.EXTRACTION_PROMPT,
            "schema": schema.EXTRACTION_SCHEMA,
        }
    payload["formats"] = formats
    if fresh:
        payload["maxAge"] = 0  # force a live re-fetch (used by verification loops)

    data = _post("scrape", payload, "scrape", use_cache=not fresh)
    doc = (data or {}).get("data") or {}
    return {
        "url": url,
        "markdown": doc.get("markdown", ""),
        "json": doc.get("json") or doc.get("extract") or {},
        "metadata": doc.get("metadata", {}),
        "ok": bool((data or {}).get("success", True)) and bool(doc),
    }
