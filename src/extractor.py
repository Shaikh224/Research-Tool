"""First-pass research for one app: search -> pick best doc page -> extract,
with a fallback scrape when the first page is thin, plus a dedicated MCP check.
"""
from __future__ import annotations

import json
import re

import config
import firecrawl_client as fc
import schema

_MCP_KNOWN = {}
_mcp_path = config.DATA / "mcp_known.json"
if _mcp_path.exists():
    _MCP_KNOWN = (json.loads(_mcp_path.read_text(encoding="utf-8")) or {}).get("has_mcp", {})


def _domain(hint: str) -> str:
    m = re.match(r"([a-z0-9.\-]+\.[a-z]{2,})", (hint or "").strip().lower())
    return m.group(1) if m else ""


def _hint_url(hint: str) -> str:
    """The app-list hints ARE doc URLs (e.g. 'developers.notion.com',
    'stripe.com/docs/api'). Build a direct URL so we can scrape the right page
    without a search call — cheaper and more accurate."""
    h = (hint or "").strip()
    m = re.match(r"([a-z0-9.\-]+\.[a-z]{2,}(?:/[^\s()]*)?)", h.lower())
    if not m:
        return ""
    return "https://" + m.group(1).rstrip("/")


def _name_tokens(name: str) -> list[str]:
    base = re.sub(r"\(.*?\)", "", name).lower()
    return [t for t in re.split(r"[^a-z0-9]+", base) if len(t) > 2]


def _rank_doc_urls(results: list[dict], domain: str) -> list[str]:
    """Score candidate URLs; return best-first. Prefer the hint domain and
    pages that look like auth/API reference."""
    scored = []
    for r in results:
        u = (r.get("url") or "").lower()
        if not u:
            continue
        s = 0
        if domain and domain in u:
            s += 4
        for kw, w in (("auth", 3), ("/api", 2), ("reference", 2), ("rest", 1),
                      ("graphql", 1), ("developer", 1), ("docs", 1), ("getting-started", 1)):
            if kw in u:
                s += w
        scored.append((s, r["url"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [u for _, u in scored]


def _pick_pricing_url(results: list[dict]) -> str | None:
    for r in results:
        u = (r.get("url") or "").lower()
        if any(k in u for k in ("pricing", "signup", "sign-up", "register", "plans", "get-started")):
            return r["url"]
    return None


def _clean_auth(val) -> list:
    """Keep allowed methods; drop the 'none' noise when real methods exist."""
    if not isinstance(val, list):
        return []
    vals = [v for v in val if v in schema.AUTH_METHODS]
    real = [v for v in vals if v != "none"]
    return real if real else vals


def _clean_list(val, allowed) -> list:
    if not isinstance(val, list):
        return []
    return [v for v in val if v in allowed]


def _apply_facts(rec: dict, facts: dict) -> None:
    rec["one_liner"] = (facts.get("one_liner") or rec["one_liner"] or "").strip()
    auth = _clean_auth(facts.get("auth_methods"))
    if auth:
        rec["auth_methods"] = auth
    api = _clean_list(facts.get("api_type"), schema.API_TYPES)
    api = [a for a in api if a != "none"] or api
    if api:
        rec["api_type"] = api
    if facts.get("access_model") in schema.ACCESS_MODELS and facts["access_model"] != "unknown":
        rec["access_model"] = facts["access_model"]
    if facts.get("api_breadth") in schema.API_BREADTH and facts["api_breadth"] != "unknown":
        rec["api_breadth"] = facts["api_breadth"]
    if facts.get("has_mcp"):
        rec["has_mcp"] = True
        rec["mcp_url"] = (facts.get("mcp_url") or rec["mcp_url"] or "").strip()
    if facts.get("evidence_notes"):
        rec["evidence_notes"] = facts["evidence_notes"].strip()
    try:
        rec["confidence"] = max(rec["confidence"], round(float(facts.get("confidence", 0.0)), 2))
    except (TypeError, ValueError):
        pass


def _thin(rec: dict) -> bool:
    return not (set(rec["auth_methods"]) - {"none"}) or rec["access_model"] == "unknown"


def detect_mcp(app: dict) -> tuple[bool, str]:
    """Dedicated MCP check — the auth/docs page rarely mentions MCP.
    Reviewer-seeded map first (zero credits), then a live search as fallback."""
    if app["name"] in _MCP_KNOWN:
        return True, _MCP_KNOWN[app["name"]]
    if not config.MCP_LIVE_SEARCH:
        return False, ""
    toks = _name_tokens(app["name"])
    res = fc.search(f'{app["name"]} MCP server model context protocol', limit=3)
    for r in res:
        blob = f"{r.get('url','')} {r.get('title','')} {r.get('description','')}".lower()
        if "mcp" in blob and any(t in blob for t in toks):
            return True, r.get("url", "")
    return False, ""


def research_app(app: dict) -> dict:
    rec = schema.blank_record(app)
    domain = _domain(app.get("hint", ""))

    # MCP seed up front (free, deterministic) so it survives any early return.
    if app["name"] in _MCP_KNOWN:
        rec["has_mcp"], rec["mcp_url"] = True, _MCP_KNOWN[app["name"]]

    # 1) Try the documentation hint directly — the hints ARE doc URLs, so this
    # is more accurate than search and uses no search credit.
    scraped_any = False
    hint_url = _hint_url(app.get("hint", ""))
    if hint_url:
        scraped = fc.scrape(hint_url, extract=True)
        facts = scraped.get("json") or {}
        if scraped.get("ok") and facts:
            scraped_any = True
            rec["evidence_urls"].insert(0, hint_url)
            _apply_facts(rec, facts)

    # 2) Only if the hint page was thin do we spend a search to find a better one.
    if _thin(rec):
        q = f'{app["name"]} developer API authentication documentation'
        if domain:
            q += f" {domain}"
        results = fc.search(q)
        for r in results[:3]:
            if r.get("url") and r["url"] not in rec["evidence_urls"]:
                rec["evidence_urls"].append(r["url"])
        candidates = _rank_doc_urls(results, domain)
        limit = len(candidates) if config.OFFLINE else 2
        for url in candidates[:limit]:
            scraped = fc.scrape(url, extract=True)
            facts = scraped.get("json") or {}
            if scraped.get("ok") and facts:
                scraped_any = True
                _apply_facts(rec, facts)
                if not _thin(rec):
                    break
    if not scraped_any:
        rec["flags"].append("extract-failed")

    # 3) Dedicated MCP detection (independent of the auth page).
    if not rec["has_mcp"]:
        mcp, mcp_url = detect_mcp(app)
        rec["has_mcp"], rec["mcp_url"] = mcp, (rec["mcp_url"] or mcp_url)

    rec["first_pass_access_model"] = rec["access_model"]
    rec["verdict"], rec["main_blocker"] = schema.derive_verdict(rec)
    return rec
