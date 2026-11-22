"""Mise en forme d'une édition de la veille (README et archive)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

SECTIONS = [
    ("articles", "À lire", "Les dernières publications des labos et des blogs spécialisés."),
    ("papers", "Papers du moment", "Les papers de recherche les plus votés par la communauté Hugging Face."),
    ("discussions", "Discussions", "Les sujets IA qui font réagir sur Hacker News."),
    ("repos", "Repos à suivre", "Des repos IA récents qui gagnent vite des étoiles sur GitHub."),
]

SOURCES_SUIVIES = [
    ("OpenAI", "https://openai.com/news/"),
    ("Google DeepMind", "https://deepmind.google/blog/"),
    ("Google Research", "https://research.google/blog/"),
    ("Hugging Face", "https://huggingface.co/blog"),
    ("Simon Willison", "https://simonwillison.net/"),
    ("ActuIA", "https://www.actuia.com/"),
    ("Hugging Face Papers", "https://huggingface.co/papers"),
    ("Hacker News", "https://news.ycombinator.com/"),
    ("GitHub", "https://github.com/topics/llm"),
]

IMAGE = "assets/banniere.png"


def date_fr(iso: str) -> str:
    annee, mois, jour = (int(x) for x in iso.split("-"))
    return f"{'1er' if jour == 1 else jour} {MOIS[mois - 1]} {annee}"


def _propre(texte: str) -> str:
    return texte.replace("|", "/").replace("[", "(").replace("]", ")")


def _ligne(e: dict) -> str:
    titre = f"[{_propre(e['titre'])}]({e['url']})"
    if e["categorie"] == "articles":
        return f"| {titre} | {e['source']} | {date_fr(e['publie_le'])} |"
    if e["categorie"] == "papers":
        extra = f" · {e['detail']}" if e["detail"] else ""
        return f"| {titre} | {e['score']} votes{extra} | [arXiv]({e['lien_discussion']}) |"
    if e["categorie"] == "discussions":
        return f"| {titre} | {e['score']} points | [{e['detail']}]({e['lien_discussion']}) |"
    return f"| {titre} | {e['score']} étoiles | {_propre(e['detail']) or '-'} |"


ENTETES = {
    "articles": ["| Article | Source | Date |", "|---|---|---|"],
    "papers": ["| Paper | Votes | Lien |", "|---|---|---|"],
    "discussions": ["| Sujet | Points | Discussion |", "|---|---|---|"],
    "repos": ["| Repo | Étoiles | Description |", "|---|---|---|"],
}


def corps_edition(elements: list[dict]) -> list[str]:
    lignes = []
    for categorie, titre, intro in SECTIONS:
        choisis = [e for e in elements if e["categorie"] == categorie]
        if not choisis:
            continue
        lignes += [f"## {titre}", "", intro, "", *ENTETES[categorie], *map(_ligne, choisis), ""]
    if not lignes:
        lignes = ["Rien de nouveau depuis la dernière édition.", ""]
    return lignes


def _resume(elements: list[dict]) -> str:
    compte = {c: len([e for e in elements if e["categorie"] == c]) for c, _, _ in SECTIONS}
    morceaux = [
        f"{compte['articles']} articles", f"{compte['papers']} papers",
        f"{compte['discussions']} discussions", f"{compte['repos']} repos",
    ]
    return " · ".join(morceaux)


def edition(elements: list[dict], jour: str) -> str:
    """Fichier d'archive editions/AAAA-MM-JJ.md."""
    return "\n".join([
        f"# Veille IA du {date_fr(jour)}",
        "",
        f"**{_resume(elements)}**",
        "",
        *corps_edition(elements),
        "[Retour à la dernière édition](../README.md)",
        "",
    ])


def readme(elements: list[dict], jour: str, archives: list[str], racine: Path) -> str:
    lignes = []
    if (racine / IMAGE).exists():
        lignes += [f'<img src="{IMAGE}" width="100%" alt="Veille IA">', ""]
    lignes += [
        "# Veille IA",
        "",
        "Une sélection de lectures sur l'intelligence artificielle, mise à jour tous les deux jours : "
        "les publications des labos, les papers de recherche les plus suivis, les discussions du moment "
        "et les repos qui montent.",
        "",
        f"**Édition du {date_fr(jour)}** · {_resume(elements)}",
        "",
        *corps_edition(elements),
    ]
    precedentes = [a for a in sorted(archives, reverse=True) if a != jour][:15]
    if precedentes:
        lignes += ["## Éditions précédentes", ""]
        lignes += [f"- [{date_fr(a)}](editions/{a}.md)" for a in precedentes]
        lignes.append("")
    lignes += [
        "<details>",
        "<summary>Sources suivies</summary>",
        "",
        *[f"- [{nom}]({url})" for nom, url in SOURCES_SUIVIES],
        "",
        "</details>",
        "",
        "---",
        "",
        "<sub>Chaque lien renvoie vers la publication d'origine. Cette page reprend uniquement les titres, "
        "les dates et les indicateurs publics (votes, points, étoiles). "
        "Fonctionnement du projet : [TECHNIQUE.md](TECHNIQUE.md).</sub>",
        "",
    ]
    return "\n".join(lignes)
