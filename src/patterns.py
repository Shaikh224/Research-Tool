"""Turn 100 rows into the patterns/insight layer — the headline of the page."""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import config

CATEGORIES = [
    "CRM and Sales", "Support and Helpdesk", "Communications and Messaging",
    "Marketing, Ads, Email and Social", "Ecommerce", "Data, SEO and Scraping",
    "Developer, Infra and Data platforms", "Productivity and Project Management",
    "Finance and Fintech", "AI, Research and Media-native",
]


def run() -> dict:
    records = json.loads((config.DATA / "results.json").read_text(encoding="utf-8"))
    n = len(records)

    auth = Counter()
    for r in records:
        for a in (r["auth_methods"] or ["none"]):
            auth[a] += 1

    access = Counter(r["access_model"] for r in records)
    verdict = Counter(r["verdict"] for r in records)
    blockers = Counter(r["main_blocker"] for r in records if r["verdict"] in ("blocked", "buildable-with-friction"))

    mcp_count = sum(1 for r in records if r["has_mcp"])
    composio_count = sum(1 for r in records if r["composio_toolkit"] is True)

    # Verdict breakdown per category (for the stacked bars).
    by_cat = defaultdict(lambda: Counter())
    for r in records:
        by_cat[r["category"]][r["verdict"]] += 1

    cat_rows = []
    for c in CATEGORIES:
        counts = by_cat.get(c, Counter())
        total = sum(counts.values()) or 1
        buildable = counts.get("buildable-now", 0)
        cat_rows.append({
            "category": c,
            "total": sum(counts.values()),
            "buildable_now": buildable,
            "with_friction": counts.get("buildable-with-friction", 0),
            "blocked": counts.get("blocked", 0),
            "not_api": counts.get("not-an-api", 0),
            "buildable_pct": round(100 * buildable / total),
        })

    easy = verdict.get("buildable-now", 0)
    walls = verdict.get("blocked", 0)
    gated = verdict.get("blocked", 0) + verdict.get("buildable-with-friction", 0)

    # Data completeness: how many apps returned a conclusive auth + access.
    conclusive = sum(1 for r in records
                     if (set(r["auth_methods"]) - {"none"}) and r["access_model"] != "unknown")
    unknown_access = access.get("unknown", 0)

    # Dominant auth EXCLUDING the 'none'/extraction-gap noise.
    real_auth = Counter({k: v for k, v in auth.items() if k != "none"})
    top_auth = real_auth.most_common(1)[0] if real_auth else ("oauth2", 0)

    ranked = sorted(cat_rows, key=lambda x: x["buildable_pct"], reverse=True)

    insights = [
        f"Of {n} apps, {easy} are buildable as an agent toolkit today and {gated} are buildable "
        f"only with friction or blocked — the long tail of OAuth app-review and contact-sales gates "
        f"is where the real work is.",
        f"Among apps with a conclusive answer, {top_auth[0].upper()} is the most common auth "
        f"({top_auth[1]} apps) — the toolkit layer must treat OAuth2 and API-key as first-class.",
        f"Easiest categories: {ranked[0]['category']} and {ranked[1]['category']} "
        f"({ranked[0]['buildable_pct']}% / {ranked[1]['buildable_pct']}% buildable now).",
        f"Composio already covers {composio_count}/{n} of these apps; {mcp_count}/{n} ship an "
        f"official MCP server — the agent-native surface is still early.",
        f"Data completeness: {conclusive}/{n} apps returned a conclusive auth + access on this run; "
        f"{unknown_access} still read 'unknown' (thin docs / credit-limited scrape) and are flagged "
        f"for a cleaner re-run — stated plainly rather than guessed.",
    ]

    out = {
        "n": n,
        "auth": dict(auth.most_common()),
        "access": dict(access.most_common()),
        "verdict": dict(verdict.most_common()),
        "blockers": dict(blockers.most_common(6)),
        "mcp_count": mcp_count,
        "composio_count": composio_count,
        "by_category": cat_rows,
        "insights": insights,
    }
    path = config.DATA / "patterns.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Patterns written -> {path}")
    return out
