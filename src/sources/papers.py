"""Papers de recherche les plus suivis, via l'API "daily papers" de Hugging Face."""

from __future__ import annotations

from datetime import datetime

URL = "https://huggingface.co/api/daily_papers"
NOMBRE = 8


def analyser(donnees: list[dict], depuis: datetime) -> list[dict]:
    papers = []
    for element in donnees:
        paper = element.get("paper") or element
        identifiant = paper.get("id")
        titre = (paper.get("title") or element.get("title") or "").strip()
        date = (paper.get("submittedOnDailyAt") or paper.get("publishedAt") or "")[:10]
        if not identifiant or not titre or not date or date < depuis.date().isoformat():
            continue
        detail = ""
        if paper.get("githubRepo"):
            detail = "code disponible"
        papers.append({
            "categorie": "papers",
            "source": "Hugging Face Papers",
            "titre": " ".join(titre.split()),
            "url": f"https://huggingface.co/papers/{identifiant}",
            "publie_le": date,
            "score": int(paper.get("upvotes") or 0),
            "detail": detail,
            "lien_discussion": f"https://arxiv.org/abs/{identifiant}",
            "image": element.get("thumbnail") or "",
        })
    papers.sort(key=lambda p: p["score"], reverse=True)
    return papers[:NOMBRE]


def collecter(session, depuis: datetime) -> list[dict]:
    reponse = session.get(URL, timeout=60)
    reponse.raise_for_status()
    papers = analyser(reponse.json(), depuis)
    print(f"  Hugging Face Papers : {len(papers)} papers")
    return papers
