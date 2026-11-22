"""Édition de la veille IA : collecte, tri des nouveautés, README et archive.

Usage :  python src/veille.py
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import page  # noqa: E402
from sources import USER_AGENT, flux, github_repos, hacker_news, papers  # noqa: E402

SOURCES = {
    "Blogs et médias": flux.collecter,
    "Hugging Face Papers": papers.collecter,
    "Hacker News": hacker_news.collecter,
    "GitHub": github_repos.collecter,
}

RACINE = Path(__file__).resolve().parent.parent
FICHIER_HISTORIQUE = RACINE / "data" / "historique.csv"
DOSSIER_EDITIONS = RACINE / "editions"
FICHIER_README = RACINE / "README.md"
FICHIER_MESSAGE = RACINE / ".commit_msg"

COLONNES = ["edition", "categorie", "source", "titre", "url", "publie_le", "score", "detail", "lien_discussion"]

# On remonte jusqu'à 4 jours en arrière : couvre l'intervalle de 2 jours avec une marge,
# les doublons étant écartés grâce à l'historique.
FENETRE_JOURS = 4


def lire_historique() -> list[dict]:
    if not FICHIER_HISTORIQUE.exists():
        return []
    with FICHIER_HISTORIQUE.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def nouveautes(collectes: list[dict], historique: list[dict]) -> list[dict]:
    """Retire ce qui a déjà paru dans une édition précédente et les doublons du jour."""
    deja_vus = {h["url"] for h in historique}
    resultat, vus = [], set()
    for element in collectes:
        if element["url"] in deja_vus or element["url"] in vus:
            continue
        vus.add(element["url"])
        resultat.append(element)
    return resultat


def ecrire_historique(historique: list[dict], elements: list[dict], jour: str) -> None:
    lignes = [h for h in historique if h["edition"] != jour] + [{**e, "edition": jour} for e in elements]
    FICHIER_HISTORIQUE.parent.mkdir(exist_ok=True)
    with FICHIER_HISTORIQUE.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES, extrasaction="ignore")
        ecrivain.writeheader()
        ecrivain.writerows(lignes)


def message_commit(jour: str, elements: list[dict]) -> str:
    compte = lambda *cats: len([e for e in elements if e["categorie"] in cats])  # noqa: E731
    return (
        f"veille: édition du {jour} ({compte('articles', 'francais')} articles, {compte('papers')} papers, "
        f"{compte('discussions')} discussions, {compte('repos')} repos)"
    )


def main() -> int:
    jour = date.today().isoformat()
    depuis = datetime.now(timezone.utc) - timedelta(days=FENETRE_JOURS)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    collectes, echecs = [], []
    for nom, collecter in SOURCES.items():
        print(f"{nom} :")
        try:
            collectes.extend(collecter(session, depuis))
        except Exception as erreur:  # une source en panne ne bloque pas les autres
            print(f"  échec ({erreur})", file=sys.stderr)
            echecs.append(nom)

    if len(echecs) == len(SOURCES):
        print("Toutes les sources ont échoué, rien n'est modifié.", file=sys.stderr)
        return 1

    historique = lire_historique()
    elements = nouveautes(collectes, [h for h in historique if h["edition"] != jour])

    ecrire_historique(historique, elements, jour)
    DOSSIER_EDITIONS.mkdir(exist_ok=True)
    (DOSSIER_EDITIONS / f"{jour}.md").write_text(page.edition(elements, jour), encoding="utf-8")
    archives = [f.stem for f in DOSSIER_EDITIONS.glob("*.md")]
    FICHIER_README.write_text(page.readme(elements, jour, archives, RACINE), encoding="utf-8")

    message = message_commit(jour, elements)
    FICHIER_MESSAGE.write_text(message, encoding="utf-8")
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
