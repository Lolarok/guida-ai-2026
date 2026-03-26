#!/usr/bin/env python3
"""
Translator — Traduce titoli e riassunti EN→IT.
Legge raw_news.json, produce curated.json con traduzioni.
"""

import json
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    os.system(f"{sys.executable} -m pip install deep-translator --break-system-packages -q")
    from deep_translator import GoogleTranslator

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def translate_batch(texts: list, batch_size: int = 10) -> list:
    """Translate a list of texts from EN to IT using Google Translate."""
    translator = GoogleTranslator(source="en", target="it")
    results = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        batch_results = []

        for text in batch:
            if not text or len(text.strip()) < 5:
                batch_results.append(text)
                continue

            try:
                # Google Translate has a 5000 char limit
                if len(text) > 4500:
                    text = text[:4500] + "..."
                translated = translator.translate(text)
                batch_results.append(translated if translated else text)
            except Exception as e:
                print(f"    ⚠️  Translation error: {e}")
                batch_results.append(text)

            time.sleep(0.15)  # Rate limit courtesy

        results.extend(batch_results)
        progress = min(i + batch_size, total)
        print(f"    Translated: {progress}/{total}", end="\r", flush=True)

    print()
    return results


def main():
    print("🌐 Translator EN→IT\n")

    raw_path = DATA_DIR / "raw_news.json"
    if not raw_path.exists():
        print("❌ No raw_news.json found. Run news_scraper.py first.")
        sys.exit(1)

    with open(raw_path) as f:
        data = json.load(f)

    articles = data.get("articles", [])
    print(f"  📰 Articles to translate: {len(articles)}")

    # Filter articles that need translation
    to_translate = [a for a in articles if not a.get("title_it") and not a.get("summary_it")]
    if not to_translate:
        print("  ✅ All articles already translated")
        return

    print(f"  🔄 Translating: {len(to_translate)} new articles\n")

    # Translate titles
    print("  📝 Translating titles...")
    titles = [a.get("title", "") for a in to_translate]
    titles_it = translate_batch(titles, batch_size=15)

    # Translate summaries
    print("  📝 Translating summaries...")
    summaries = [a.get("summary", "") for a in to_translate]
    summaries_it = translate_batch(summaries, batch_size=10)

    # Apply translations
    t_idx = 0
    for article in articles:
        if not article.get("title_it") and not article.get("summary_it") and t_idx < len(to_translate):
            article["title_it"] = titles_it[t_idx]
            article["summary_it"] = summaries_it[t_idx]
            article["translated_at"] = datetime.now(timezone.utc).isoformat()
            t_idx += 1

    # Also translate guides if present
    guide_path = DATA_DIR / "daily_guide.json"
    if guide_path.exists():
        with open(guide_path) as f:
            guide = json.load(f)
        if not guide.get("title_it"):
            print(f"\n  📖 Translating guide title: {guide['title']}")
            try:
                translator = GoogleTranslator(source="en", target="it")
                # Guide title is already in Italian for most entries
                guide["title_it"] = guide["title"]  # Already Italian
            except Exception as e:
                print(f"    ⚠️  {e}")
            with open(guide_path, "w") as f:
                json.dump(guide, f, indent=2, ensure_ascii=False)

    # Save curated.json
    output = {
        "translated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(articles),
        "translated": t_idx,
        "articles": articles,
    }

    curated_path = DATA_DIR / "curated.json"
    with open(curated_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done!")
    print(f"   Translated: {t_idx} articles")
    print(f"   Saved to: {curated_path}")

    # Show sample
    if to_translate:
        sample = to_translate[0]
        idx = articles.index(sample)
        print(f"\n📝 Sample translation:")
        print(f"   EN: {sample.get('title', '')[:70]}")
        print(f"   IT: {articles[idx].get('title_it', '')[:70]}")


if __name__ == "__main__":
    main()
