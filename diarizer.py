"""
Diarisation des locuteurs via pyannote.audio.
Necessite un token HuggingFace avec acces au modele pyannote/speaker-diarization-3.1.

Prerequis HuggingFace :
  1. Creer un token sur huggingface.co/settings/tokens
  2. Accepter les conditions d'utilisation sur :
     - huggingface.co/pyannote/speaker-diarization-3.1
     - huggingface.co/pyannote/segmentation-3.0
"""
from typing import List, Dict, Optional

import streamlit as st


@st.cache_resource(show_spinner=False)
def _load_pipeline(hf_token: str):
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    return pipeline


def diarize(
    audio_path: str,
    hf_token: str,
    num_speakers: Optional[int] = None,
) -> List[Dict]:
    """
    Identifie les locuteurs dans un fichier audio.

    Args:
        audio_path   : chemin vers le fichier audio temporaire
        hf_token     : token HuggingFace
        num_speakers : nombre de locuteurs attendus (None = detection automatique)

    Returns:
        [{"start": float, "end": float, "speaker": str}, ...]
    """
    pipeline = _load_pipeline(hf_token)

    params = {}
    if num_speakers and num_speakers > 1:
        params["num_speakers"] = num_speakers

    diarization = pipeline(audio_path, **params)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 2),
            "end":   round(turn.end, 2),
            "speaker": speaker,
        })
    return segments
