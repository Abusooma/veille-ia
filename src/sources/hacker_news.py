"""Discussions IA les plus commentées sur Hacker News, via l'API Algolia."""

from __future__ import annotations

import re
from datetime import datetime

URL = "https://hn.algolia.com/api/v1/search_by_date"
POINTS_MIN = 100
NOMBRE = 8

# Mots-clés IA, sans tenir compte de la casse.
MOTS_IA = re.compile(
    r"\b(LLMs?|GPT[-\w]*|ChatGPT|Claude|Gemini|Llama|Mistral|DeepSeek|Qwen|OpenAI|Anthropic|DeepMind|"
    r"Hugging ?Face|machine learning|deep learning|neural networks?|transformers?|agentic|RAG|"
    r"fine-?tun\w*|diffusion models?|embeddings?|prompt\w*|chatbots?|copilot|vibe cod\w*)\b",
    re.IGNORECASE,
)
# "AI" en majuscules seulement : "ai" en minuscules apparaît dans d'autres contextes.
AI_MAJUSCULES = re.compile(r"\bA\.?I\b")


def est_ia(titre: str) -> bool:
    return bool(AI_MAJUSCULES.search(titre) or MOTS_IA.search(titre))


def analyser(donnees: dict) -> list[dict]:
    discussions = []
    for hit in donnees.get("hits", []):
        titre = (hit.get("title") or "").strip()
        if not titre or not est_ia(titre):
            continue
        identifiant = hit.get("objectID")
        lien_hn = f"https://news.ycombinator.com/item?id={identifiant}"
        discussions.append({
            "categorie": "discussions",
            "source": "Hacker News",
            "titre": titre,
            "url": hit.get("url") or lien_hn,
            "publie_le": (hit.get("created_at") or "")[:10],
            "score": int(hit.get("points") or 0),
            "detail": f"{int(hit.get('num_comments') or 0)} commentaires",
            "lien_discussion": lien_hn,
        })
    discussions.sort(key=lambda d: d["score"], reverse=True)
    return discussions[:NOMBRE]


def collecter(session, depuis: datetime) -> list[dict]:
    reponse = session.get(
        URL,
        params={
            "tags": "story",
            "numericFilters": f"created_at_i>{int(depuis.timestamp())},points>{POINTS_MIN}",
            "hitsPerPage": 500,
        },
        timeout=60,
    )
    reponse.raise_for_status()
    discussions = analyser(reponse.json())
    print(f"  Hacker News : {len(discussions)} discussions")
    return discussions
