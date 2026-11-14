"""
Build a prioritized reading dashboard for the Claude articles deep-reading book.

Scores every catalog article for relevance to the user's professional context
(agentic coding tools / GitHub Copilot CLI work, enterprise AI automation,
Azure/.NET, M365 integrations, PR review automation, content writing),
checks that each source link is still reachable, folds in newly published
articles found via the live sitemap that aren't in the catalog yet, and
emits a single self-contained HTML dashboard.
"""
import csv
import json
import re
import datetime
import concurrent.futures
import urllib.request
import urllib.error

ROOT = r"C:\Users\ityshchenko\Documents\claude-articles-deep-reading-book"
CSV_PATH = ROOT + r"\data\claude_articles_deep_index.csv"
SITEMAP_PATH = ROOT + r"\sitemap.xml"
OUT_HTML = r"C:\Users\ityshchenko\Desktop\claude-articles-priority-dashboard.html"

CHAPTER_WEIGHT = {
    "Claude Code & software engineering": 10,
    "Agents & tool use": 10,
    "Platform, APIs & infrastructure": 8,
    "Enterprise adoption & operations": 7,
    "Product updates & models": 6,
    "Security, safety & governance": 5,
    "Productivity, education & creative work": 5,
    "Foundations & prompting": 5,
    "Customer stories & domain use cases": 4,
    "Partnerships & ecosystem": 4,
    "": 3,
}

CATEGORY_WEIGHT = {
    "Best practices": 4,
    "Insights": 3,
    "Product announcements": 2,
    "Perspectives": 2,
    "": 0,
}

KEYWORDS = [
    "agent", "subagent", "mcp", "code", "coding", "api", "sdk", "harness",
    "automation", "tool use", "orchestrat", "context", "enterprise",
    "security", "cost", "roi", "copilot", "workflow", "connector",
    "skill", "github", "devops", "microsoft", "integration",
]

today = datetime.date(2026, 11, 14)


def recency_bonus(date_str):
    try:
        d = datetime.date.fromisoformat(date_str)
    except ValueError:
        return 0
    months_old = (today - d).days / 30.4
    if months_old <= 1:
        return 6
    if months_old <= 3:
        return 4
    if months_old <= 6:
        return 2
    if months_old <= 12:
        return 1
    return 0


def keyword_bonus(title):
    t = title.lower()
    hits = sum(1 for k in KEYWORDS if k in t)
    return min(hits * 2, 6)


def score_article(title, chapter, category, date_str):
    s = CHAPTER_WEIGHT.get(chapter, 3)
    s += CATEGORY_WEIGHT.get(category, 0)
    s += keyword_bonus(title)
    s += recency_bonus(date_str)
    return round(s, 1)


def check_url(url, timeout=6):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                      headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except urllib.error.HTTPError as e:
        if e.code == 405:
            try:
                req = urllib.request.Request(url, method="GET",
                                              headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.status < 400
            except Exception:
                return False
        return False
    except Exception:
        return False


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(SITEMAP_PATH, encoding="utf-8") as f:
        sitemap = f.read()
    sitemap_urls = set(re.findall(
        r"<loc>(https://claude\.com/resources/articles/[^<]+)</loc>", sitemap))
    catalog_urls = set(r["url"].strip() for r in rows)
    new_urls = sorted(sitemap_urls - catalog_urls)

    new_meta = {
        "https://claude.com/resources/articles/building-always-on-agents": (
            "Building always-on agents", "Agents & tool use", "Best practices",
            "How stateful, proactive agents run on the core agent loop with primitives for wake triggers, carryover context, and delivery."),
        "https://claude.com/resources/articles/self-hosted-claude-managed-agents": (
            "Self-hosted Claude Managed Agents", "Agents & tool use", "Product announcements",
            "Private beta letting teams run the Managed Agents control plane (harness, sandboxes, credentials) inside their own environment."),
        "https://claude.com/resources/articles/message-threads": (
            "Message threads on the Claude Platform", "Platform, APIs & infrastructure", "Product announcements",
            "New thread API parameter cuts repeated context resends for long agent sessions, dropping median TTFT ~35% for large coding-agent sessions."),
        "https://claude.com/resources/articles/claude-enterprise-security-updates": (
            "Claude Enterprise security and admin updates", "Security, safety & governance", "Product announcements",
            "Security center, GA inference hooks, centralized admin console, Admin API sign-out, and IP allowlists for enterprise orgs."),
        "https://claude.com/resources/articles/how-to-manage-costs-and-demonstrate-roi-for-claude-code-on-google-cloud": (
            "Managing costs and ROI for Claude Code on Google Cloud", "Enterprise adoption & operations", "Best practices",
            "Three levers (control, track, prove) for platform teams to manage Claude Code spend and show business impact."),
        "https://claude.com/resources/articles/jpmorganchase-expands-claude-code": (
            "JPMorganChase expands Claude Code firm-wide", "Customer stories & domain use cases", "Product announcements",
            "Rollout beyond engineers, including PR-review and self-healing agents, infra/ops monitoring, and security vulnerability triage."),
        "https://claude.com/resources/articles/new-agents-and-products-claude-marketplace": (
            "New agents and products on Claude Marketplace", "Partnerships & ecosystem", "Product announcements",
            "Latest partner agent/product additions across security, dev infrastructure, creative, and productivity."),
        "https://claude.com/resources/articles/interactive-connectors-full-tool": (
            "Interactive connectors: full-tool view", "Platform, APIs & infrastructure", "Product announcements",
            "Interactive connectors can now open beside the conversation or go full-screen so Claude can work directly in your open tools."),
        "https://claude.com/resources/articles/more-ways-to-work-with-claude-sheets-whiteboards-and-interactive-connectors": (
            "Claude Sheets, Whiteboards, and upgraded interactive connectors", "Productivity, education & creative work", "Product announcements",
            "New artifact types (Sheets, Whiteboards, Data) plus an interactive-connectors upgrade and upcoming Claude Meetings."),
        "https://claude.com/resources/articles/sheets-whiteboards-data": (
            "Claude Whiteboards, Sheets, and Data (GA)", "Productivity, education & creative work", "Product announcements",
            "Whiteboards and Sheets launch in beta; Claude Dashboards becomes GA as Claude Data with certified queries and live sharing."),
        "https://claude.com/resources/articles/claude-meetings": (
            "Claude Meetings (beta)", "Productivity, education & creative work", "Product announcements",
            "Claude joins video calls as a visible participant, answers questions live, and writes notes/action items."),
        "https://claude.com/resources/articles/using-claude-opus-5-5-as-your-daily-driver-for-knowledge-work": (
            "Using Claude Opus 5.5 as your daily driver", "Product updates & models", "Best practices",
            "Opus 5.5 is now default on Pro/Max/Ultra/Team; guidance on when a stronger default model offsets its higher per-token cost."),
        "https://claude.com/resources/articles/claude-tag-guide-for-startups": (
            "Claude Tag guide for startups", "Enterprise adoption & operations", "Best practices",
            "Lessons from 8 high-growth startups on which Slack channels to add Claude Tag to first."),
        "https://claude.com/resources/articles/introducing-artifacts-for-legal-work": (
            "Artifacts for legal work", "Customer stories & domain use cases", "Product announcements",
            "Ready-to-use legal artifacts (contract review, regulatory tracking, intake) building on Claude for Legal."),
        "https://claude.com/resources/articles/claude-for-manufacturing": (
            "Claude for Manufacturing", "Customer stories & domain use cases", "Product announcements",
            "Plugin with connectors to Autodesk Fusion, Infor, Microsoft 365, and NetSuite for quoting, diagnostics, and approvals."),
        "https://claude.com/resources/articles/expanding-claude-for-nonprofits": (
            "Expanding Claude for Nonprofits", "Customer stories & domain use cases", "Product announcements",
            "Nonprofits plugin plus an expanded Claude Corps fellows partnership with Taproot."),
        "https://claude.com/resources/articles/introducing-personal-finance-in-claude": (
            "Personal Finance in Claude", "Productivity, education & creative work", "Product announcements",
            "Read-only bank/card connections so Claude can answer plain-language questions about your finances."),
        "https://claude.com/resources/articles/idc-brings-quanta-into-claude-and-adopts-claude-across-the-company": (
            "IDC brings Quanta into Claude", "Customer stories & domain use cases", "Product announcements",
            "IDC's research/forecast MCP connector surfaces IDC Quanta analysis directly inside Claude."),
        "https://claude.com/resources/articles/how-curative-is-building-a-national-provider-network-with-agents-on-claude": (
            "How Curative builds a provider network with agents", "Customer stories & domain use cases", "Insights",
            "Curative built a hierarchy of agents on Claude to sign provider contracts ~50x faster."),
        "https://claude.com/resources/articles/j-crew-style-advisor-with-claude": (
            "J.Crew Style Advisor built with Claude Code", "Customer stories & domain use cases", "Product announcements",
            "J.Crew built an AI stylist on JCrew.com with Claude Code using multiple Claude models matched to task."),
        "https://claude.com/resources/articles/smart-reports-surveys-pooled-budgets": (
            "Smart reports, in-app surveys, pooled budgets", "Enterprise adoption & operations", "Product announcements",
            "Admin features for measuring and reporting on team Claude adoption and spend."),
    }

    out_rows = []
    for r in rows:
        title, date, chapter, category = r["title"], r["date"], r["chapter"], r["category"]
        sc = score_article(title, chapter, category, date)
        out_rows.append({
            "title": title.strip(), "date": date, "chapter": chapter,
            "category": category, "deep_words": r["deep_words"],
            "url": r["url"].strip(), "score": sc, "is_new": False,
            "summary": "",
        })

    for u in new_urls:
        meta = new_meta.get(u)
        if not meta:
            continue
        title, chapter, category, summary = meta
        sc = score_article(title, chapter, category, "2026-11-10")
        out_rows.append({
            "title": title, "date": "2026-11 (new)", "chapter": chapter,
            "category": category, "deep_words": "", "url": u,
            "score": sc, "is_new": True, "summary": summary,
        })

    urls = [r["url"] for r in out_rows]
    status = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
        futs = {ex.submit(check_url, u): u for u in urls}
        for fut in concurrent.futures.as_completed(futs):
            u = futs[fut]
            try:
                status[u] = fut.result()
            except Exception:
                status[u] = False

    for r in out_rows:
        r["ok"] = status.get(r["url"], False)

    out_rows.sort(key=lambda r: r["score"], reverse=True)

    broken = [r for r in out_rows if not r["ok"]]
    print(f"Total articles (incl. new): {len(out_rows)}")
    print(f"New articles found: {len(new_urls)} (matched metadata: {sum(1 for r in out_rows if r['is_new'])})")
    print(f"Broken/unreachable links: {len(broken)}")
    for r in broken:
        print("  BROKEN:", r["url"])

    build_html(out_rows)


def build_html(rows):
    data_json = json.dumps(rows, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA__", data_json)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote", OUT_HTML)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Claude Articles - Priority Reading Dashboard</title>
<style>
  :root{--bg:#0f1115;--panel:#171a21;--panel2:#1d212b;--text:#e8eaed;--muted:#9aa3b2;
        --accent:#d97757;--good:#4caf7d;--bad:#e05d5d;--warn:#e0b65d;--border:#2a2f3a;}
  *{box-sizing:border-box;}
  body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text);}
  header{padding:24px 32px 12px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg);z-index:10;}
  h1{margin:0 0 4px;font-size:22px;}
  .sub{color:var(--muted);font-size:13px;margin-bottom:14px;}
  .controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding-bottom:14px;}
  input[type=text], select{background:var(--panel2);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:13px;}
  input[type=text]{width:260px;}
  .chip{padding:6px 12px;border-radius:999px;border:1px solid var(--border);background:var(--panel2);font-size:12px;cursor:pointer;color:var(--muted);}
  .chip.active{background:var(--accent);color:#1a1a1a;border-color:var(--accent);font-weight:600;}
  .stats{color:var(--muted);font-size:12px;margin-left:auto;}
  main{padding:18px 32px 60px;}
  .top-picks{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:22px;}
  .top-picks h2{margin:0 0 10px;font-size:15px;color:var(--accent);}
  .top-picks ol{margin:0;padding-left:20px;}
  .top-picks li{margin:4px 0;font-size:13px;}
  .top-picks a{color:var(--text);}
  table{width:100%;border-collapse:collapse;font-size:13px;}
  th{text-align:left;padding:8px 10px;color:var(--muted);font-weight:600;border-bottom:1px solid var(--border);position:sticky;top:120px;background:var(--bg);cursor:pointer;}
  td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top;}
  tr:hover td{background:var(--panel2);}
  .score{font-weight:700;color:var(--accent);}
  .badge{display:inline-block;padding:2px 7px;border-radius:5px;font-size:11px;font-weight:600;}
  .b-new{background:#2c4a3a;color:var(--good);}
  .b-ok{color:var(--good);}
  .b-bad{color:var(--bad);font-weight:700;}
  .chapter-tag{font-size:11px;color:var(--muted);}
  a.title-link{color:var(--text);text-decoration:none;font-weight:600;}
  a.title-link:hover{color:var(--accent);text-decoration:underline;}
  .summary{color:var(--muted);font-size:12px;margin-top:3px;max-width:520px;}
  .count{font-size:12px;color:var(--muted);margin:10px 0;}
</style>
</head>
<body>
<header>
  <h1>Claude Articles - Priority Reading Dashboard</h1>
  <div class="sub">Sorted by relevance to agentic coding / enterprise AI automation work. Click any title to open the source article (opens in a new tab). Data refreshed against the live claude.com sitemap.</div>
  <div class="controls">
    <input type="text" id="search" placeholder="Search title or chapter...">
    <select id="chapterFilter"><option value="">All chapters</option></select>
    <select id="categoryFilter"><option value="">All categories</option></select>
    <span class="chip" id="newOnly">New only</span>
    <span class="chip" id="brokenOnly">Broken links only</span>
    <span class="stats" id="stats"></span>
  </div>
</header>
<main>
  <div class="top-picks">
    <h2>Top picks for you right now</h2>
    <ol id="topPicks"></ol>
  </div>
  <div class="count" id="rowCount"></div>
  <table>
    <thead>
      <tr>
        <th data-key="score">Score</th>
        <th data-key="title">Article</th>
        <th data-key="chapter">Chapter</th>
        <th data-key="date">Date</th>
        <th data-key="ok">Link</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>
</main>
<script>
const DATA = __DATA__;
let sortKey = 'score', sortDir = -1;
let filters = { q:'', chapter:'', category:'', newOnly:false, brokenOnly:false };

const chapterSel = document.getElementById('chapterFilter');
const categorySel = document.getElementById('categoryFilter');
[...new Set(DATA.map(d=>d.chapter).filter(Boolean))].sort().forEach(c=>{
  const o=document.createElement('option'); o.value=c; o.textContent=c; chapterSel.appendChild(o);
});
[...new Set(DATA.map(d=>d.category).filter(Boolean))].sort().forEach(c=>{
  const o=document.createElement('option'); o.value=c; o.textContent=c; categorySel.appendChild(o);
});

function render(){
  let rows = DATA.filter(d=>{
    if(filters.q){
      const q = filters.q.toLowerCase();
      if(!d.title.toLowerCase().includes(q) && !d.chapter.toLowerCase().includes(q)) return false;
    }
    if(filters.chapter && d.chapter !== filters.chapter) return false;
    if(filters.category && d.category !== filters.category) return false;
    if(filters.newOnly && !d.is_new) return false;
    if(filters.brokenOnly && d.ok) return false;
    return true;
  });
  rows.sort((a,b)=>{
    let va=a[sortKey], vb=b[sortKey];
    if(typeof va === 'string'){ va=va.toLowerCase(); vb=vb.toLowerCase(); }
    if(va<vb) return -1*sortDir; if(va>vb) return 1*sortDir; return 0;
  });
  document.getElementById('rowCount').textContent = rows.length + ' of ' + DATA.length + ' articles shown';
  const tbody = document.getElementById('rows');
  tbody.innerHTML = rows.map(d=>`
    <tr>
      <td class="score">${d.score}</td>
      <td>
        <a class="title-link" href="${d.url}" target="_blank" rel="noopener">${d.is_new?'<span class="badge b-new">NEW</span> ':''}${escapeHtml(d.title)}</a>
        ${d.summary?`<div class="summary">${escapeHtml(d.summary)}</div>`:''}
      </td>
      <td><span class="chapter-tag">${escapeHtml(d.chapter||'-')}</span><br><span class="chapter-tag">${escapeHtml(d.category||'')}</span></td>
      <td>${d.date}</td>
      <td>${d.ok? '<span class="b-ok">opens</span>' : '<span class="b-bad">broken</span>'}</td>
    </tr>`).join('');

  const stats = DATA.length + ' total - ' + DATA.filter(d=>d.is_new).length + ' new - ' + DATA.filter(d=>!d.ok).length + ' broken';
  document.getElementById('stats').textContent = stats;

  const top = [...DATA].sort((a,b)=>b.score-a.score).slice(0,15);
  document.getElementById('topPicks').innerHTML = top.map(d=>`<li><a href="${d.url}" target="_blank" rel="noopener">${d.is_new?'[NEW] ':''}${escapeHtml(d.title)}</a> <span class="chapter-tag">- ${escapeHtml(d.chapter)} - score ${d.score}</span></li>`).join('');
}

function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

document.getElementById('search').addEventListener('input', e=>{ filters.q = e.target.value; render(); });
chapterSel.addEventListener('change', e=>{ filters.chapter = e.target.value; render(); });
categorySel.addEventListener('change', e=>{ filters.category = e.target.value; render(); });
document.getElementById('newOnly').addEventListener('click', e=>{ filters.newOnly=!filters.newOnly; e.target.classList.toggle('active'); render(); });
document.getElementById('brokenOnly').addEventListener('click', e=>{ filters.brokenOnly=!filters.brokenOnly; e.target.classList.toggle('active'); render(); });
document.querySelectorAll('th[data-key]').forEach(th=>{
  th.addEventListener('click', ()=>{
    const k = th.dataset.key;
    if(sortKey===k) sortDir*=-1; else { sortKey=k; sortDir = k==='score'?-1:1; }
    render();
  });
});

render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
