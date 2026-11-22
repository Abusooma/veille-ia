"""Chaque source expose collecter(session, depuis) -> list[dict] au format commun :

{
    "categorie": "articles" | "papers" | "discussions" | "repos",
    "source": nom affiché,
    "titre": ...,
    "url": lien principal,
    "publie_le": "AAAA-MM-JJ",
    "score": nombre (votes, points, étoiles) ou 0,
    "detail": courte information complémentaire (langage, nombre de commentaires...),
    "lien_discussion": lien secondaire éventuel,
}
"""

USER_AGENT = "veille-ia/1.0 (+https://github.com/Abusooma/veille-ia)"
