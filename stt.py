import os
import tempfile
import streamlit as st
from faster_whisper import WhisperModel


@st.cache_resource(show_spinner=False)
def load_model(model_size: str = "medium") -> WhisperModel:
    """Chargé une seule fois, mis en cache pour toute la session Streamlit."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe(audio_bytes: bytes, filename: str, model_size: str = "medium") -> dict:
    """
    Transcrit un fichier audio en texte.

    Args:
        audio_bytes : contenu brut du fichier uploadé
        filename    : nom d'origine pour conserver l'extension
        model_size  : "tiny" | "small" | "medium" | "large-v3"

    Returns:
        dict { transcript, segments, language, duration }
    """
    ext = os.path.splitext(filename)[-1].lower()
    supported = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm"}
    if ext not in supported:
        raise ValueError(f"Format non supporté : {ext}. Acceptés : {', '.join(supported)}")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = load_model(model_size)
        segments_gen, info = model.transcribe(
            tmp_path,
            language=None,  # détection automatique (fr, en, ...)
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        # Feedback progressif : affiche chaque segment au fil de la transcription
        placeholder = st.empty()
        full_parts = []
        segments_list = []

        for seg in segments_gen:
            text = seg.text.strip()
            if not text:
                continue
            full_parts.append(text)
            segments_list.append({
                "start": round(seg.start, 2),
                "end":   round(seg.end, 2),
                "text":  text,
            })
            placeholder.caption(f"… {text}")

        placeholder.empty()

        return {
            "transcript": " ".join(full_parts),
            "segments":   segments_list,
            "language":   info.language,
            "duration":   round(info.duration, 2),
        }

    finally:
        os.unlink(tmp_path)