"""Central configuration. Reads from environment / .env."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_CACHE = DATA / "raw_cache"
SITE = ROOT / "site"

try:  # optional: site rebuilds should work without any deps installed
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# OFFLINE=true -> never hit the network; use only the on-disk cache. Lets the
# pipeline regenerate results from cached scrapes for free (e.g. after credits
# run out, or to re-apply code fixes without new API calls).
OFFLINE = _bool("OFFLINE", False)

# Live MCP search costs ~1 call per non-seeded app. The seed map + page signal
# already cover MCP well, so keep this off for cheap runs; set true to confirm
# MCP for the apps not in data/mcp_known.json.
MCP_LIVE_SEARCH = _bool("MCP_LIVE_SEARCH", False)

SEARCH_LIMIT = _int("SEARCH_LIMIT", 5)
RUN_GATE_CHECK = _bool("RUN_GATE_CHECK", True)
MAX_APPS = _int("MAX_APPS", 100)
WORKERS = _int("WORKERS", 6)

# Firecrawl v1 REST endpoints (stable contract, SDK-version independent).
FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"

for _d in (DATA, RAW_CACHE, SITE):
    _d.mkdir(parents=True, exist_ok=True)
