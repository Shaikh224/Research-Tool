# Composio — 100-App Agent Research Pipeline

Research 100 apps for one question: **can an AI agent call this app as a toolkit today?**
For each app the agent captures category, auth method(s), self-serve-vs-gated access, API
surface, whether an MCP server exists, and a **buildability verdict** — with an evidence URL
behind every answer. It then **finds the patterns**, **verifies its own accuracy** against a
hand-labeled sample, and renders a single self-explanatory **HTML case study**.

> Deliverable page: `site/index.html` (self-contained — deploy to any static host as-is).

![Case study — the generated site/index.html](docs/case-study.png)

## What it does, in one picture

```mermaid
flowchart LR
  A["100 apps<br/>seed list"] --> B["Firecrawl<br/>scrape docs hint URL"]
  B --> C["Firecrawl extract<br/>JSON schema:<br/>auth · access · API · MCP"]
  C --> D["Composio<br/>cross-reference<br/>(already a toolkit?)"]
  D --> E{"Verification<br/>loops"}
  E -->|Loop A| F["confidence gate<br/>flag thin answers"]
  E -->|Loop B| G["gate re-check<br/>pricing page → fix access"]
  F --> H["verdict<br/>(derived by rule)"]
  G --> H
  H --> I["results.json"]
  I --> J["patterns + accuracy<br/>vs gold sample"]
  J --> K["index.html<br/>case study"]
```

**The agent extracts *facts* (auth, access, API type, MCP). The *verdict* is computed by a
transparent rule** (`src/schema.py :: derive_verdict`), not guessed — so it is reproducible and
defensible in an interview.

## Results snapshot (latest run)

- **82 / 100** apps buildable as an agent toolkit today; **14** with friction, **3** blocked, **1** not-an-API.
- Dominant auth **OAuth2 (51)**, then **API-key (28)**; access is mostly **self-serve-free (70)**.
- **40 / 100** already covered by Composio; **45 / 100** ship an MCP server.
- **Verified accuracy 70%** on a 20-app hand-labeled sample, up from a **56% first pass** after two
  verification loops (see the Accuracy section of the page, misses shown openly).

## Quick start

```powershell
pip install -r requirements.txt
copy .env.example .env        # then paste your Firecrawl key into .env
python run.py                 # full pipeline -> site/index.html
```

Only a **Firecrawl API key** is required (free tier works). An optional `GEMINI_API_KEY`
enables a true second-model critic; without it, the Firecrawl re-extraction + diff is the critic.

### Cheap first run
Set `MAX_APPS=10` in `.env` to test the whole pipeline on 10 apps before spending credits on 100.

### Run individual stages
```powershell
python run.py agent      # research only  -> data/results.json
python run.py patterns   # recompute patterns
python run.py verify     # recompute accuracy vs data/gold_labels.json
python run.py site       # rebuild site/index.html from existing data (no key needed)
```

## Why these tools (justification)

| Choice | Why |
| --- | --- |
| **Firecrawl** | Search + scrape + structured JSON extraction in one API. Its search results double as the **evidence URLs**, so sourcing is automatic. Free tier → any reviewer can reproduce the run. |
| **Verdict by rule, not LLM** | The most subjective field becomes deterministic and auditable. |
| **Composio catalog cross-reference** | If Composio already ships a toolkit, that's near-ground-truth for buildability + auth, and answers the real question: *what do we already cover vs. the gap.* |
| **Two verification loops + gold sample** | Accuracy is the graded thing. We show it move from a first pass to a higher number, and show the misses. |
| **Static HTML + GitHub Pages** | A 2-minute, self-explanatory page with no runtime; repo + live link in one place. |

## How accuracy is measured (the honest part)

- `data/gold_labels.json` is a **hand-labeled stratified sample of 20 apps** (all 10 categories,
  every auth pattern, easy→gated, plus edge cases like Sherlock / Mermaid CLI that aren't APIs).
- `verify.py` compares the agent to the gold set on **auth, access model, verdict, and MCP**, and
  reports **first-pass vs. after-loops** accuracy. Loop B (re-checking the access model on the
  pricing page) is what moves the number — the count of changed rows is reported.
- Every sampled miss is listed on the page, unhidden.

> The gold labels are the reviewer's best-known values as of the check. **Confirm them against
> the evidence URL and correct any that are stale** — refreshing them *is* the human loop.

## Where a human was needed
- **Obscure / thin-doc apps** (iPayX, Paygent, fanbasis, Waterfall.io, higgsfield): search returns
  little; low-confidence flags route these to manual review.
- **Not-an-API edge cases** (Sherlock OSS CLI, Mermaid CLI, NotebookLM): correctly labeling these
  as *not* agent-callable is a human judgment the rule encodes.
- **The gold labels** themselves, which anchor the accuracy measurement.

## Cost control
Every raw Firecrawl response is cached to `data/raw_cache/` (git-ignored). Re-runs, the critic
pass, and site rebuilds cost **zero credits**. Budget ≈ 1 search + 1 extract per app, plus 1
pricing scrape for the apps that need the gate re-check (~2–3 credits/app).

## Layout
```
run.py                  entrypoint (stages: agent | patterns | verify | site | all)
src/config.py           env + paths
src/schema.py           record schema, Firecrawl extraction contract, verdict rule
src/firecrawl_client.py search / scrape / JSON-extract with disk cache + retries
src/extractor.py        first-pass research for one app
src/composio_catalog.py Composio toolkit cross-reference
src/critic.py           Loop A (confidence) + Loop B (access re-check)
src/agent.py            concurrent orchestrator -> data/results.json
src/verify.py           accuracy vs gold sample -> data/verification.json
src/patterns.py         aggregate patterns -> data/patterns.json
src/build_site.py       render self-contained site/index.html
data/apps.json          the 100-app seed list
data/gold_labels.json   hand-labeled accuracy sample
data/composio_known.json reviewer-seeded Composio coverage map
```

## Limitations (stated honestly on the page too)
- Extraction quality depends on the page Firecrawl lands on; low-confidence rows are flagged.
- `composio_known.json` is seeded from the reviewer's knowledge; set `COMPOSIO_SEARCH=true` to
  confirm/fill exact toolkit URLs via Firecrawl.
- Access model for apps with sandbox-free-but-production-gated tiers (e.g. Plaid) is genuinely
  nuanced; the page notes these rather than pretending they're binary.
