"""Mise en forme d'une édition de la veille (README et archive)."""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path

MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
               "juil.", "août", "sept.", "oct.", "nov.", "déc."]

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

# Auteur de la veille, affiché dans l'en-tête.
AUTEUR = "Aboubacar"
AUTEUR_LIEN = "https://github.com/Abusooma"
AUTEUR_TITRES = ["AI Product Builder", "Computer Science Engineering Graduate", "Formateur"]

# (catégorie, ancre, titre, phrase d'introduction)
SECTIONS = [
    ("articles", "a-lire", "À lire", "Les dernières publications des labos et des blogs spécialisés."),
    ("francais", "en-francais", "En français", "L'actualité de l'IA dans la presse spécialisée francophone."),
    ("papers", "papers", "Papers du moment", "Les papers de recherche les plus votés par la communauté Hugging Face."),
    ("discussions", "discussions", "Discussions", "Les sujets IA qui font réagir sur Hacker News."),
    ("repos", "repos", "Repos à suivre", "Des repos IA récents qui gagnent vite des étoiles sur GitHub."),
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


def date_courte(iso: str) -> str:
    """'2026-11-20' -> '20 nov. 2026'."""
    annee, mois, jour = (int(x) for x in iso.split("-"))
    return f"{'1er' if jour == 1 else jour} {MOIS_COURTS[mois - 1]} {annee}"


def _propre(texte: str) -> str:
    return texte.replace("|", "/").replace("[", "(").replace("]", ")")


def _ligne(e: dict) -> str:
    titre = f"[{_propre(e['titre'])}]({e['url']})"
    if e["categorie"] in ("articles", "francais"):
        return f"| {titre} | {e['source']} | {date_courte(e['publie_le'])} |"
    if e["categorie"] == "papers":
        extra = f" · {e['detail']}" if e["detail"] else ""
        return f"| {titre} | {e['score']} votes{extra} | [arXiv]({e['lien_discussion']}) |"
    if e["categorie"] == "discussions":
        return f"| {titre} | {e['score']} points | [{e['detail']}]({e['lien_discussion']}) |"
    return f"| {titre} | {e['score']} étoiles | {_propre(e['detail']) or '-'} |"


ENTETES = {
    "articles": ["| Article | Source | Date |", "|---|---|---|"],
    "francais": ["| Article | Source | Date |", "|---|---|---|"],
    "papers": ["| Paper | Votes | Lien |", "|---|---|---|"],
    "discussions": ["| Sujet | Points | Discussion |", "|---|---|---|"],
    "repos": ["| Repo | Étoiles | Description |", "|---|---|---|"],
}


LABOS = ["Google DeepMind", "OpenAI", "Google Research", "Hugging Face"]


def essentiel(elements: list[dict]) -> list[str]:
    """Cinq liens pour le lecteur pressé, avec une vignette quand la source en fournit une.

    Les images sont affichées depuis le site d'origine, jamais copiées dans le dépôt.
    """
    def premier(categorie, cle):
        choix = [e for e in elements if e["categorie"] == categorie]
        return max(choix, key=cle) if choix else None

    annonces = [e for e in elements if e["categorie"] == "articles" and e["source"] in LABOS]
    annonce = max(
        annonces, key=lambda e: (e["publie_le"], bool(e.get("image")), -LABOS.index(e["source"]))
    ) if annonces else None
    choix = [
        ("Discussion", premier("discussions", lambda e: int(e["score"])), lambda e: f"{e['score']} points sur Hacker News"),
        ("Paper", premier("papers", lambda e: int(e["score"])), lambda e: f"{e['score']} votes sur Hugging Face"),
        ("Repo", premier("repos", lambda e: int(e["score"])), lambda e: f"{e['score']} étoiles sur GitHub"),
        ("Annonce", annonce, lambda e: e["source"]),
        ("En français", premier("francais", lambda e: (e["publie_le"], bool(e.get("image")))), lambda e: e["source"]),
    ]
    lignes = []
    for nom, e, info in choix:
        if not e:
            continue
        url = escape(e["url"])
        texte = (
            f'<sub>{escape(nom.upper())}</sub><br>'
            f'<b><a href="{url}">{escape(e["titre"])}</a></b><br>'
            f"<sub>{escape(info(e))}</sub>"
        )
        if e.get("image"):
            cellules = [
                f'<td width="176" valign="top"><a href="{url}"><img src="{escape(e["image"])}" width="160" alt=""></a></td>',
                f'<td valign="top">{texte}</td>',
            ]
        else:  # pas d'image : le texte prend toute la largeur
            cellules = [f'<td colspan="2" valign="top">{texte}</td>']
        lignes += ["<tr>", *cellules, "</tr>"]
    if not lignes:
        return []
    return ['<a name="essentiel"></a>', "", "## L'essentiel", "", "<table>", *lignes, "</table>", ""]


def sommaire(elements: list[dict]) -> str:
    liens = ["[L'essentiel](#essentiel)"] if elements else []
    for categorie, ancre, titre, _ in SECTIONS:
        if any(e["categorie"] == categorie for e in elements):
            liens.append(f"[{titre}](#{ancre})")
    return " · ".join(liens)


def sommaire_html(elements: list[dict]) -> str:
    liens = ['<a href="#essentiel">L\'essentiel</a>'] if elements else []
    for categorie, ancre, titre, _ in SECTIONS:
        if any(e["categorie"] == categorie for e in elements):
            liens.append(f'<a href="#{ancre}">{escape(titre)}</a>')
    return " · ".join(liens)


def corps_edition(elements: list[dict]) -> list[str]:
    lignes = essentiel(elements)
    for categorie, ancre, titre, intro in SECTIONS:
        choisis = [e for e in elements if e["categorie"] == categorie]
        if not choisis:
            continue
        lignes += [f'<a name="{ancre}"></a>', "", f"## {titre}", "", intro, "",
                   *ENTETES[categorie], *map(_ligne, choisis), ""]
    if not lignes:
        lignes = ["Rien de nouveau depuis la dernière édition.", ""]
    return lignes


def _resume(elements: list[dict]) -> str:
    compte = lambda *cats: len([e for e in elements if e["categorie"] in cats])  # noqa: E731
    return " · ".join([
        f"{compte('articles', 'francais')} articles", f"{compte('papers')} papers",
        f"{compte('discussions')} discussions", f"{compte('repos')} repos",
    ])


def edition(elements: list[dict], jour: str) -> str:
    """Fichier d'archive editions/AAAA-MM-JJ.md."""
    return "\n".join([
        f"# Veille IA du {date_fr(jour)}",
        "",
        f"**{_resume(elements)}**",
        "",
        sommaire(elements),
        "",
        *corps_edition(elements),
        "[Retour à la dernière édition](../README.md)",
        "",
    ])


def _chiffres(elements: list[dict]) -> list[str]:
    """Quatre chiffres de l'édition, côte à côte."""
    compte = lambda *cats: len([e for e in elements if e["categorie"] in cats])  # noqa: E731
    cases = [
        (compte("articles", "francais"), "articles"),
        (compte("papers"), "papers"),
        (compte("discussions"), "discussions"),
        (compte("repos"), "repos"),
    ]
    cellules = [f'<td align="center" width="140"><h3>{n}</h3><sub>{libelle}</sub></td>' for n, libelle in cases]
    return ["<table>", "<tr>", *cellules, "</tr>", "</table>"]


def entete(elements: list[dict], jour: str, racine: Path) -> list[str]:
    lignes = ['<div align="center">', ""]
    if (racine / IMAGE).exists():
        lignes += [f'<img src="{IMAGE}" width="100%" alt="Veille IA">', ""]
    lignes += [
        "<h1>Veille IA</h1>",
        "",
        "<p><b>Les lectures IA à ne pas manquer, réunies tous les deux jours.</b></p>",
        "",
        "<p>Annonces des labos · Papers de recherche · Discussions · Repos GitHub · Actualité en français</p>",
        "",
        f"<p><sub>ÉDITION DU {date_fr(jour).upper()}</sub></p>",
        "",
        *_chiffres(elements),
        "",
        f'<p><sub>Sélection préparée par <a href="{AUTEUR_LIEN}"><b>{escape(AUTEUR)}</b></a><br>'
        f'{" · ".join(escape(t) for t in AUTEUR_TITRES)}</sub></p>',
        "",
        "</div>",
        "",
        "---",
        "",
        f'<p align="center">{sommaire_html(elements)}</p>',
        "",
    ]
    return lignes


def readme(elements: list[dict], jour: str, archives: list[str], racine: Path) -> str:
    lignes = [*entete(elements, jour, racine), *corps_edition(elements)]
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
