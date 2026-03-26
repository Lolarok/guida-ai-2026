#!/usr/bin/env python3
"""
AI News Scraper — Raccoglie notizie AI da feed RSS e pagine web.
Output: data/raw_news.json

Uses ONLY Python builtins — no pip install needed.
"""

import json
import hashlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USER_AGENT = "Mozilla/5.0 (compatible; AIHubBot/1.0; +https://lolarok.github.io/guida-ai)"


# ─── Config ─────────────────────────────────────────

def load_config():
    with open(SCRIPTS_DIR / "config.json") as f:
        return json.load(f)


# ─── Deduplication ──────────────────────────────────

def article_id(title: str, link: str) -> str:
    """Generate a stable ID for deduplication."""
    raw = f"{title.lower().strip()}|{link.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def load_existing_ids() -> set:
    """Load IDs of already-seen articles."""
    curated_path = DATA_DIR / "curated.json"
    if curated_path.exists():
        with open(curated_path) as f:
            data = json.load(f)
            return {a.get("id") for a in data.get("articles", []) if a.get("id")}
    return set()


# ─── Scoring ─────────────────────────────────────────

def is_ai_related(title: str, summary: str, config: dict) -> bool:
    """Check if article is AI-related based on keywords."""
    text = f"{title} {summary}".lower()
    keywords = [k.lower() for k in config.get("ai_keywords", [])]
    return any(kw in text for kw in keywords)


def is_excluded(title: str, summary: str, config: dict) -> bool:
    """Check if article should be excluded."""
    text = f"{title} {summary}".lower()
    exclude = [k.lower() for k in config.get("exclude_keywords", [])]
    return any(kw in text for kw in exclude)


def score_article(article: dict, feed_config: dict, config: dict) -> float:
    """Score an article for ranking."""
    score = 0.0
    scoring = config.get("scoring", {})
    text = f"{article['title']} {article.get('summary', '')}".lower()

    weight = feed_config.get("weight", 1)
    score += weight * scoring.get("source_weight_multiplier", 1.5)

    if article.get("published"):
        try:
            pub = datetime.fromisoformat(article["published"].replace("Z", "+00:00"))
            hours_old = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
            if hours_old < scoring.get("recency_hours", 48):
                score += scoring.get("recency_bonus", 2.0)
        except (ValueError, TypeError):
            pass

    keywords = [k.lower() for k in config.get("ai_keywords", [])]
    matches = sum(1 for kw in keywords if kw in text)
    score += matches * scoring.get("keyword_match_bonus", 1.0)

    return round(score, 2)


# ─── HTML Cleaning ───────────────────────────────────

def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─── RSS/Atom Parsing (pure Python) ─────────────────

def fetch_feed(url: str) -> bytes:
    """Fetch feed content using urllib."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def parse_rss_items(root: ET.Element) -> list:
    """Parse RSS 2.0 <item> elements."""
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        summary = item.findtext("description") or item.findtext("summary") or ""
        pub_date = item.findtext("pubDate") or item.findtext("published") or ""

        # Also check content:encoded
        ns_content = "http://purl.org/rss/1.0/modules/content/"
        content_el = item.find(f"{{{ns_content}}}encoded")
        if content_el is not None and content_el.text:
            summary = content_el.text

        if title and link:
            items.append({
                "title": title,
                "link": link,
                "summary": strip_html(summary),
                "published_raw": pub_date,
            })
    return items


def parse_atom_entries(root: ET.Element) -> list:
    """Parse Atom <entry> elements."""
    ns = "http://www.w3.org/2005/Atom"
    items = []
    entries = root.findall(f"{{{ns}}}entry") or root.findall("entry")

    for entry in entries:
        title = (entry.findtext(f"{{{ns}}}title") or entry.findtext("title") or "").strip()

        # Link can be in <link href="..."/> or <link>text</link>
        link_el = entry.find(f"{{{ns}}}link[@rel='alternate']") or entry.find(f"{{{ns}}}link")
        if link_el is None:
            link_el = entry.find("link")
        link = ""
        if link_el is not None:
            link = link_el.get("href", "") or (link_el.text or "").strip()

        summary = (entry.findtext(f"{{{ns}}}summary") or entry.findtext(f"{{{ns}}}content") or
                   entry.findtext("summary") or entry.findtext("content") or "")
        pub_date = (entry.findtext(f"{{{ns}}}published") or entry.findtext(f"{{{ns}}}updated") or
                    entry.findtext("published") or entry.findtext("updated") or "")

        if title and link:
            items.append({
                "title": title,
                "link": link,
                "summary": strip_html(summary),
                "published_raw": pub_date,
            })
    return items


def parse_date(raw: str) -> str:
    """Try to parse various date formats into ISO 8601."""
    if not raw:
        return ""
    raw = raw.strip()

    # Try ISO format first
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f%z"]:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass

    # Try RFC 2822 (RSS date format)
    # "Wed, 02 Oct 2002 13:00:00 GMT" or with +0000
    raw_clean = re.sub(r"\s*\([^)]+\)\s*$", "", raw)  # Remove (UTC) etc.
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %Z"]:
        try:
            dt = datetime.strptime(raw_clean.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass

    return ""


def detect_feed_type(root: ET.Element) -> str:
    """Detect if the feed is RSS or Atom."""
    tag = root.tag.lower()
    if "feed" in tag:
        return "atom"
    return "rss"


# ─── Feed Parsing ────────────────────────────────────

def parse_feed(feed_config: dict, config: dict, existing_ids: set) -> list:
    """Parse a single RSS/Atom feed and return new articles."""
    articles = []
    url = feed_config["url"]
    name = feed_config["name"]

    print(f"  📡 Fetching: {name}...", end=" ", flush=True)

    try:
        content = fetch_feed(url)
        root = ET.fromstring(content)
    except Exception as e:
        print(f"❌ {e}")
        return articles

    feed_type = detect_feed_type(root)

    if feed_type == "atom":
        raw_items = parse_atom_entries(root)
    else:
        # For RSS, find the channel element
        channel = root.find("channel")
        if channel is None:
            channel = root  # Some feeds have items at root level
        raw_items = parse_rss_items(channel)

    if not raw_items:
        print("⚠️  no entries")
        return articles

    count = 0
    for item in raw_items[:30]:  # Max 30 per feed
        title = item["title"]
        link = item["link"]

        aid = article_id(title, link)
        if aid in existing_ids:
            continue

        summary = item["summary"]
        if len(summary) > 500:
            summary = summary[:497] + "..."

        if is_excluded(title, summary, config):
            continue

        if not is_ai_related(title, summary, config):
            continue

        published = parse_date(item["published_raw"])

        article = {
            "id": aid,
            "title": title,
            "link": link,
            "summary": summary,
            "source": name,
            "source_url": url,
            "published": published,
            "category": feed_config.get("category", "news"),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

        article["score"] = score_article(article, feed_config, config)
        articles.append(article)
        existing_ids.add(aid)
        count += 1

    print(f"✅ {count} new articles")
    return articles


# ─── Main ────────────────────────────────────────────

def main():
    print("🔍 AI News Scraper — Collecting articles\n")

    config = load_config()
    existing_ids = load_existing_ids()
    all_articles = []

    for feed in config["feeds"]:
        articles = parse_feed(feed, config, existing_ids)
        all_articles.extend(articles)

    # Sort by score
    all_articles.sort(key=lambda a: a["score"], reverse=True)

    # Save raw data
    output = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_articles),
        "articles": all_articles,
    }

    raw_path = DATA_DIR / "raw_news.json"
    with open(raw_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Results:")
    print(f"   Total collected: {len(all_articles)}")
    print(f"   Saved to: {raw_path}")

    # Show top 5
    if all_articles:
        print(f"\n🏆 Top 5 by score:")
        for a in all_articles[:5]:
            print(f"   [{a['score']:.1f}] {a['title'][:60]}")
            print(f"          {a['source']} — {a['link'][:70]}")

    return all_articles


if __name__ == "__main__":
    main()
