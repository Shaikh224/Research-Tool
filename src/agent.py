"""Orchestrator: run the research agent across all apps with concurrency.

Pipeline per app:  search+extract (extractor)  ->  Composio cross-ref
                   ->  verification loops (critic)  ->  final record.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import composio_catalog
import config
import critic
from extractor import research_app


def _one(app: dict) -> dict:
    rec = research_app(app)
    supported, url = composio_catalog.lookup(app["name"])
    rec["composio_toolkit"] = supported
    rec["composio_url"] = url
    rec = critic.refine(rec)
    return rec


def run() -> list[dict]:
    apps = json.loads((config.DATA / "apps.json").read_text(encoding="utf-8"))
    apps = apps[: config.MAX_APPS]

    results: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=config.WORKERS) as pool:
        futures = {pool.submit(_one, a): a for a in apps}
        for fut in as_completed(futures):
            app = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:  # never let one app kill the run
                from schema import blank_record, derive_verdict
                rec = blank_record(app)
                rec["flags"].append(f"error:{type(e).__name__}")
                rec["verdict"], rec["main_blocker"] = derive_verdict(rec)
            results.append(rec)
            done += 1
            print(f"  [{done:>3}/{len(apps)}] {app['name']:<28} "
                  f"{rec['verdict']:<24} conf={rec.get('confidence', 0)}")

    results.sort(key=lambda r: r["id"])
    out = config.DATA / "results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(results)} records -> {out}")
    return results
