# Fonctionnement technique

Tous les deux jours, un GitHub Action lance `src/veille.py`, qui prépare une nouvelle édition de la veille.

## Sources

| Rubrique | Source | Accès |
|---|---|---|
| À lire | OpenAI, Google DeepMind, Google Research, Hugging Face, Simon Willison, ActuIA | Flux RSS et Atom publics |
| Papers du moment | Hugging Face Papers | API publique `huggingface.co/api/daily_papers` |
| Discussions | Hacker News | API Algolia `hn.algolia.com/api/v1/search_by_date` |
| Repos à suivre | GitHub | API de recherche, avec le jeton fourni par GitHub Actions |

Chaque source est indépendante : si l'une est en panne, l'édition paraît avec les autres.

## Règles de sélection

- Articles : publiés dans les 4 derniers jours, 5 au maximum par source.
- Papers : les 8 plus votés parmi ceux mis en avant dans les 4 derniers jours.
- Discussions : sujets de plus de 100 points dont le titre parle d'IA, les 8 plus votés.
- Repos : créés dans les 14 derniers jours, plus de 50 étoiles, sur les sujets `llm`, `ai-agents`, `generative-ai`, `rag` et `machine-learning`, les 8 plus étoilés.
- Un lien déjà paru dans une édition précédente n'est jamais repris (voir `data/historique.csv`).

## Structure

```
src/
├── veille.py            # orchestration : collecte, nouveautés, fichiers
├── page.py              # mise en forme du README et des éditions
└── sources/
    ├── flux.py          # blogs et médias (RSS, Atom)
    ├── papers.py        # Hugging Face Papers
    ├── hacker_news.py   # Hacker News
    └── github_repos.py  # repos GitHub
data/historique.csv      # tout ce qui a paru, édition par édition
editions/AAAA-MM-JJ.md   # archive de chaque édition
```

Le README est réécrit à chaque édition. Pour changer sa présentation, modifier `src/page.py`.
Pour ajouter un blog, ajouter une ligne dans `FLUX` (`src/sources/flux.py`).
Pour afficher une image en haut de la page, déposer un fichier `assets/banniere.png`.

## Lancer en local

```bash
pip install -r requirements.txt
python src/veille.py
```

Tests :

```bash
pip install pytest
pytest
```
