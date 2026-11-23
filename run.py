#!/usr/bin/env python3
"""Entry point for the Composio 100-app research pipeline.

Usage:
  python run.py            # full pipeline: research -> patterns -> verify -> site
  python run.py agent      # run only the research agent (writes data/results.json)
  python run.py patterns   # recompute patterns from results.json
  python run.py verify     # recompute accuracy vs the gold sample
  python run.py site       # rebuild site/index.html from existing data (no API key needed)

Tip: set MAX_APPS=10 in .env for a cheap first test run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def main():
    stage = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()

    if stage in ("all", "agent"):
        import agent
        print("== Research agent ==")
        agent.run()
    if stage in ("all", "patterns"):
        import patterns
        print("== Patterns ==")
        patterns.run()
    if stage in ("all", "verify"):
        import verify
        print("== Verification ==")
        verify.run()
    if stage in ("all", "site"):
        import build_site
        print("== Building case study ==")
        build_site.run()

    if stage == "all":
        print("\nDone. Open site/index.html, or deploy the repo to GitHub Pages / Vercel.")


if __name__ == "__main__":
    main()
