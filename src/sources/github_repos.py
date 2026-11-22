"""Repos IA récents qui prennent des étoiles, via l'API de recherche de GitHub."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

URL = "https://api.github.com/search/repositories"
SUJETS = ["llm", "ai-agents", "generative-ai", "rag", "machine-learning"]
FENETRE_JOURS = 14     # repos créés dans les 14 derniers jours
ETOILES_MIN = 50
NOMBRE = 8


def analyser(donnees: dict) -> list[dict]:
    repos = []
    for repo in donnees.get("items", []):
        description = " ".join((repo.get("description") or "").split())
        if len(description) > 90:
            description = description[:87].rsplit(" ", 1)[0] + "..."
        repos.append({
            "categorie": "repos",
            "source": "GitHub",
            "titre": repo["full_name"],
            "url": repo["html_url"],
            "publie_le": (repo.get("created_at") or "")[:10],
            "score": int(repo.get("stargazers_count") or 0),
            "detail": " · ".join(x for x in [repo.get("language") or "", description] if x),
            "lien_discussion": "",
        })
    return repos


def collecter(session, depuis: datetime) -> list[dict]:
    debut = (depuis - timedelta(days=FENETRE_JOURS)).date().isoformat()
    entetes = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        entetes["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"

    par_nom = {}
    for sujet in SUJETS:
        reponse = session.get(
            URL,
            params={"q": f"topic:{sujet} created:>{debut} stars:>{ETOILES_MIN}", "sort": "stars", "order": "desc", "per_page": 10},
            headers=entetes,
            timeout=60,
        )
        reponse.raise_for_status()
        for repo in analyser(reponse.json()):
            par_nom[repo["titre"]] = repo
        time.sleep(2)
    repos = sorted(par_nom.values(), key=lambda r: r["score"], reverse=True)[:NOMBRE]
    print(f"  GitHub : {len(repos)} repos")
    return repos
