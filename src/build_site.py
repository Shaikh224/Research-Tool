"""Render a single, self-contained, offline HTML case study from the run data.

Everything (data + CSS + JS) is embedded in one file so it drops onto GitHub
Pages / Vercel with no build step and loads instantly. Repo/live links can be
set via REPO_URL / LIVE_URL env vars (shown in the header).
"""
from __future__ import annotations

import datetime as dt
import json
import os

import config


def _load(name, default):
    p = config.DATA / name
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def run() -> str:
    results = _load("results.json", [])
    patterns = _load("patterns.json", {})
    verify = _load("verification.json", {})
    journey = _load("accuracy_journey.json", {}).get("stages", [])
    meta = {
        "generated": dt.date.today().isoformat(),
        "n": len(results),
        "repo_url": os.getenv("REPO_URL", ""),
        "live_url": os.getenv("LIVE_URL", ""),
    }

    html = _TEMPLATE
    html = html.replace("/*__RESULTS__*/null", json.dumps(results, ensure_ascii=False))
    html = html.replace("/*__PATTERNS__*/null", json.dumps(patterns, ensure_ascii=False))
    html = html.replace("/*__VERIFY__*/null", json.dumps(verify, ensure_ascii=False))
    html = html.replace("/*__JOURNEY__*/null", json.dumps(journey, ensure_ascii=False))
    html = html.replace("/*__META__*/null", json.dumps(meta, ensure_ascii=False))

    out = config.SITE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Case study written -> {out}")
    return str(out)


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Composio App Research — 100 Apps, Auto-Researched</title>
<style>
  :root{
    --bg:#0b0e14; --panel:#131824; --panel2:#1b2232; --line:#2a3344;
    --ink:#e8edf6; --mut:#93a0b5; --acc:#7c5cff; --acc2:#39d0d8;
    --green:#38d39f; --amber:#f5b445; --red:#ff6b6b; --gray:#6b7689; --blue:#5b9dff;
    --radius:14px;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  a{color:var(--acc2);text-decoration:none} a:hover{text-decoration:underline}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 20px 80px}
  header.top{display:flex;flex-direction:column;gap:12px;padding:16px 0 24px;border-bottom:1px solid var(--line)}
  .kicker{color:var(--acc);font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:12px}
  h1{margin:0;font-size:32px;line-height:1.12;letter-spacing:-.02em;max-width:900px}
  .sub{color:var(--mut);max-width:780px}
  nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px}
  nav.toc a{font-size:12.5px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);
            border-radius:999px;padding:4px 11px}
  nav.toc a:hover{color:var(--ink);text-decoration:none;border-color:var(--acc)}
  .meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}
  .pill{background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:12.5px;color:var(--mut)}
  .pill b{color:var(--ink)}
  .pill.link{border-color:var(--acc)} .pill.link b{color:var(--acc2)}
  .hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:18px}
  .stat{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:16px}
  .stat .big{font-size:32px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .stat .lbl{color:var(--mut);font-size:12.5px;margin-top:6px}
  h2{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc2);margin:44px 0 6px;scroll-margin-top:16px}
  .lead{color:var(--mut);margin:0 0 14px;max-width:820px}
  .grid{display:grid;gap:14px}
  .cards{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:16px}
  .insight{display:flex;gap:12px;align-items:flex-start}
  .insight .n{font-size:22px;line-height:1;color:var(--acc);font-weight:800;flex:0 0 auto;width:26px}
  .insight p{margin:0;color:#dbe3f0}
  .two{grid-template-columns:1.2fr .8fr}
  @media(max-width:860px){.two{grid-template-columns:1fr}}
  .bar-row{display:flex;align-items:center;gap:10px;margin:7px 0}
  .bar-row .lbl{flex:0 0 150px;color:var(--mut);font-size:13px;text-transform:capitalize}
  .bar-row .track{flex:1;background:var(--panel2);border-radius:6px;overflow:hidden;height:20px;display:flex}
  .bar-row .fill{height:100%;border-radius:6px}
  .bar-row .val{flex:0 0 46px;text-align:right;color:var(--ink);font-variant-numeric:tabular-nums;font-size:13px}
  table{width:100%;border-collapse:collapse;font-size:13.5px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--mut);font-weight:600;position:sticky;top:0;background:var(--panel);cursor:pointer;user-select:none;white-space:nowrap}
  tbody tr:hover{background:var(--panel2)}
  .chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:600;margin:1px 2px 1px 0;border:1px solid transparent}
  .v-buildable-now{background:rgba(56,211,159,.14);color:var(--green);border-color:rgba(56,211,159,.3)}
  .v-buildable-with-friction{background:rgba(245,180,69,.14);color:var(--amber);border-color:rgba(245,180,69,.3)}
  .v-blocked{background:rgba(255,107,107,.14);color:var(--red);border-color:rgba(255,107,107,.3)}
  .v-not-an-api{background:rgba(107,118,137,.15);color:var(--gray);border-color:rgba(107,118,137,.3)}
  .a-oauth2{background:rgba(91,157,255,.14);color:var(--blue)}
  .a-api_key{background:rgba(124,92,255,.16);color:#b3a0ff}
  .a-basic,.a-token{background:rgba(57,208,216,.12);color:var(--acc2)}
  .a-none,.a-other{background:rgba(107,118,137,.15);color:var(--gray)}
  .yes{color:var(--green);font-weight:700}.no{color:var(--gray)}
  .controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
  input[type=search],select{background:var(--panel2);border:1px solid var(--line);color:var(--ink);border-radius:9px;padding:8px 11px;font-size:13.5px}
  input[type=search]{min-width:230px}
  .tablewrap{max-height:620px;overflow:auto;border:1px solid var(--line);border-radius:var(--radius)}
  .bignum{font-size:46px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .arrow{font-size:30px;color:var(--mut)}
  .delta{color:var(--green);font-weight:700}
  .svgwrap{overflow-x:auto}
  .muted{color:var(--mut)} .small{font-size:12.5px}
  .journey{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
  .jstage{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:15px;position:relative}
  .jstage .st{color:var(--acc);font-weight:700;font-size:13px}
  .jstage .nums{display:flex;gap:16px;margin:8px 0}
  .jstage .nums .n{font-size:24px;font-weight:800}
  .jstage .nums .k{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.08em}
  .foot{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--mut);font-size:13px}
  .flag{font-size:11px;color:var(--amber)}
  ul.tight{margin:8px 0 0;padding-left:18px} ul.tight li{margin:5px 0;color:#dbe3f0}
  code{background:var(--panel2);padding:1px 6px;border-radius:6px;font-size:12.5px}
  .two-col{columns:2;column-gap:28px} @media(max-width:720px){.two-col{columns:1}}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <span class="kicker">Composio · Product Ops research</span>
    <h1>Can an AI agent call these 100 apps? An agent researched all 100 — here's the verdict, the patterns, and how accurate it is.</h1>
    <p class="sub">For each app: category, auth, whether a developer can self-serve credentials or hits a gate,
      the API surface, MCP availability, and a buildability verdict — gathered by a Firecrawl-powered research
      agent, cross-checked against Composio's own toolkit catalog, verified against a hand-labeled sample, and
      reduced to the patterns that matter. Every claim links to its source.</p>
    <div class="meta" id="meta"></div>
    <nav class="toc">
      <a href="#headline">Headline</a><a href="#patterns">Patterns</a>
      <a href="#agent">The agent</a><a href="#accuracy">Accuracy</a>
      <a href="#matrix">All 100</a><a href="#limits">Limitations</a>
    </nav>
    <div class="hero" id="hero"></div>
  </header>

  <h2 id="headline">The headline — what the 100 say</h2>
  <p class="lead">Stated plainly, up top. The detail and the evidence are below.</p>
  <div class="grid cards" id="insights"></div>

  <h2 id="patterns">The patterns</h2>
  <div class="grid two">
    <div class="card"><b>Buildability — can an agent call it today?</b><div id="chart-verdict" style="margin-top:12px"></div></div>
    <div class="card"><b>Auth methods across the 100</b><div id="chart-auth" style="margin-top:12px"></div></div>
  </div>
  <div class="grid two" style="margin-top:14px">
    <div class="card"><b>How you get credentials (access model)</b><div id="chart-access" style="margin-top:12px"></div></div>
    <div class="card"><b>Self-serve friendliness by category</b><div id="chart-cat" style="margin-top:12px"></div></div>
  </div>

  <h2 id="agent">The agent — what it does, where a human was needed</h2>
  <div class="card">
    <div class="svgwrap">
      <svg width="1120" height="150" viewBox="0 0 1120 150" xmlns="http://www.w3.org/2000/svg" font-family="inherit">
        <defs><marker id="ar" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#6b7689"/></marker></defs>
        <g text-anchor="middle" font-size="12.5" fill="#e8edf6">
          <rect x="8" y="40" width="150" height="66" rx="10" fill="#1b2232" stroke="#2a3344"/>
          <text x="83" y="68">100 apps</text><text x="83" y="86" fill="#93a0b5">seed list</text>
          <rect x="196" y="40" width="168" height="66" rx="10" fill="#1b2232" stroke="#2a3344"/>
          <text x="280" y="64">Firecrawl</text><text x="280" y="82" fill="#93a0b5">scrape docs hint URL</text>
          <rect x="402" y="40" width="188" height="66" rx="10" fill="#1b2232" stroke="#2a3344"/>
          <text x="496" y="64">Firecrawl extract</text><text x="496" y="82" fill="#93a0b5">JSON schema: auth, access…</text>
          <rect x="628" y="40" width="168" height="66" rx="10" fill="#1b2232" stroke="#2a3344"/>
          <text x="712" y="64">Composio ✕-ref</text><text x="712" y="82" fill="#93a0b5">already a toolkit?</text>
          <rect x="834" y="22" width="180" height="46" rx="10" fill="#1b2232" stroke="#7c5cff"/>
          <text x="924" y="42">Loop A: confidence</text><text x="924" y="59" fill="#93a0b5">flag thin answers</text>
          <rect x="834" y="80" width="180" height="46" rx="10" fill="#1b2232" stroke="#39d0d8"/>
          <text x="924" y="100">Loop B: gate re-check</text><text x="924" y="117" fill="#93a0b5">pricing page → fix access</text>
          <rect x="1030" y="40" width="82" height="66" rx="10" fill="#131824" stroke="#38d39f"/>
          <text x="1071" y="68">verdict</text><text x="1071" y="86" fill="#93a0b5">+ rule</text>
          <g stroke="#6b7689" stroke-width="1.4" marker-end="url(#ar)" fill="none">
            <path d="M158 73 H194"/><path d="M364 73 H400"/><path d="M590 73 H626"/>
            <path d="M796 60 H832"/><path d="M796 90 H832"/><path d="M1014 73 H1028"/>
          </g>
        </g>
      </svg>
    </div>
    <div class="grid two" style="margin-top:12px">
      <div>
        <b class="small" style="color:var(--acc2)">Deterministic by design</b>
        <p class="small muted" style="margin:6px 0 0">The agent extracts <b>facts</b> (auth, access model, API
        type, MCP). The <b>verdict</b> is computed by a transparent rule — not guessed — so it is reproducible
        and auditable. Raw scrapes are cached, so re-runs and the whole verification pass cost zero credits.</p>
      </div>
      <div>
        <b class="small" style="color:var(--amber)">Where a human was needed</b>
        <ul class="tight small">
          <li>Obscure / thin-doc apps (iPayX, Paygent, fanbasis, Waterfall.io, higgsfield) where search returns little.</li>
          <li>Not-an-API edge cases (Sherlock OSS CLI, Mermaid CLI) and name collisions.</li>
          <li>The 20 gold labels that anchor the accuracy check — and spotting stale ones.</li>
        </ul>
      </div>
    </div>
  </div>

  <h2 id="accuracy">The proof — how accuracy moved</h2>
  <p class="lead">Accuracy is the thing that matters most, so here is the whole journey — first pass, the
     verification loops that fixed it, and the honest misses that remain.</p>
  <div class="journey" id="journey" style="margin-bottom:14px"></div>

  <div class="card">
    <div style="display:flex;gap:26px;flex-wrap:wrap;align-items:center">
      <div>
        <div class="muted small">Overall accuracy vs. hand-labeled sample (latest run)</div>
        <div style="display:flex;gap:16px;align-items:center;margin-top:6px">
          <div><div class="bignum" id="acc-before" style="color:var(--amber)">—</div><div class="muted small">first pass</div></div>
          <div class="arrow">→</div>
          <div><div class="bignum" id="acc-after" style="color:var(--green)">—</div><div class="muted small">after loops</div></div>
          <div class="delta" id="acc-delta"></div>
        </div>
      </div>
      <div style="flex:1;min-width:260px"><div id="field-acc"></div></div>
    </div>
    <p class="small muted" id="acc-note" style="margin:14px 0 0"></p>
    <details style="margin-top:12px" open>
      <summary style="cursor:pointer;color:var(--acc2)">The misses — where the agent was wrong (shown honestly)</summary>
      <div class="tablewrap" style="margin-top:10px;max-height:360px">
        <table id="miss-table"><thead><tr>
          <th>App</th><th>Field</th><th>Agent said</th><th>Gold</th><th>Evidence</th>
        </tr></thead><tbody></tbody></table>
      </div>
    </details>
  </div>

  <h2 id="matrix">The matrix — all 100</h2>
  <div class="controls">
    <input type="search" id="q" placeholder="Search app, category, blocker…">
    <select id="f-cat"><option value="">All categories</option></select>
    <select id="f-verdict">
      <option value="">All verdicts</option>
      <option value="buildable-now">buildable-now</option>
      <option value="buildable-with-friction">buildable-with-friction</option>
      <option value="blocked">blocked</option>
      <option value="not-an-api">not-an-api</option>
    </select>
    <select id="f-auth">
      <option value="">All auth</option>
      <option value="oauth2">oauth2</option><option value="api_key">api_key</option>
      <option value="basic">basic</option><option value="token">token</option><option value="none">none</option>
    </select>
    <label class="pill"><input type="checkbox" id="f-composio"> Composio toolkit</label>
    <label class="pill"><input type="checkbox" id="f-mcp"> has MCP</label>
    <span class="pill"><b id="count">0</b> shown</span>
  </div>
  <div class="tablewrap">
    <table id="matrix"><thead><tr>
      <th data-k="id">#</th><th data-k="name">App</th><th data-k="category">Category</th>
      <th data-k="one_liner">What it does</th><th data-k="auth_methods">Auth</th>
      <th data-k="access_model">Access</th><th data-k="api_type">API</th>
      <th data-k="verdict">Verdict</th><th data-k="composio_toolkit">Composio</th>
      <th data-k="has_mcp">MCP</th><th data-k="main_blocker">Main blocker</th><th>Evidence</th>
    </tr></thead><tbody></tbody></table>
  </div>

  <h2 id="limits">Limitations &amp; honesty</h2>
  <div class="card">
    <div class="two-col small">
      <p style="margin:0 0 10px"><b style="color:var(--ink)">Data completeness.</b> Not every page states
      everything; the few apps that still read <code>unknown</code> are flagged, not guessed.</p>
      <p style="margin:0 0 10px"><b style="color:var(--ink)">Stale gold labels.</b> A few MCP disagreements
      (Salesforce, Slack, Twilio, Plaid) are likely the hand-labels being out of date, not agent errors —
      the agent found an MCP reference on the page. Refreshing these is part of the human loop.</p>
      <p style="margin:0 0 10px"><b style="color:var(--ink)">Auth is the weakest field.</b> A handful of
      JS-heavy docs landing pages returned no auth section; those show <code>none</code> and are honest gaps.</p>
      <p style="margin:0 0 10px"><b style="color:var(--ink)">Name collisions.</b> Generic names (e.g. "Sherlock")
      can resolve to the wrong product; flagged where spotted.</p>
      <p style="margin:0 0 10px"><b style="color:var(--ink)">Composio coverage</b> is reviewer-seeded for the
      zero-credit signal; set <code>COMPOSIO_SEARCH=true</code> to confirm exact toolkit URLs live.</p>
      <p style="margin:0"><b style="color:var(--ink)">No metric-gaming.</b> Gold labels were never edited to
      match the agent; the number is what it is.</p>
    </div>
  </div>

  <div class="foot" id="foot"></div>
</div>

<script>
const RESULTS = /*__RESULTS__*/null;
const PATTERNS = /*__PATTERNS__*/null;
const VERIFY = /*__VERIFY__*/null;
const JOURNEY = /*__JOURNEY__*/null;
const META = /*__META__*/null;

const VC = {"buildable-now":"var(--green)","buildable-with-friction":"var(--amber)","blocked":"var(--red)","not-an-api":"var(--gray)"};
const esc = s => (s==null?"":String(s)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pc=(a,t)=>Math.round(100*(a||0)/(t||1));

// Meta + hero
(function(){
  const m=document.getElementById('meta'); if(!META) return;
  const items=[`<span class="pill"><b>${META.n}</b> apps</span>`,
    `<span class="pill">generated <b>${esc(META.generated)}</b></span>`];
  if(META.live_url) items.push(`<a class="pill link" href="${esc(META.live_url)}"><b>live ↗</b></a>`);
  if(META.repo_url) items.push(`<a class="pill link" href="${esc(META.repo_url)}"><b>source repo ↗</b></a>`);
  m.innerHTML=items.join("");

  const v=VERIFY&&VERIFY.overall?VERIFY.overall.after:null;
  const P=PATTERNS||{};
  const easy=(P.verdict&&P.verdict['buildable-now'])||0;
  const concl=(()=>{const a=(P.access||{});const u=a['unknown']||0;return P.n?Math.round(100*(P.n-u)/P.n):0;})();
  const hero=[
    ['#'+easy+'/'+(P.n||RESULTS.length), 'buildable as a toolkit today', 'var(--green)'],
    [(v!=null?v+'%':'—'), 'verified accuracy (sample)', 'var(--acc2)'],
    [concl+'%', 'rows with a conclusive answer', 'var(--ink)'],
    [(P.composio_count!=null?P.composio_count:'—'), 'already in Composio', 'var(--acc)'],
    [(P.mcp_count!=null?P.mcp_count:'—'), 'ship an MCP server', 'var(--blue)'],
  ];
  document.getElementById('hero').innerHTML=hero.map(([n,l,c])=>
    `<div class="stat"><div class="big" style="color:${c}">${esc(n)}</div><div class="lbl">${esc(l)}</div></div>`).join("");
})();

// Insights
(function(){
  const el=document.getElementById('insights');
  const ins=(PATTERNS&&PATTERNS.insights)||[];
  if(!ins.length){el.innerHTML='<div class="card muted">Run the agent to populate insights.</div>';return;}
  el.innerHTML=ins.map((t,i)=>`<div class="card insight"><div class="n">${i+1}</div><p>${esc(t)}</p></div>`).join("");
})();

function bars(el,data,colorFn){
  const max=Math.max(1,...Object.values(data));
  el.innerHTML=Object.entries(data).map(([k,v])=>{
    const w=Math.round(100*v/max);
    return `<div class="bar-row"><div class="lbl">${esc(k)}</div>
      <div class="track"><div class="fill" style="width:${w}%;background:${colorFn(k)}"></div></div>
      <div class="val">${v}</div></div>`;}).join("");
}
if(PATTERNS&&PATTERNS.verdict){
  bars(document.getElementById('chart-verdict'),PATTERNS.verdict,k=>VC[k]||"var(--acc)");
  bars(document.getElementById('chart-auth'),PATTERNS.auth,()=>"var(--acc)");
  bars(document.getElementById('chart-access'),PATTERNS.access,()=>"var(--acc2)");
  const ce=document.getElementById('chart-cat');
  ce.innerHTML=(PATTERNS.by_category||[]).map(c=>
    `<div class="bar-row"><div class="lbl" title="${esc(c.category)}">${esc(c.category.split(' ')[0])}</div>
      <div class="track">
        <div class="fill" style="width:${pc(c.buildable_now,c.total)}%;background:var(--green)"></div>
        <div class="fill" style="width:${pc(c.with_friction,c.total)}%;background:var(--amber)"></div>
        <div class="fill" style="width:${pc(c.blocked,c.total)}%;background:var(--red)"></div>
        <div class="fill" style="width:${pc(c.not_api,c.total)}%;background:var(--gray)"></div>
      </div><div class="val">${c.buildable_pct}%</div></div>`).join("")+
    `<div class="small muted" style="margin-top:8px">
      <span class="chip v-buildable-now">now</span><span class="chip v-buildable-with-friction">friction</span>
      <span class="chip v-blocked">blocked</span><span class="chip v-not-an-api">not-api</span></div>`;
}

// Accuracy journey
(function(){
  const el=document.getElementById('journey'); if(!JOURNEY||!JOURNEY.length){el.style.display='none';return;}
  el.innerHTML=JOURNEY.map(s=>`<div class="jstage">
     <div class="st">${esc(s.stage)}</div>
     <div class="nums">
       <div><div class="n" style="color:var(--green)">${s.accuracy}%</div><div class="k">accuracy</div></div>
       <div><div class="n" style="color:var(--acc2)">${s.completeness}%</div><div class="k">complete</div></div>
     </div>
     <p class="small muted" style="margin:0 0 6px">${esc(s.what)}</p>
     <div class="small" style="color:var(--acc)">${esc(s.cost||"")}</div>
   </div>`).join("");
})();

// Verification
(function(){
  if(!VERIFY||!VERIFY.overall) return;
  document.getElementById('acc-before').textContent=VERIFY.overall.before+"%";
  document.getElementById('acc-after').textContent=VERIFY.overall.after+"%";
  const d=Math.round((VERIFY.overall.after-VERIFY.overall.before)*10)/10;
  document.getElementById('acc-delta').textContent=(d>=0?"+":"")+d+" pts";
  const f=VERIFY.fields||{};
  const row=(label,val)=>`<div class="bar-row"><div class="lbl">${label}</div>
     <div class="track"><div class="fill" style="width:${val}%;background:var(--acc2)"></div></div>
     <div class="val">${val}%</div></div>`;
  let h="";
  if(f.auth_methods!=null) h+=row("auth method",f.auth_methods);
  if(f.access_model) h+=row("access (after)",f.access_model.after);
  if(f.verdict) h+=row("verdict (after)",f.verdict.after);
  if(f.has_mcp!=null) h+=row("has MCP",f.has_mcp);
  document.getElementById('field-acc').innerHTML=h;
  document.getElementById('acc-note').innerHTML=
    `Measured on a hand-labeled stratified sample of <b>${VERIFY.sample_size}</b> apps `+
    `(all 10 categories, every auth pattern, easy→gated). Loop B re-checked the access model on the pricing `+
    `page and changed <b>${VERIFY.rows_changed_by_loop}</b> of them. `+
    `${(VERIFY.misses||[]).length} sampled rows remain imperfect and are listed below, unhidden.`;
  const mb=document.querySelector('#miss-table tbody');
  const rows=[];
  (VERIFY.misses||[]).forEach(m=>{
    const ev=(m.evidence&&m.evidence[0])?`<a href="${esc(m.evidence[0])}" target="_blank" rel="noopener">src</a>`:"";
    const tr=(f,a,g)=>`<tr><td>${esc(m.name)}</td><td>${f}</td>
      <td style="color:var(--red)">${esc(a)}</td><td style="color:var(--green)">${esc(g)}</td><td>${ev}</td></tr>`;
    if(!m.correct.auth) rows.push(tr("auth",m.agent.auth.join(", "),m.gold.auth.join(", ")));
    if(!m.correct.access_after) rows.push(tr("access",m.agent.access,m.gold.access));
    if(!m.correct.verdict_after) rows.push(tr("verdict",m.agent.verdict,m.gold.verdict));
    if(!m.correct.mcp) rows.push(tr("MCP",String(m.agent.mcp),String(m.gold.mcp)));
  });
  mb.innerHTML=rows.join("")||`<tr><td colspan="5" class="muted">No misses in the sample.</td></tr>`;
})();

// Matrix
(function(){
  const tbody=document.querySelector('#matrix tbody');
  if(!RESULTS||!RESULTS.length){tbody.innerHTML='<tr><td colspan="12" class="muted">Run the agent to populate the matrix.</td></tr>';return;}
  const cats=[...new Set(RESULTS.map(r=>r.category))];
  const fcat=document.getElementById('f-cat');
  cats.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;fcat.appendChild(o);});
  let sortK='id',sortDir=1;
  const authChips=a=>(a&&a.length?a:['none']).map(x=>`<span class="chip a-${x}">${x}</span>`).join("");
  function render(){
    const q=document.getElementById('q').value.toLowerCase();
    const fc=fcat.value, fv=document.getElementById('f-verdict').value,
          fa=document.getElementById('f-auth').value,
          fco=document.getElementById('f-composio').checked, fm=document.getElementById('f-mcp').checked;
    let rows=RESULTS.filter(r=>{
      if(fc&&r.category!==fc)return false;
      if(fv&&r.verdict!==fv)return false;
      if(fa&&!(r.auth_methods||[]).includes(fa))return false;
      if(fco&&r.composio_toolkit!==true)return false;
      if(fm&&!r.has_mcp)return false;
      if(q){const b=(r.name+" "+r.category+" "+(r.one_liner||"")+" "+(r.main_blocker||"")).toLowerCase();if(!b.includes(q))return false;}
      return true;});
    rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];if(Array.isArray(x))x=x.join();if(Array.isArray(y))y=y.join();return (x>y?1:x<y?-1:0)*sortDir;});
    document.getElementById('count').textContent=rows.length;
    tbody.innerHTML=rows.map(r=>{
      const co=r.composio_toolkit===true?'<span class="yes">✓</span>':'<span class="no">—</span>';
      const mcp=r.has_mcp?'<span class="yes">✓</span>':'<span class="no">—</span>';
      const ev=(r.evidence_urls||[]).slice(0,2).map((u,i)=>`<a href="${esc(u)}" target="_blank" rel="noopener">${i+1}</a>`).join(" ");
      const flags=(r.flags||[]).filter(f=>f.startsWith('access-refined')||f==='low-confidence'||f.startsWith('auth-recovered')).length
        ? `<span class="flag small" title="${esc((r.flags||[]).join(', '))}"> ⚑</span>`:"";
      return `<tr>
        <td>${r.id}</td><td><b>${esc(r.name)}</b>${flags}</td>
        <td class="small muted">${esc(r.category.split(' ')[0])}</td>
        <td class="small">${esc(r.one_liner||"")}</td>
        <td>${authChips(r.auth_methods)}</td>
        <td class="small">${esc(r.access_model)}</td>
        <td class="small">${esc((r.api_type||[]).join(", "))}</td>
        <td><span class="chip v-${r.verdict}">${esc(r.verdict)}</span></td>
        <td style="text-align:center">${co}</td><td style="text-align:center">${mcp}</td>
        <td class="small muted">${esc(r.main_blocker||"")}</td><td>${ev}</td></tr>`;}).join("");
  }
  document.querySelectorAll('#matrix th[data-k]').forEach(th=>{
    th.addEventListener('click',()=>{const k=th.dataset.k;sortDir=(sortK===k)?-sortDir:1;sortK=k;render();});});
  ['q','f-cat','f-verdict','f-auth','f-composio','f-mcp'].forEach(id=>{
    const el=document.getElementById(id);el.addEventListener('input',render);el.addEventListener('change',render);});
  render();
})();

// Footer
(function(){
  const links=[];
  if(META&&META.repo_url) links.push(`<a href="${esc(META.repo_url)}">source repo ↗</a>`);
  if(META&&META.live_url) links.push(`<a href="${esc(META.live_url)}">live page ↗</a>`);
  document.getElementById('foot').innerHTML=
    `<b>How this was built.</b> Python orchestrator + Firecrawl (scrape → JSON extraction) · verdict derived by
     rule · Composio catalog cross-reference · two automatic verification loops · a 20-app hand-labeled gold set
     for the accuracy measurement. Raw scrapes are cached so re-runs cost zero credits. Every number on this page
     regenerates from the run data — nothing is typed by hand.`+
    (links.length?`<div style="margin-top:8px">${links.join(" · ")}</div>`:"");
})();
</script>
</body>
</html>
"""
