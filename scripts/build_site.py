#!/usr/bin/env python3
"""
Site Builder — Genera le pagine HTML statiche del sito.
Trasforma data/curated.json in news/index.html + tools/index.html
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# ─── CSS & HTML Templates ───────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --bg: #09090b;
  --surface: #111113;
  --surface2: #18181b;
  --border: #27272a;
  --text: #e4e4e7;
  --text2: #a1a1aa;
  --text3: #52525b;
  --accent: #8b5cf6;
  --accent2: #06b6d4;
  --green: #22c55e;
  --orange: #f97316;
  --pink: #ec4899;
  --yellow: #eab308;
  --red: #ef4444;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  line-height: 1.8;
}

/* ─── Nav ──────────────────────────────────────── */
nav {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
nav .logo {
  font-size: 18px;
  font-weight: 800;
  color: var(--text);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
nav .logo span { font-size: 22px; }
nav .links {
  display: flex;
  gap: 20px;
}
nav .links a {
  font-size: 13px;
  font-weight: 500;
  color: var(--text2);
  text-decoration: none;
  transition: color 0.2s;
}
nav .links a:hover, nav .links a.active {
  color: var(--accent);
}

/* ─── Header ───────────────────────────────────── */
.page-header {
  max-width: 900px;
  margin: 0 auto;
  padding: 48px 24px 32px;
}
.page-header h1 {
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 900;
  letter-spacing: -1px;
  margin-bottom: 8px;
}
.page-header h1 .gradient {
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.page-header p {
  font-size: 14px;
  color: var(--text2);
}
.page-header .date {
  font-size: 12px;
  color: var(--text3);
  margin-top: 4px;
}

/* ─── Content ──────────────────────────────────── */
.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 24px 80px;
}

/* ─── News Card ────────────────────────────────── */
.news-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
  position: relative;
}
.news-card:hover {
  border-color: var(--accent);
}
.news-card .card-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.news-card .source {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--accent);
  background: rgba(139,92,246,0.1);
  padding: 2px 8px;
  border-radius: 4px;
}
.news-card .time {
  font-size: 11px;
  color: var(--text3);
}
.news-card .score {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent2);
  margin-left: auto;
}
.news-card h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  line-height: 1.4;
}
.news-card h3 a {
  color: var(--text);
  text-decoration: none;
}
.news-card h3 a:hover {
  color: var(--accent);
}
.news-card .summary {
  font-size: 13px;
  color: var(--text2);
  line-height: 1.6;
  margin-bottom: 8px;
}
.news-card .link {
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  color: var(--accent);
  text-decoration: none;
  word-break: break-all;
}
.news-card .link:hover { text-decoration: underline; }

/* ─── Guide Card ───────────────────────────────── */
.guide-card {
  background: linear-gradient(135deg, rgba(139,92,246,0.06), rgba(6,182,212,0.06));
  border: 1px solid rgba(139,92,246,0.2);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.guide-card .guide-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--accent);
  margin-bottom: 8px;
}
.guide-card h3 {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 10px;
}
.guide-card .guide-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text3);
  margin-bottom: 12px;
}
.guide-card .guide-body {
  font-size: 14px;
  color: var(--text2);
  line-height: 1.8;
}
.guide-card .guide-body strong {
  color: var(--text);
}
.guide-card .guide-body code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  background: var(--surface2);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--accent2);
}
.guide-card .guide-body ul {
  padding-left: 18px;
  margin: 10px 0;
}
.guide-card .guide-body li {
  margin-bottom: 6px;
}

/* ─── Section Divider ──────────────────────────── */
.section-title {
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text3);
  margin: 40px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* ─── Footer ───────────────────────────────────── */
footer {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 12px;
  color: var(--text3);
}
footer a { color: var(--accent); text-decoration: none; }

/* ─── Level badges ─────────────────────────────── */
.level-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 4px;
}
.level-principiante { background: rgba(34,197,94,0.15); color: var(--green); }
.level-intermedio { background: rgba(234,179,8,0.15); color: var(--yellow); }
.level-avanzato { background: rgba(239,68,68,0.15); color: var(--red); }
"""


def nav(active: str) -> str:
    return f"""<nav>
  <a href="../index.html" class="logo"><span>🧠</span> AI Hub Italia</a>
  <div class="links">
    <a href="../index.html">Home</a>
    <a href="index.html"{' class="active"' if active == 'news' else ''}>📰 News</a>
    <a href="../tools/index.html"{' class="active"' if active == 'tools' else ''}>🛠️ Tool</a>
  </div>
</nav>"""


def format_time(iso_str: str) -> str:
    """Format ISO datetime to human-readable Italian."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return "pochi minuti fa"
        elif hours < 6:
            return f"{int(hours)}h fa"
        elif hours < 24:
            return f"oggi, {dt.strftime('%H:%M')}"
        elif hours < 48:
            return f"ieri, {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%d %b %Y")
    except (ValueError, TypeError):
        return ""


# ─── News Page ───────────────────────────────────────

def build_news_page(data: dict, guide: dict = None) -> str:
    """Build the news HTML page."""
    articles = data.get("articles", [])
    collected = data.get("collected_at", "")

    articles_html = ""
    for a in articles:
        time_str = format_time(a.get("published", ""))
        summary = a.get("summary", "")
        if a.get("summary_it"):
            summary = a["summary_it"]
        title = a.get("title_it") or a.get("title", "")
        
        articles_html += f"""
  <div class="news-card">
    <div class="card-top">
      <span class="source">{escape(a.get('source', ''))}</span>
      <span class="time">{time_str}</span>
      <span class="score">⭐ {a.get('score', 0):.1f}</span>
    </div>
    <h3><a href="{escape(a.get('link', '#'))}" target="_blank" rel="noopener">{escape(title)}</a></h3>
    <p class="summary">{escape(summary)}</p>
    <a href="{escape(a.get('link', '#'))}" class="link" target="_blank" rel="noopener">{escape(a.get('link', '')[:80])}</a>
  </div>"""

    # Guide section
    guide_html = ""
    if guide:
        level = guide.get("level", "principiante")
        guide_html = f"""
  <div class="section-title">📖 Impara Oggi</div>
  <div class="guide-card">
    <div class="guide-label">Guida quotidiana</div>
    <h3>{escape(guide.get('title', ''))}</h3>
    <div class="guide-meta">
      <span class="level-badge level-{level}">{level}</span>
      <span>🏷️ {escape(guide.get('tag', ''))}</span>
      <span>📖 ~5 min di lettura</span>
    </div>
    <div class="guide-body">
      {guide.get('content_html', '<p>Guida in preparazione...</p>')}
    </div>
  </div>"""

    date_str = format_time(collected) if collected else datetime.now().strftime("%d %B %Y")

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📰 News AI — AI Hub Italia</title>
<meta name="description" content="Le ultime notizie sull'intelligenza artificiale, tradotte e curate in italiano.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
<style>{CSS}</style>
</head>
<body>
{nav('news')}
<div class="page-header">
  <h1>📰 <span class="gradient">News AI</span></h1>
  <p>Le ultime notizie dall'AI, raccolte e tradotte ogni giorno.</p>
  <p class="date">Aggiornato: {date_str} · {len(articles)} articoli</p>
</div>
<div class="content">
  {guide_html}
  <div class="section-title">Ultime Notizie</div>
  {articles_html}
</div>
<footer>
  <p>AI Hub Italia — <a href="../index.html">Guida completa</a></p>
  <p style="margin-top:8px">Fonti: TechCrunch, The Verge, VentureBeat, Ars Technica, Hacker News e altre</p>
</footer>
</body>
</html>"""


# ─── Tools Page ──────────────────────────────────────

def stars(rating: int) -> str:
    """Convert rating to stars."""
    return "⭐" * rating + "☆" * (5 - rating)


def build_tools_page(tools_data: dict) -> str:
    """Build the tools HTML page."""
    tools = tools_data.get("tools", [])
    updated = tools_data.get("updated_at", "")

    # Group by category
    categories = {}
    for t in tools:
        cat = t.get("category", "uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    cat_labels = {
        "coding": "💻 Coding & Sviluppo",
        "chat": "💬 Chatbot & Assistente",
        "immagini": "🎨 Generazione Immagini",
        "musica": "🎵 Generazione Musica",
        "video": "🎬 Generazione Video",
        "audio": "🎙️ Audio & Voce",
        "ricerca": "🔍 Ricerca & Analisi",
        "agent": "🤖 Agenti",
        "produttività": "📊 Produttività",
        "presentazioni": "📽️ Presentazioni",
        "infrastruttura": "⚙️ Infrastruttura",
        "framework": "🔧 Framework",
        "modello": "🧠 Modelli",
        "uncategorized": "📦 Scoperti di recente",
    }

    tools_html = ""
    # Show featured first
    featured = [t for t in tools if t.get("featured")]
    if featured:
        tools_html += '<div class="section-title">⭐ In Evidenza</div>\n'
        for t in featured:
            tools_html += tool_card_html(t)

    # Then by category
    for cat in ["coding", "chat", "immagini", "musica", "video", "audio",
                 "ricerca", "agent", "produttività", "presentazioni",
                 "infrastruttura", "framework", "modello", "uncategorized"]:
        if cat not in categories:
            continue
        cat_tools = [t for t in categories[cat] if not t.get("featured")]
        if not cat_tools:
            continue
        label = cat_labels.get(cat, cat)
        tools_html += f'<div class="section-title">{label}</div>\n'
        for t in cat_tools:
            tools_html += tool_card_html(t)

    date_str = format_time(updated) if updated else datetime.now().strftime("%d %B %Y")

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🛠️ Tool AI — AI Hub Italia</title>
<meta name="description" content="I migliori strumenti di intelligenza artificiale, catalogati e recensiti in italiano.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
<style>{CSS}
/* ─── Extra Tool Styles ──────────────────────── */
.tool-card-grid {{
  display: grid;
  gap: 12px;
}}
.tool-card {{
  display: flex;
  flex-direction: column;
}}
.tool-card .tool-top {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}}
.tool-card .tool-name {{
  font-size: 16px;
  font-weight: 700;
}}
.tool-card .tool-name a {{
  color: var(--text);
  text-decoration: none;
}}
.tool-card .tool-name a:hover {{
  color: var(--accent);
}}
.tool-card .tool-cat {{
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(139,92,246,0.1);
  color: var(--accent);
}}
.tool-card .tool-stars {{
  font-size: 12px;
  margin-left: auto;
}}
.tool-card .tool-desc {{
  font-size: 13px;
  color: var(--text2);
  line-height: 1.6;
  margin-bottom: 8px;
}}
.tool-card .tool-meta {{
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text3);
  flex-wrap: wrap;
}}
.tool-card .tool-tags {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}}
.tool-card .tag {{
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--surface2);
  color: var(--text3);
}}
.featured-badge {{
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(234,179,8,0.15);
  color: var(--yellow);
}}
</style>
</head>
<body>
{nav('tools')}
<div class="page-header">
  <h1>🛠️ <span class="gradient">Tool AI</span></h1>
  <p>I migliori strumenti di intelligenza artificiale, catalogati e recensiti in italiano.</p>
  <p class="date">Aggiornato: {date_str} · {len(tools)} strumenti</p>
</div>
<div class="content tool-card-grid">
  {tools_html}
</div>
<footer>
  <p>AI Hub Italia — <a href="../index.html">Guida completa</a> · <a href="../news/">📰 News</a></p>
</footer>
</body>
</html>"""


def tool_card_html(t: dict) -> str:
    """Generate HTML for a single tool card."""
    tags_html = ""
    tags = t.get("tags", [])
    if tags:
        tags_html = '<div class="tool-tags">' + "".join(f'<span class="tag">{escape(tag)}</span>' for tag in tags[:5]) + '</div>'

    featured = '<span class="featured-badge">⭐ In Evidenza</span>' if t.get("featured") else ""
    rating = stars(t.get("rating", 0))
    url = escape(t.get("url", "#"))
    name = escape(t.get("name", ""))
    desc = escape(t.get("description_it", ""))
    pricing = escape(t.get("pricing", ""))

    return f"""
  <div class="news-card">
    <div class="tool-top">
      <span class="tool-name"><a href="{url}" target="_blank" rel="noopener">{name}</a></span>
      <span class="tool-cat">{escape(t.get('category', ''))}</span>
      {featured}
      <span class="tool-stars">{rating}</span>
    </div>
    <p class="summary">{desc}</p>
    <div class="tool-meta">
      <span>💰 {pricing}</span>
      <a href="{url}" class="link" target="_blank" rel="noopener">{url[:60]}</a>
    </div>
    {tags_html}
  </div>"""


# ─── Main ────────────────────────────────────────────

def main():
    curated_path = DATA_DIR / "curated.json"
    raw_path = DATA_DIR / "raw_news.json"

    # Use curated if available, otherwise raw
    data_path = curated_path if curated_path.exists() else raw_path
    if not data_path.exists():
        print("❌ No data found. Run news_scraper.py first.")
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    print(f"🔨 Building site from {data_path.name}")
    print(f"   Articles: {len(data.get('articles', []))}")

    # Load today's guide if exists
    guide = None
    guide_path = DATA_DIR / "daily_guide.json"
    if guide_path.exists():
        with open(guide_path) as f:
            guide = json.load(f)
        print(f"   Guide: {guide.get('title', 'N/A')}")

    # Build news page
    news_html = build_news_page(data, guide)
    news_dir = BASE_DIR / "news"
    news_dir.mkdir(exist_ok=True)
    (news_dir / "index.html").write_text(news_html, encoding="utf-8")
    print(f"   ✅ news/index.html")

    # Build tools page
    tools_path = DATA_DIR / "tools_db.json"
    if tools_path.exists():
        with open(tools_path) as f:
            tools_data = json.load(f)
        tools_html = build_tools_page(tools_data)
        tools_dir = BASE_DIR / "tools"
        tools_dir.mkdir(exist_ok=True)
        (tools_dir / "index.html").write_text(tools_html, encoding="utf-8")
        print(f"   ✅ tools/index.html ({tools_data.get('total', 0)} tools)")
    else:
        print(f"   ⚠️  No tools_db.json — run tools_scanner.py first")

    print("\n🏗️  Site built successfully!")


if __name__ == "__main__":
    main()
