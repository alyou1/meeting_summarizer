import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
from stt import transcribe
from llm import call_ollama
from components.display import render_summary
from export import transcript_to_txt, transcript_to_docx, summary_to_txt, summary_to_docx
#from recorder import AudioRecorder, list_input_devices
from audio_capture import DualAudioRecorder

st.set_page_config(page_title="Meeting Summarizer", layout="wide")
st.title("Meeting Summarizer")

# ── Sidebar : configuration ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    model_size = st.selectbox(
        "Modele Whisper",
        ["tiny", "small", "medium", "large-v3"],
        index=2,
        help="medium = bon equilibre. large-v3 pour accents ou jargon metier.",
    )

    st.divider()
    st.subheader("Diarisation des locuteurs")
    hf_token = st.text_input(
        "Token HuggingFace",
        type="password",
        help=(
            "Requis pour identifier les locuteurs. "
            "Cree ton token sur huggingface.co/settings/tokens, "
            "puis accepte les conditions sur pyannote/speaker-diarization-3.1."
        ),
        placeholder="hf_...",
    )
    num_speakers = st.number_input(
        "Nombre de participants (0 = detection auto)",
        min_value=0,
        max_value=20,
        value=0,
        step=1,
    )
    if hf_token:
        st.success("Token renseigne — diarisation activee")
    else:
        st.info("Sans token : transcription sans identification des locuteurs")

    st.divider()
    st.caption(
        "Pour capturer l'audio de tous les participants d'une reunion en ligne, "
        "installe **BlackHole** (brew install blackhole-2ch) et selectionne-le "
        "comme peripherique d'entree ci-dessous."
    )

# ── Initialisation etat ────────────────────────────────────────────────────────
for key in ("transcript", "summary", "recorder", "audio_bytes", "audio_filename"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Etape 1 : Source audio ────────────────────────────────────────────────────
st.subheader("1 · Source audio")

tab_record, tab_upload = st.tabs(["Enregistrement en direct", "Upload d'un fichier"])

with tab_record:
    devices = list_input_devices()
    if not devices:
        st.error("Aucun peripherique d'entree audio detecte.")
    else:
        device_labels = [f"{d['name']}" for d in devices]
        device_indices = [d["index"] for d in devices]

        selected_idx = st.selectbox(
            "Peripherique d'entree",
            range(len(device_labels)),
            format_func=lambda i: device_labels[i],
            help=(
                "Micro = capture uniquement votre voix. "
                "BlackHole / Loopback = capture tout l'audio systeme (tous les participants)."
            ),
        )
        selected_device_index = device_indices[selected_idx]

        recorder: DualAudioRecorder = st.session_state.get("recorder")
        is_recording = recorder is not None and recorder.is_recording

        col_start, col_stop, col_status = st.columns([1, 1, 4])

        with col_start:
            if st.button("Demarrer", disabled=is_recording, type="primary"):
                rec = DualAudioRecorder(samplerate=16000)
                rec.start()
                st.session_state["recorder"] = rec
                st.session_state["audio_bytes"] = None
                st.session_state["audio_filename"] = None
                st.rerun()

        with col_stop:
            if st.button("Arreter", disabled=not is_recording):
                wav_bytes = st.session_state["recorder"].stop()
                st.session_state["audio_bytes"] = wav_bytes
                st.session_state["audio_filename"] = "recording.wav"
                st.session_state["recorder"] = None
                st.rerun()

        with col_status:
            if is_recording:
                st.warning("Enregistrement en cours...")
            elif st.session_state.get("audio_bytes") and st.session_state.get("audio_filename") == "recording.wav":
                st.success("Enregistrement termine — pret pour la transcription")

        if (
            st.session_state.get("audio_bytes")
            and st.session_state.get("audio_filename") == "recording.wav"
        ):
            st.audio(st.session_state["audio_bytes"], format="audio/wav")

with tab_upload:
    uploaded = st.file_uploader(
        "Fichier audio de la reunion",
        type=["mp3", "mp4", "m4a", "wav", "ogg", "webm"],
        help="Enregistrement local depuis Teams, Zoom, Meet...",
    )
    if uploaded:
        st.session_state["audio_bytes"] = uploaded.read()
        st.session_state["audio_filename"] = uploaded.name

# ── Bouton transcription ───────────────────────────────────────────────────────
audio_bytes = st.session_state.get("audio_bytes")
audio_filename = st.session_state.get("audio_filename") or "audio.wav"

if audio_bytes and st.button("Generer le transcript", type="primary"):
    with st.spinner(f"Transcription avec le modele {model_size}..."):
        result = transcribe(
            audio_bytes=audio_bytes,
            filename=audio_filename,
            model_size=model_size,
            hf_token=hf_token or None,
            num_speakers=int(num_speakers) if num_speakers else None,
        )
        st.session_state["transcript"] = result["transcript"]
        st.session_state["summary"] = None

    st.success(
        f"Termine — {result['duration']:.0f}s audio · "
        f"{len(result['segments'])} segments · "
        f"langue : {result['language']}"
        + (" · diarisation activee" if hf_token else "")
    )

# ── Etape 2 : Revision du transcript ─────────────────────────────────────────
if st.session_state["transcript"]:
    st.subheader("2 · Revision du transcript")
    st.caption("Corrige si necessaire avant de lancer le resume.")

    st.session_state["transcript"] = st.text_area(
        "Transcript",
        value=st.session_state["transcript"],
        height=300,
        label_visibility="collapsed",
    )
    st.caption(f"{len(st.session_state['transcript'].split())} mots")

    col_btn, col_exp1, col_exp2 = st.columns([3, 1, 1])
    with col_btn:
        run_summary = st.button("Generer le resume", type="primary")
    with col_exp1:
        st.download_button(
            "Exporter .txt",
            data=transcript_to_txt(st.session_state["transcript"]),
            file_name="transcript.txt",
            mime="text/plain",
        )
    with col_exp2:
        st.download_button(
            "Exporter .docx",
            data=transcript_to_docx(st.session_state["transcript"]),
            file_name="transcript.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    if run_summary:
        with st.spinner("Analyse LLM en cours..."):
            st.session_state["summary"] = call_ollama(st.session_state["transcript"])
        st.success("Resume genere !")

# ── Etape 3 : Resume structure ────────────────────────────────────────────────
if st.session_state["summary"]:
    st.subheader("3 · Resume structure")
    render_summary(st.session_state["summary"])

    st.divider()
    col_exp3, col_exp4 = st.columns([1, 1])
    with col_exp3:
        st.download_button(
            "Exporter resume .txt",
            data=summary_to_txt(st.session_state["summary"]),
            file_name="resume_reunion.txt",
            mime="text/plain",
        )
    with col_exp4:
        st.download_button(
            "Exporter resume .docx",
            data=summary_to_docx(st.session_state["summary"]),
            file_name="resume_reunion.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
