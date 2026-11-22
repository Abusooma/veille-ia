import json
from datetime import datetime, timezone
from pathlib import Path

import page
import veille
from sources import flux, github_repos, hacker_news, papers

FIXTURES = Path(__file__).parent / "fixtures"
DEPUIS = datetime(2026, 11, 18, tzinfo=timezone.utc)


def _json(nom):
    return json.loads((FIXTURES / nom).read_text(encoding="utf-8"))


# ------------------------------------------------------------------- Flux

def test_rss_garde_les_articles_recents():
    articles = flux.analyser((FIXTURES / "rss.xml").read_bytes(), "Blog", DEPUIS)
    assert [a["url"] for a in articles] == ["https://exemple.org/nouveau-modele", "https://exemple.org/client"]
    assert articles[0]["publie_le"] == "2026-11-20"
    assert articles[0]["categorie"] == "articles"


def test_atom():
    articles = flux.analyser((FIXTURES / "atom.xml").read_bytes(), "Weblog", DEPUIS)
    assert len(articles) == 1
    assert articles[0]["url"] == "https://blog.exemple.org/2026/Nov/20/llm-local/"


# ----------------------------------------------------------------- Papers

def test_papers_tries_par_votes_et_recents():
    resultat = papers.analyser(_json("daily_papers.json"), DEPUIS)
    assert [p["score"] for p in resultat] == [7, 2]  # le paper d'octobre est écarté
    assert resultat[0]["titre"] == "Teaching Vision-Language-Action Models to Stop Safely"
    assert resultat[0]["url"] == "https://huggingface.co/papers/2611.26239"
    assert resultat[0]["detail"] == "code disponible"


# ------------------------------------------------------------ Hacker News

def test_hacker_news_garde_seulement_l_ia():
    resultat = hacker_news.analyser(_json("hn.json"))
    assert [d["score"] for d in resultat] == [312, 150]
    assert resultat[1]["url"] == "https://news.ycombinator.com/item?id=48000003"  # Ask HN sans lien externe
    assert resultat[0]["detail"] == "140 commentaires"


def test_filtre_ia():
    assert hacker_news.est_ia("Fine-tuning Llama on a laptop")
    assert hacker_news.est_ia("Why AI agents fail")
    assert not hacker_news.est_ia("Kaizen and the ai of zen")
    assert not hacker_news.est_ia("A car model review")


# ----------------------------------------------------------------- GitHub

def test_repos():
    resultat = github_repos.analyser(_json("github.json"))
    assert resultat[0]["titre"] == "exemple/agent-kit"
    assert resultat[0]["detail"] == "Python · A lightweight framework to build AI agents with tools and memory"
    assert resultat[1]["detail"] == ""


# ------------------------------------------------------------- Édition

def _tout():
    return (
        flux.analyser((FIXTURES / "rss.xml").read_bytes(), "Blog", DEPUIS)
        + papers.analyser(_json("daily_papers.json"), DEPUIS)
        + hacker_news.analyser(_json("hn.json"))
        + github_repos.analyser(_json("github.json"))
    )


def test_nouveautes_ecarte_le_deja_vu():
    elements = _tout()
    historique = [{"url": elements[0]["url"], "edition": "2026-11-20"}]
    resultat = veille.nouveautes(elements + elements[:1], historique)
    assert elements[0]["url"] not in [e["url"] for e in resultat]
    assert len(resultat) == len(elements) - 1


def test_message_commit():
    assert veille.message_commit("2026-11-22", _tout()) == (
        "veille: édition du 2026-11-22 (2 articles, 2 papers, 2 discussions, 2 repos)"
    )


def test_readme(tmp_path):
    texte = page.readme(_tout(), "2026-11-22", ["2026-11-20", "2026-11-22"], tmp_path)
    assert "**Édition du 22 novembre 2026**" in texte
    assert "## Papers du moment" in texte
    assert "- [20 novembre 2026](editions/2026-11-20.md)" in texte
    assert "<img" not in texte  # pas d'image tant que assets/banniere.png n'existe pas
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "banniere.png").write_bytes(b"x")
    assert '<img src="assets/banniere.png"' in page.readme(_tout(), "2026-11-22", [], tmp_path)


def test_edition_vide():
    assert "Rien de nouveau" in page.edition([], "2026-11-22")
