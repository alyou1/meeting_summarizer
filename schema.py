# schema.py
SUMMARY_SCHEMA = {
    "titre_reunion": "string | null",
    "date": "string | null",
    "duree_estimee": "string | null",
    "participants": ["liste de noms"],
    "ordre_du_jour": ["liste des points abordés"],
    "points_cles": ["max 5 éléments importants"],
    "decisions": [
        {
            "decision": "description de la décision",
            "contexte": "justification courte | null"
        }
    ],
    "actions": [
        {
            "action": "description de l'action",
            "responsable": "nom | null",
            "deadline": "DD/MM/YYYY | null",
            "priorite": "haute | moyenne | basse"
        }
    ],
    "prochaine_reunion": "string | null"
}