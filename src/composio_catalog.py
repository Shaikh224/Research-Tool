"""Cross-reference each app against Composio's own toolkit catalog.

Why: if Composio already ships a toolkit for an app, that is strong evidence
the app is buildable and tells us the auth it uses. It is also the most
role-relevant column — 'what do we already cover vs. the gap'.

Default: use the reviewer-seeded data/composio_known.json (0 credits).
Optional (COMPOSIO_SEARCH=true): confirm/fill exact toolkit URLs via Firecrawl.
"""
from __future__ import annotations

import json
import os

import config
import firecrawl_client as fc

_KNOWN = {}
_path = config.DATA / "composio_known.json"
if _path.exists():
    _KNOWN = (json.loads(_path.read_text(encoding="utf-8")) or {}).get("supported", {})

_SEARCH = os.getenv("COMPOSIO_SEARCH", "false").strip().lower() in {"1", "true", "yes", "on"}


def lookup(app_name: str) -> tuple[bool | None, str]:
    """Return (supported, url). supported is True / None(unknown)."""
    if app_name in _KNOWN:
        url = ""
        if _SEARCH:
            url = _search_url(app_name)
        return True, url

    if _SEARCH:
        url = _search_url(app_name)
        if url:
            return True, url
    return None, ""


def _search_url(app_name: str) -> str:
    results = fc.search(f"{app_name} composio toolkit integration", limit=3)
    for r in results:
        u = (r.get("url") or "").lower()
        if "composio.dev" in u or "composio.ai" in u:
            return r["url"]
    return ""
