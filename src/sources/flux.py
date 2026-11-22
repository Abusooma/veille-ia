"""Articles des blogs des labos et des médias spécialisés, via leurs flux RSS ou Atom."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import feedparser

FLUX = [
    {"source": "OpenAI", "url": "https://openai.com/news/rss.xml"},
    {"source": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"source": "Google Research", "url": "https://research.google/blog/rss/"},
    {"source": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"source": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
    {"source": "ActuIA (FR)", "url": "https://www.actuia.com/feed/"},
]

MAX_PAR_SOURCE = 5


def _date(entree) -> datetime | None:
    for champ in ("published_parsed", "updated_parsed"):
        valeur = entree.get(champ)
        if valeur:
            return datetime(*valeur[:6], tzinfo=timezone.utc)
    return None


def analyser(contenu: bytes | str, source: str, depuis: datetime) -> list[dict]:
    flux = feedparser.parse(contenu)
    articles = []
    for entree in flux.entries:
        date = _date(entree)
        titre = (entree.get("title") or "").strip()
        lien = (entree.get("link") or "").strip()
        if not titre or not lien or not date or date < depuis:
            continue
        articles.append({
            "categorie": "articles",
            "source": source,
            "titre": titre,
            "url": lien,
            "publie_le": date.date().isoformat(),
            "score": 0,
            "detail": "",
            "lien_discussion": "",
        })
    articles.sort(key=lambda a: a["publie_le"], reverse=True)
    return articles[:MAX_PAR_SOURCE]


def collecter(session, depuis: datetime) -> list[dict]:
    articles = []
    for flux in FLUX:
        try:
            reponse = session.get(flux["url"], timeout=60)
            reponse.raise_for_status()
            trouves = analyser(reponse.content, flux["source"], depuis)
            print(f"  {flux['source']} : {len(trouves)} articles")
            articles.extend(trouves)
        except Exception as erreur:  # un blog en panne ne bloque pas les autres
            print(f"  {flux['source']} : échec ({erreur})")
        time.sleep(1)
    return articles
