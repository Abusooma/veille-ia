"""Articles des blogs des labos et des médias spécialisés, via leurs flux RSS ou Atom."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import feedparser

# "exclure_titre" et "exclure_url" écartent ce qui n'apporte rien au lecteur
# (témoignages clients, démos commerciales, citations, notes de version).
FLUX = [
    {"source": "OpenAI", "url": "https://openai.com/news/rss.xml",
     "exclure_url": r"/customer-stories/|/business/"},
    {"source": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"source": "Google Research", "url": "https://research.google/blog/rss/"},
    {"source": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml"},
    {"source": "Simon Willison", "url": "https://simonwillison.net/atom/everything/",
     "exclure_titre": r"^Quoting |^[\w.-]+ \d+(\.\d+)+\b"},
    {"source": "ActuIA", "url": "https://www.actuia.com/feed/", "francais": True},
]

MAX_PAR_SOURCE = 3


def _date(entree) -> datetime | None:
    for champ in ("published_parsed", "updated_parsed"):
        valeur = entree.get(champ)
        if valeur:
            return datetime(*valeur[:6], tzinfo=timezone.utc)
    return None


def analyser(contenu: bytes | str, config: dict, depuis: datetime) -> list[dict]:
    flux = feedparser.parse(contenu)
    exclure_titre = re.compile(config["exclure_titre"]) if config.get("exclure_titre") else None
    exclure_url = re.compile(config["exclure_url"]) if config.get("exclure_url") else None
    articles = []
    for entree in flux.entries:
        date = _date(entree)
        titre = (entree.get("title") or "").strip()
        lien = (entree.get("link") or "").strip()
        if not titre or not lien or not date or date < depuis:
            continue
        if (exclure_titre and exclure_titre.search(titre)) or (exclure_url and exclure_url.search(lien)):
            continue
        articles.append({
            "categorie": "francais" if config.get("francais") else "articles",
            "source": config["source"],
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
            trouves = analyser(reponse.content, flux, depuis)
            print(f"  {flux['source']} : {len(trouves)} articles")
            articles.extend(trouves)
        except Exception as erreur:  # un blog en panne ne bloque pas les autres
            print(f"  {flux['source']} : échec ({erreur})")
        time.sleep(1)
    return articles
