"""Data schema, the Firecrawl extraction contract, and the deterministic
buildability rules.

Design note: the *facts* (auth, access model, API type, MCP) are extracted
from pages by an LLM. The *verdict* and *main blocker* are NOT asked of the
LLM — they are derived by a transparent rule from those facts. That makes the
most subjective field reproducible and defensible in an interview.
"""
from __future__ import annotations

# Controlled vocabularies ---------------------------------------------------

AUTH_METHODS = ["oauth2", "api_key", "basic", "token", "none", "other"]
ACCESS_MODELS = [
    "self-serve-free",   # credentials free, no approval
    "self-serve-trial",  # free trial / sandbox, then paid
    "paid-plan",         # must be on a paid plan to get API access
    "admin-approval",    # workspace/org admin must enable
    "partner-gated",     # partnership / contact-sales / app-review required
    "unknown",
]
API_TYPES = ["REST", "GraphQL", "SDK", "webhook", "none"]
API_BREADTH = ["narrow", "medium", "broad", "unknown"]
VERDICTS = ["buildable-now", "buildable-with-friction", "blocked", "not-an-api"]

# What we ask Firecrawl's JSON mode to pull off each page -------------------

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "one_liner": {"type": "string", "description": "One sentence: what the product does."},
        "auth_methods": {
            "type": "array",
            "items": {"type": "string", "enum": AUTH_METHODS},
            "description": "Auth the public API supports. [] or ['none'] if no public API.",
        },
        "access_model": {
            "type": "string",
            "enum": ACCESS_MODELS,
            "description": (
                "How a developer gets credentials. self-serve-free = sign up and "
                "get a key free; self-serve-trial = free trial/sandbox then paid; "
                "paid-plan = need a paid plan; admin-approval = org admin must "
                "enable; partner-gated = partnership/contact-sales/app-review. "
                "unknown if the page does not say."
            ),
        },
        "api_type": {"type": "array", "items": {"type": "string", "enum": API_TYPES}},
        "api_breadth": {"type": "string", "enum": API_BREADTH,
                        "description": "narrow (<~15 endpoints), medium, or broad (full CRUD across many objects)."},
        "has_mcp": {"type": "boolean", "description": "Does an official MCP server exist?"},
        "mcp_url": {"type": "string", "description": "URL of the MCP server/docs if any, else ''."},
        "evidence_notes": {"type": "string", "description": "Short quote/paraphrase justifying the auth & access answers."},
        "confidence": {"type": "number", "description": "0..1 confidence this page fully answers the questions."},
    },
    "required": ["auth_methods", "access_model", "api_type", "confidence"],
}

EXTRACTION_PROMPT = (
    "You are researching whether this app can become an agent toolkit. "
    "Answer ONLY from the content of this page. If the page does not state "
    "something, use 'unknown' / false / '' rather than guessing. Focus on the "
    "PUBLIC developer API: what authentication it uses and how a developer "
    "obtains credentials (free self-serve, trial, paid plan, admin approval, "
    "or partner/contact-sales gate)."
)

# Deterministic verdict rule ------------------------------------------------

def derive_verdict(record: dict) -> tuple[str, str]:
    """Return (verdict, main_blocker) from extracted facts. Pure function.

    Ladder (most to least severe):
      partner-gated -> blocked  (partnership / contact-sales / app review = a wall)
      admin-approval -> friction (surmountable: you own the org or ask an admin)
      paid-plan      -> friction (money, but self-serve)
      unknown        -> friction (unclear from docs; needs manual confirmation)
      self-serve-*   -> buildable-now
    """
    auth = set(record.get("auth_methods") or [])
    api_type = set(record.get("api_type") or [])
    access = record.get("access_model") or "unknown"

    auth_real = auth - {"none"}
    api_real = api_type - {"none"}

    # No signal at all from extraction. Only call it 'not-an-api' when there is
    # a POSITIVE reason to (an OSS/CLI project, or the page explicitly said
    # 'none'). A thin extraction on a real product is an extraction miss, not
    # evidence of no API — flag it for manual confirmation instead.
    if not auth_real and not api_real:
        # Only an OSS/CLI project is confidently not-an-api. An LLM 'none' on a
        # docs page is usually an extraction miss, NOT proof of no API.
        if record.get("looks_like_oss"):
            return "not-an-api", "No hosted/agent-callable API (CLI, OSS tool, or UI-only)."
        # If a second source (pricing/signup) gave a concrete access model, the
        # app clearly HAS an API — judge it by that access model below.
        if access == "unknown":
            return "buildable-with-friction", "API docs unclear or not found — needs manual confirmation."

    if access == "partner-gated":
        return "blocked", "Credentials gated behind partnership / contact-sales / app review."
    if access == "admin-approval":
        return "buildable-with-friction", "Requires org admin / developer-token approval to call in production."
    if access == "paid-plan":
        return "buildable-with-friction", "API access requires a paid plan."
    if access == "unknown":
        return "buildable-with-friction", "Access model unclear from docs — needs manual confirmation."

    # self-serve-free / self-serve-trial with a real API
    if "oauth2" in auth and access == "self-serve-free":
        return "buildable-now", "None — OAuth app registration is self-serve."
    return "buildable-now", "None — self-serve credentials + public API."


def blank_record(app: dict) -> dict:
    """A fully-populated record with safe defaults, before research."""
    return {
        "id": app["id"],
        "name": app["name"],
        "category": app["category"],
        "hint": app.get("hint", ""),
        "one_liner": "",
        "auth_methods": [],
        "access_model": "unknown",
        "api_type": [],
        "api_breadth": "unknown",
        "has_mcp": False,
        "mcp_url": "",
        "composio_toolkit": None,   # True/False/None(unknown)
        "composio_url": "",
        "verdict": "buildable-with-friction",
        "main_blocker": "",
        "evidence_urls": [],
        "evidence_notes": "",
        "confidence": 0.0,
        "flags": [],                # verification flags, e.g. "critic-disagree"
        "looks_like_oss": (app.get("hint", "") or "").strip().lower().startswith("github.com/"),
        "first_pass_access_model": None,  # for the before/after accuracy story
    }
