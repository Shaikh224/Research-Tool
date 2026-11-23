"""Verification loops that run *inside* the agent (automatic, all 100 apps).

Loop A  — confidence gate: flag thin/low-confidence extractions.
Loop B  — access re-check: the self-serve-vs-gated field is the most error-prone
          (docs say 'REST API', the pricing page reveals a Contact-Sales wall).
          We re-extract access_model from the PRICING/SIGNUP page and reconcile.
          Every change here is a measurable first-pass -> refined improvement.

Optional second-model critic (Gemini) is used only if GEMINI_API_KEY is set;
otherwise the Firecrawl re-extraction + diff is the critic (still fully free).
"""
from __future__ import annotations

import config
import firecrawl_client as fc
import schema
from extractor import _apply_facts, _pick_pricing_url

_LOW_CONF = 0.55
# Access models worth double-checking on the pricing page (cheap wins vs. walls).
_RECHECK = {"self-serve-free", "self-serve-trial", "unknown", "paid-plan"}


def refine(rec: dict) -> dict:
    # Loop A: confidence gate.
    if rec.get("confidence", 0) < _LOW_CONF:
        rec["flags"].append("low-confidence")

    if not config.RUN_GATE_CHECK:
        return rec

    # Loop B: re-check the access model on the pricing/signup page.
    if rec.get("access_model") not in _RECHECK:
        return rec  # partner-gated/admin-approval first passes are rarely too-optimistic

    results = fc.search(f'{rec["name"]} API pricing plans free developer sign up')
    pricing_url = _pick_pricing_url(results) or (results[0]["url"] if results else None)
    if not pricing_url:
        rec["flags"].append("no-pricing-page")
        return rec

    scraped = fc.scrape(pricing_url, extract=True)
    facts = scraped.get("json") or {}
    if pricing_url not in rec["evidence_urls"]:
        rec["evidence_urls"].append(pricing_url)
    if not facts:
        return rec

    prev_access = rec["access_model"]
    had_auth = bool(set(rec["auth_methods"]) - {"none"})

    # The pricing/signup page is a legitimate SECOND source. Merge its facts —
    # this also recovers auth/API for apps whose docs-search came back empty.
    _apply_facts(rec, facts)

    if rec["access_model"] != prev_access and rec["access_model"] != "unknown":
        rec["flags"].append(f"access-refined:{prev_access}->{rec['access_model']}")
    if not had_auth and (set(rec["auth_methods"]) - {"none"}):
        rec["flags"].append("auth-recovered-from-pricing")

    rec["verdict"], rec["main_blocker"] = schema.derive_verdict(rec)
    return rec
