import os
import tempfile
from typing import List, Dict, Optional

import streamlit as st
from faster_whisper import WhisperModel


@st.cache_resource(show_spinner=False)
def load_model(model_size: str = "medium") -> WhisperModel:
    """Charge le modele Whisper une seule fois et le met en cache."""
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def _find_speaker(seg_start: float, seg_end: float, speaker_segs: List[Dict]) -> str:
    """Associe un segment Whisper au locuteur le plus present sur cet intervalle."""
    best_speaker = "SPEAKER_00"
    best_overlap = 0.0
    for sp in speaker_segs:
        overlap = min(seg_end, sp["end"]) - max(seg_start, sp["start"])
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = sp["speaker"]
    return best_speaker


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def transcribe(
    audio_bytes: bytes,
    filename: str,
    model_size: str = "medium",
    hf_token: Optional[str] = None,
    num_speakers: Optional[int] = None,
) -> dict:
    """
    Transcrit un fichier audio, avec identification optionnelle des locuteurs.

    Args:
        audio_bytes  : contenu brut du fichier audio
        filename     : nom d'origine (pour conserver l'extension)
        model_size   : "tiny" | "small" | "medium" | "large-v3"
        hf_token     : token HuggingFace pour activer la diarisation (optionnel)
        num_speakers : nombre de participants attendus (None = auto)

    Returns:
        dict { transcript, segments, language, duration }
    """
    ext = os.path.splitext(filename)[-1].lower() or ".wav"
    supported = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm"}
    if ext not in supported:
        raise ValueError(f"Format non supporte : {ext}. Acceptes : {', '.join(supported)}")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # ── Transcription Whisper ──────────────────────────────────────────────
        model = load_model(model_size)
        segments_gen, info = model.transcribe(
            tmp_path,
            language=None,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

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
            placeholder.caption(f"... {text}")

        placeholder.empty()

        # ── Diarisation (si token fourni) ──────────────────────────────────────
        if hf_token and hf_token.strip():
            from diarizer import diarize as run_diarize
            with st.spinner("Identification des locuteurs en cours..."):
                speaker_segs = run_diarize(tmp_path, hf_token.strip(), num_speakers)

            lines = []
            prev_speaker = None
            for seg in segments_list:
                speaker = _find_speaker(seg["start"], seg["end"], speaker_segs)
                label = speaker.replace("SPEAKER_", "Intervenant ")
                if speaker != prev_speaker:
                    lines.append(f"\n[{label}] {_fmt_time(seg['start'])}")
                    prev_speaker = speaker
                lines.append(seg["text"])

            transcript = "\n".join(lines).strip()
        else:
            transcript = " ".join(full_parts)

        return {
            "transcript": transcript,
            "segments":   segments_list,
            "language":   info.language,
            "duration":   round(info.duration, 2),
        }

    finally:
        os.unlink(tmp_path)
