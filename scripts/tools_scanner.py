#!/usr/bin/env python3
"""
AI Tools Scanner — Scopre e cataloga tool AI.
Output: data/tools_db.json
"""

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    import feedparser
except ImportError:
    import os, sys
    os.system(f"{sys.executable} -m pip install feedparser --break-system-packages -q")
    import feedparser

try:
    import requests
except ImportError:
    import os, sys
    os.system(f"{sys.executable} -m pip install requests --break-system-packages -q")
    import requests

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── Tool Sources ────────────────────────────────────

TOOL_SOURCES = [
    {
        "name": "There's An AI For That (feed)",
        "url": "https://theresanaiforthat.com/rss/",
        "type": "rss",
        "weight": 3,
    },
    {
        "name": "Product Hunt AI (feed)",
        "url": "https://www.producthunt.com/feed?category=ai",
        "type": "rss",
        "weight": 2,
    },
    {
        "name": "Hugging Face Spaces",
        "url": "https://huggingface.co/spaces/rss",
        "type": "rss",
        "weight": 2,
    },
]

# ─── Curated tools database ─────────────────────────
# Seed data: well-known AI tools with Italian descriptions

CURATED_TOOLS = [
    {
        "name": "Cursor",
        "url": "https://cursor.com",
        "category": "coding",
        "tags": ["ide", "coding", "autocomplete", "chat"],
        "pricing": "Freemium ($20/mese Pro)",
        "description_it": "IDE basato su VS Code con AI integrata. Autocomplete contestuale, chat inline, refactor con un click. Il 'vibe coding' fatto strumento.",
        "rating": 5,
        "featured": True,
    },
    {
        "name": "Claude Code",
        "url": "https://docs.anthropic.com/en/docs/claude-code",
        "category": "coding",
        "tags": ["cli", "agent", "coding", "git"],
        "pricing": "Piano Max",
        "description_it": "Agente di coding nel terminale. Legge il progetto, modifica file, esegue comandi, gestisce git. Un collega che lavora al posto tuo.",
        "rating": 5,
        "featured": True,
    },
    {
        "name": "Windsurf",
        "url": "https://windsurf.com",
        "category": "coding",
        "tags": ["ide", "coding", "agent", "multi-file"],
        "pricing": "Freemium ($15/mese Pro)",
        "description_it": "IDE AI con Cascade: analizza l'intero progetto e suggerisce modifiche multi-file. Ex Codeium.",
        "rating": 4,
        "featured": True,
    },
    {
        "name": "OpenClaw",
        "url": "https://openclaw.ai",
        "category": "agent",
        "tags": ["agent", "personale", "open-source", "mcp"],
        "pricing": "Open source (MIT)",
        "description_it": "Agente AI personale che gira sulla tua macchina. Gestisce email, calendario, codice, automazioni. Locale, privato, con MCP nativo.",
        "rating": 4,
        "featured": True,
    },
    {
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "category": "chat",
        "tags": ["chat", "multimodale", "ricerca", "coding"],
        "pricing": "Free / $20/mese Plus",
        "description_it": "Il chatbot più famoso al mondo. GPT-4o con visione, browsing, code interpreter, DALL-E integrato.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Claude",
        "url": "https://claude.ai",
        "category": "chat",
        "tags": ["chat", "analisi", "coding", "documenti"],
        "pricing": "Free / $20/mese Pro",
        "description_it": "Chatbot di Anthropic. Eccelle in analisi di documenti, coding, e conversazioni articolate. 200K token di contesto.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Midjourney",
        "url": "https://midjourney.com",
        "category": "immagini",
        "tags": ["generazione", "immagini", "arte", "v7"],
        "pricing": "$10/mese Basic",
        "description_it": "Generazione immagini AI di altissima qualità. La v7 ha un salto fotorealistico impressionante. Testo nelle immagini finalmente leggibile.",
        "rating": 5,
        "featured": True,
    },
    {
        "name": "Flux",
        "url": "https://blackforestlabs.ai",
        "category": "immagini",
        "tags": ["generazione", "immagini", "open-source", "locale"],
        "pricing": "Open source / API",
        "description_it": "Generazione immagini open-source di Black Forest Labs. Gira localmente con 12GB VRAM. L'alternativa a Midjourney per chi vuole controllo totale.",
        "rating": 4,
        "featured": True,
    },
    {
        "name": "Suno",
        "url": "https://suno.com",
        "category": "musica",
        "tags": ["generazione", "musica", "audio", "vocale"],
        "pricing": "Free / $10/mese Pro",
        "description_it": "Generazione musicale AI. Scrivi cosa vuoi e in 30 secondi hai una canzone completa: voce, testo, strumenti, mix.",
        "rating": 5,
        "featured": True,
    },
    {
        "name": "NotebookLM",
        "url": "https://notebooklm.google.com",
        "category": "ricerca",
        "tags": ["ricerca", "documenti", "podcast", "riassunti"],
        "pricing": "Gratuito",
        "description_it": "Carica documenti e l'AI li analizza, genera riassunti e produce podcast audio dove due 'host' discutono i tuoi contenuti. Non allucina.",
        "rating": 5,
        "featured": True,
    },
    {
        "name": "Ollama",
        "url": "https://ollama.com",
        "category": "infrastruttura",
        "tags": ["locale", "llm", "open-source", "self-hosted"],
        "pricing": "Open source",
        "description_it": "Esegui LLM locali in un comando. Llama, DeepSeek, Mistral — tutto sul tuo computer, senza costi, senza privacy concerns.",
        "rating": 4,
        "featured": True,
    },
    {
        "name": "Aider",
        "url": "https://aider.chat",
        "category": "coding",
        "tags": ["cli", "coding", "open-source", "git"],
        "pricing": "Open source",
        "description_it": "Coding agent open-source nel terminale. Modifica file, fa commit, funziona con qualsiasi LLM. Il favorito della community.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Hugging Face",
        "url": "https://huggingface.co",
        "category": "infrastruttura",
        "tags": ["modelli", "dataset", "open-source", "community"],
        "pricing": "Free / Pro",
        "description_it": "Il 'GitHub dell'AI'. Ospita modelli, dataset, e Spaces (app demo). Dove la community open-source condivide e collabora.",
        "rating": 5,
        "featured": False,
    },
    {
        "name": "LangChain",
        "url": "https://langchain.com",
        "category": "framework",
        "tags": ["framework", "python", "agent", "rag"],
        "pricing": "Open source / LangSmith ($)",
        "description_it": "Framework per costruire applicazioni LLM. Chain, agenti, RAG, memory. Il più usato per app AI production-ready.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "ComfyUI",
        "url": "https://github.com/comfyanonymous/ComfyUI",
        "category": "immagini",
        "tags": ["generazione", "immagini", "workflow", "open-source"],
        "pricing": "Open source",
        "description_it": "UI a nodi per generazione immagini AI. Flusso di lavoro visuale con Stable Diffusion, Flux, e altri modelli. Potente e flessibile.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Perplexity",
        "url": "https://perplexity.ai",
        "category": "ricerca",
        "tags": ["ricerca", "web", "citazioni", "chat"],
        "pricing": "Free / $20/mese Pro",
        "description_it": "Motore di ricerca AI. Cerca il web, sintetizza risposte, cita le fonti. È Google se Google fosse un LLM.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "category": "audio",
        "tags": ["voce", "tts", "clonazione", "audio"],
        "pricing": "Free / $5/mese Starter",
        "description_it": "Sintesi vocale AI ultra-realistica. Clonazione voce, generazione audio in 29 lingue. Lo standard per TTS professionale.",
        "rating": 5,
        "featured": False,
    },
    {
        "name": "Runway",
        "url": "https://runwayml.com",
        "category": "video",
        "tags": ["video", "generazione", "editing", "gen-3"],
        "pricing": "$12/mese Standard",
        "description_it": "Generazione e editing video AI. Gen-3 Alpha produce clip video da testo o immagini. Leader nel video AI.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "v0",
        "url": "https://v0.dev",
        "category": "coding",
        "tags": ["ui", "frontend", "generazione", "react"],
        "pricing": "Free tier",
        "description_it": "Genera interfacce UI da una descrizione testuale. Produce React + Tailwind. Da Vercel — perfetto per prototipi veloci.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "DeepSeek",
        "url": "https://deepseek.com",
        "category": "modello",
        "tags": ["llm", "reasoning", "open-source", "cinese"],
        "pricing": "Open source / API economica",
        "description_it": "Il laboratorio cinese che ha scosso l'industria. DeepSeek-R1: reasoning model open-source a una frazione del costo di GPT-4.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "GitHub Copilot",
        "url": "https://github.com/features/copilot",
        "category": "coding",
        "tags": ["autocomplete", "coding", "ide", "github"],
        "pricing": "$10/mese Individual",
        "description_it": "Autocomplete AI per il codice. Integrazione nativa in VS Code, JetBrains, Neovim. Il coding assistant più diffuso.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Notion AI",
        "url": "https://notion.so/product/ai",
        "category": "produttività",
        "tags": ["scrittura", "note", "database", "workspace"],
        "pricing": "$10/mese add-on",
        "description_it": "AI integrata in Notion. Scrivi, riassumi, traduci, genera contenuti direttamente nelle tue pagine e database.",
        "rating": 3,
        "featured": False,
    },
    {
        "name": "Gamma",
        "url": "https://gamma.app",
        "category": "presentazioni",
        "tags": ["presentazioni", "slides", "design", "generazione"],
        "pricing": "Free / $8/mese Plus",
        "description_it": "Genera presentazioni da un prompt. Scegli lo stile, l'AI crea slide professionali. Alternativa AI a PowerPoint.",
        "rating": 3,
        "featured": False,
    },
    {
        "name": "Lovable",
        "url": "https://lovable.dev",
        "category": "coding",
        "tags": ["full-stack", "app", "generazione", "web"],
        "pricing": "Free tier / $20/mese Pro",
        "description_it": "Crea app web full-stack da una descrizione. Frontend + backend + database. Ex GPT Engineer.",
        "rating": 4,
        "featured": False,
    },
    {
        "name": "Bolt.new",
        "url": "https://bolt.new",
        "category": "coding",
        "tags": ["web", "prototipo", "generazione", "browser"],
        "pricing": "Free tier",
        "description_it": "Crea e deploya app web nel browser. Descrivi cosa vuoi, l'AI scrive il codice e lo esegue live. StackBlitz sotto il cofano.",
        "rating": 4,
        "featured": False,
    },
]


def tool_id(name: str, url: str) -> str:
    """Generate stable ID for a tool."""
    raw = f"{name.lower().strip()}|{url.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ─── Auto-categorization ────────────────────────────

CATEGORY_KEYWORDS = {
    "coding": [
        "code", "coding", "ide", "editor", "developer", "programming", "dev",
        "copilot", "autocomplete", "debug", "git", "github", "deploy",
        "compiler", "linter", "refactor", "api", "sdk", "cli", "terminal",
        "full-stack", "frontend", "backend", "react", "vue", "node",
        "python", "javascript", "typescript", "rust", "golang",
    ],
    "chat": [
        "chat", "chatbot", "conversation", "assistant", "virtual assistant",
        "gpt", "claude", "gemini", "llama", "mistral", "copilot",
        "answer", "question", "ask", "talk",
    ],
    "immagini": [
        "image", "photo", "picture", "art", "design", "illustration",
        "logo", "icon", "graphic", "visual", "generate image", "dall-e",
        "midjourney", "stable diffusion", "flux", "avatar", "background",
        "screenshot", "mockup",
    ],
    "musica": [
        "music", "song", "audio", "sound", "beat", "melody",
        "compose", "instrument", "vocal", "singing", "playlist",
    ],
    "video": [
        "video", "film", "movie", "clip", "animation", "motion",
        "screen", "recording", "stream", "youtube", "tiktok",
        "subtitle", "caption",
    ],
    "audio": [
        "voice", "speech", "tts", "stt", "transcri", "podcast",
        "microphone", "audio", "noise", "vocal", "dubbing", "clone voice",
    ],
    "ricerca": [
        "search", "research", "find", "discover", "explore", "index",
        "summarize", "summary", "analysis", "analyt", "insight", "data",
        "perplexity", "notebook", "document",
    ],
    "agent": [
        "agent", "automat", "workflow", "orchestrat", "bot",
        "integration", "connect", "zapier", "action", "tool use",
    ],
    "produttività": [
        "productivity", "note", "task", "project", "calendar", "email",
        "writing", "document", "spreadsheet", "meeting", "schedule",
        "crm", "erp", "organiz",
    ],
    "presentazioni": [
        "presentation", "slide", "deck", "pitch", "powerpoint",
        "keynote", "visual presentation",
    ],
    "marketing": [
        "marketing", "seo", "content", "social media", "ad",
        "campaign", "brand", "copywrit", "email marketing", "growth",
    ],
    "scrittura": [
        "writing", "write", "essay", "blog", "article", "content generat",
        "copy", "text generat", "story", "novel", "grammar",
    ],
}


def infer_category(name: str, description: str = "") -> tuple:
    """Infer category and tags from tool name and description."""
    text = f"{name} {description}".lower()

    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cat] = score

    if not scores:
        return "altro", []

    # Best category
    best_cat = max(scores, key=scores.get)

    # Tags: which keywords matched
    matched_tags = []
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text and kw not in matched_tags:
                matched_tags.append(kw)
                if len(matched_tags) >= 5:
                    break
        if len(matched_tags) >= 5:
            break

    return best_cat, matched_tags


def infer_pricing(text: str) -> str:
    """Try to infer pricing from description/title."""
    text = text.lower()
    if any(w in text for w in ["free", "gratuito", "open source", "open-source", "oss"]):
        if any(w in text for w in ["premium", "pro", "paid", "plan", "tier"]):
            return "Freemium"
        return "Free"
    if any(w in text for w in ["$", "€", "/month", "/mese", "plan", "pricing"]):
        return "Freemium"
    return "Free tier"


def clean_summary(raw: str) -> str:
    """Strip HTML and clean RSS summary text."""
    import re
    text = re.sub(r"<[^>]+>", "", raw).strip()
    # Remove common RSS artifacts
    text = re.sub(r"\s*\(opens in new (tab|window)\)\s*", "", text, flags=re.I)
    text = re.sub(r"\s*Read more\s*$", "", text, flags=re.I)
    if len(text) > 300:
        text = text[:297] + "..."
    return text


def scan_rss_tools(source: dict) -> list:
    """Scan an RSS feed for tool mentions with auto-categorization."""
    tools = []
    print(f"  📡 Scanning: {source['name']}...", end=" ", flush=True)

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AIHubBot/1.0)"}
        resp = requests.get(source["url"], headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"❌ {e}")
        return tools

    if not feed.entries:
        print("⚠️  no entries")
        return tools

    count = 0
    for entry in feed.entries[:20]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        if not title or not link:
            continue

        # Extract tool name from title
        name = re.sub(r"^(New |Top \d+ )?(AI )?(Tool|App|Platform|Software)[\s:]*", "", title, flags=re.I)
        name = re.sub(r"\s*[-–|].*$", "", name).strip()

        if len(name) < 3 or len(name) > 60:
            continue

        # Get description from RSS
        raw_desc = entry.get("summary", "") or entry.get("description", "")
        description = clean_summary(raw_desc)

        # Auto-categorize
        category, tags = infer_category(name, description)
        pricing = infer_pricing(f"{name} {description}")

        tid = tool_id(name, link)

        tools.append({
            "id": tid,
            "name": name,
            "url": link,
            "source": source["name"],
            "category": category,
            "tags": tags,
            "pricing": pricing,
            "description_it": description,
            "rating": 2,  # Default for discovered tools
            "featured": False,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        })
        count += 1

    print(f"✅ {count} tools found")
    return tools


def main():
    print("🛠️  AI Tools Scanner\n")

    existing_path = DATA_DIR / "tools_db.json"

    # Start with curated tools
    tools = {tool_id(t["name"], t["url"]): t for t in CURATED_TOOLS}
    print(f"  📦 Curated tools: {len(CURATED_TOOLS)}")

    # Scan RSS sources
    for source in TOOL_SOURCES:
        found = scan_rss_tools(source)
        for tool in found:
            if tool["id"] not in tools:
                tools[tool["id"]] = tool

    # Merge with existing if present
    if existing_path.exists():
        with open(existing_path) as f:
            existing = json.load(f)
        for tool in existing.get("tools", []):
            tid = tool.get("id", "")
            if tid and tid not in tools:
                tools[tid] = tool
            elif tid in tools and tools[tid].get("rating", 0) == 0 and tool.get("rating", 0) > 0:
                # Keep existing rating if new one is 0
                tools[tid]["rating"] = tool["rating"]

    # Sort: featured first, then by rating
    sorted_tools = sorted(
        tools.values(),
        key=lambda t: (t.get("featured", False), t.get("rating", 0)),
        reverse=True,
    )

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(sorted_tools),
        "tools": sorted_tools,
    }

    with open(existing_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Results:")
    print(f"   Total tools: {len(sorted_tools)}")
    print(f"   Saved to: {existing_path}")

    # Count by category
    categories = {}
    for t in sorted_tools:
        cat = t.get("category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📂 Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}")


if __name__ == "__main__":
    main()
