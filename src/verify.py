"""Human-loop accuracy: compare agent output to the gold sample and report
per-field accuracy plus the first-pass -> refined improvement, honestly
(including every miss).

'before' = the agent's FIRST-PASS answer (docs page only).
'after'  = after Loop B re-checked the access model on the pricing page.
auth_methods / has_mcp are not touched by the loop, so they are the same in
both; access_model and verdict are where the loop can move the number.
"""
from __future__ import annotations

import json

import config
import schema


def _auth_ok(pred, gold) -> bool:
    ps, gs = set(pred or []), set(gold or [])
    if not gs:
        return not ps
    return len(ps & gs) > 0  # at least one correct auth method


def _verdict_from_access(rec: dict, access_model: str) -> str:
    tmp = dict(rec)
    tmp["access_model"] = access_model or "unknown"
    return schema.derive_verdict(tmp)[0]


def run() -> dict:
    results = {r["id"]: r for r in json.loads((config.DATA / "results.json").read_text(encoding="utf-8"))}
    gold = json.loads((config.DATA / "gold_labels.json").read_text(encoding="utf-8"))["labels"]

    rows, misses = [], []
    tallies = {
        "auth": [0, 0], "mcp": [0, 0],
        "access_before": [0, 0], "access_after": [0, 0],
        "verdict_before": [0, 0], "verdict_after": [0, 0],
    }

    def bump(key, ok):
        tallies[key][0] += int(bool(ok))
        tallies[key][1] += 1

    for g in gold:
        rec = results.get(g["id"])
        if not rec:
            continue

        first_access = rec.get("first_pass_access_model") or rec.get("access_model")
        verdict_before = _verdict_from_access(rec, first_access)

        checks = {
            "auth": _auth_ok(rec["auth_methods"], g["auth_methods"]),
            "mcp": bool(rec["has_mcp"]) == bool(g["has_mcp"]),
            "access_before": first_access == g["access_model"],
            "access_after": rec["access_model"] == g["access_model"],
            "verdict_before": verdict_before == g["verdict"],
            "verdict_after": rec["verdict"] == g["verdict"],
        }
        for k, v in checks.items():
            bump(k, v)

        changed = any(f.startswith("access-refined") for f in rec.get("flags", []))
        row = {
            "id": g["id"], "name": g["name"],
            "gold": {"auth": g["auth_methods"], "access": g["access_model"],
                     "verdict": g["verdict"], "mcp": g["has_mcp"]},
            "agent": {"auth": rec["auth_methods"], "access": rec["access_model"],
                      "verdict": rec["verdict"], "mcp": rec["has_mcp"],
                      "access_first_pass": first_access},
            "correct": checks,
            "changed_by_loop": changed,
            "evidence": rec.get("evidence_urls", [])[:2],
        }
        rows.append(row)
        if not (checks["auth"] and checks["access_after"] and checks["verdict_after"] and checks["mcp"]):
            misses.append(row)

    def pct(key):
        hit, tot = tallies[key]
        return round(100 * hit / tot, 1) if tot else 0.0

    # Overall = mean of the four fields (access/verdict use before vs after).
    overall_before = round((pct("auth") + pct("mcp") + pct("access_before") + pct("verdict_before")) / 4, 1)
    overall_after = round((pct("auth") + pct("mcp") + pct("access_after") + pct("verdict_after")) / 4, 1)

    report = {
        "sample_size": len(rows),
        "fields": {
            "auth_methods": pct("auth"),
            "has_mcp": pct("mcp"),
            "access_model": {"before": pct("access_before"), "after": pct("access_after")},
            "verdict": {"before": pct("verdict_before"), "after": pct("verdict_after")},
        },
        "overall": {"before": overall_before, "after": overall_after},
        "rows_changed_by_loop": sum(1 for r in rows if r["changed_by_loop"]),
        "rows": rows,
        "misses": misses,
    }
    out = config.DATA / "verification.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Accuracy: {overall_before}% (first pass) -> {overall_after}% (after loops) "
          f"on n={len(rows)}; {len(misses)} rows still imperfect. -> {out}")
    return report
