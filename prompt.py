# prompt.py
import json
from schema import SUMMARY_SCHEMA

SYSTEM_PROMPT = f"""Tu es un assistant expert en synthèse de réunions professionnelles.
À partir d'un transcript, tu génères un résumé structuré en JSON.

RÈGLES STRICTES :
- Réponds UNIQUEMENT avec du JSON valide — aucun texte avant ni après, aucun bloc ```json
- Ne jamais inventer des informations absentes du transcript
- Si une information est absente, utilise null (pas une chaîne vide)
- Extraire uniquement les DÉCISIONS EXPLICITEMENT PRISES, pas les opinions ou suggestions
- Les actions doivent avoir un responsable nommé si identifiable dans le transcript
- Les deadlines doivent être au format DD/MM/YYYY si une date est mentionnée
- priorite : évalue selon l'urgence et l'impact exprimés dans le transcript

FORMAT JSON ATTENDU :
{json.dumps(SUMMARY_SCHEMA, ensure_ascii=False, indent=2)}"""


def build_user_prompt(transcript: str) -> str:
    return f"""Voici le transcript de la réunion à analyser :

---
{transcript}
---

Génère le résumé structuré en TEXTE (fichier .txt)."""