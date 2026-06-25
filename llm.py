# llm.py
import json
import re
from ollama import Client as OllamaClient
from prompt import SYSTEM_PROMPT, build_user_prompt


def call_ollama(transcript: str, model: str = "deepseek-r1:8b") -> dict:
    client = OllamaClient()

    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(transcript)}
        ],
        options={"temperature": 0.1}  # basse température pour JSON stable
    )

    raw = response["message"]["content"]
    return parse_json_response(raw)


def parse_json_response(raw: str) -> dict:
    """Nettoie et parse la réponse LLM, même si elle contient du texte parasite."""

    # 1. Supprimer les balises <think>...</think> (deepseek-r1 les inclut parfois)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # 2. Extraire le bloc JSON si entouré de backticks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        raw = match.group(1)

    # 3. Parser
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 4. Dernière tentative : trouver le premier { ... } valide
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Impossible de parser la réponse LLM :\n{raw[:300]}")