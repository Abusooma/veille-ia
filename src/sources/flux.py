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


_IMG = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


def image(entree) -> str:
    """Image d'illustration fournie par le flux, s'il y en a une."""
    for champ in ("media_content", "media_thumbnail"):
        for media in entree.get(champ) or []:
            url = media.get("url", "")
            if url and media.get("medium", "image") == "image":
                return url
    for lien in entree.get("links") or []:
        if lien.get("rel") == "enclosure" and str(lien.get("type", "")).startswith("image/"):
            return lien.get("href", "")
    trouve = _IMG.search(entree.get("summary") or "")
    return trouve.group(1) if trouve else ""


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
            "image": image(entree),
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
