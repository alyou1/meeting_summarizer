import streamlit as st
from stt import transcribe
from llm import call_ollama
from components.display import render_summary
from export import transcript_to_txt, transcript_to_docx, summary_to_txt, summary_to_docx

st.set_page_config(page_title="Meeting Summarizer", layout="wide")
st.title("Meeting Summarizer")

# Initialisation état
for key in ("transcript", "summary"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── Étape 1 : Source audio ────────────────────────────────────────────────────
st.subheader("1 · Source audio")

model_size = st.selectbox(
    "Modèle Whisper",
    ["tiny", "small", "medium", "large-v3"],
    index=2,
    help="medium = bon équilibre. large-v3 pour accents ou jargon métier.",
)

tab_record, tab_upload = st.tabs(["Enregistrement en direct", "Upload d'un fichier"])

audio_bytes = None
audio_filename = "recording.wav"

with tab_record:
    st.caption("Appuie sur le micro pour démarrer l'enregistrement, puis à nouveau pour l'arrêter.")
    recorded = st.audio_input("Enregistrer la réunion", label_visibility="collapsed")
    if recorded:
        audio_bytes = recorded.read()
        audio_filename = "recording.wav"
        st.audio(audio_bytes, format="audio/wav")

with tab_upload:
    uploaded = st.file_uploader(
        "Fichier audio de la réunion",
        type=["mp3", "mp4", "m4a", "wav", "ogg", "webm"],
        help="Enregistrement local depuis Teams, Zoom, Meet…",
    )
    if uploaded:
        audio_bytes = uploaded.read()
        audio_filename = uploaded.name

if audio_bytes and st.button("Générer le transcript", type="primary"):
    with st.spinner(f"Transcription avec le modèle {model_size}…"):
        result = transcribe(
            audio_bytes=audio_bytes,
            filename=audio_filename,
            model_size=model_size,
        )
        st.session_state["transcript"] = result["transcript"]
        st.session_state["summary"] = None

    st.success(
        f"Terminé — {result['duration']:.0f}s audio · "
        f"{len(result['segments'])} segments · "
        f"langue : {result['language']}"
    )

# ── Étape 2 : Révision du transcript ─────────────────────────────────────────
if st.session_state["transcript"]:
    st.subheader("2 · Révision du transcript")
    st.caption("Corrige si nécessaire avant de lancer le résumé.")

    st.session_state["transcript"] = st.text_area(
        "Transcript",
        value=st.session_state["transcript"],
        height=300,
        label_visibility="collapsed",
    )
    st.caption(f"{len(st.session_state['transcript'].split())} mots")

    col_btn, col_exp1, col_exp2 = st.columns([3, 1, 1])
    with col_btn:
        run_summary = st.button("Générer le résumé", type="primary")
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
        with st.spinner("Analyse LLM en cours…"):
            st.session_state["summary"] = call_ollama(st.session_state["transcript"])
        st.success("Résumé généré !")

# ── Étape 3 : Résumé structuré ────────────────────────────────────────────────
if st.session_state["summary"]:
    st.subheader("3 · Résumé structuré")
    render_summary(st.session_state["summary"])

    st.divider()
    col_exp3, col_exp4 = st.columns([1, 1])
    with col_exp3:
        st.download_button(
            "Exporter résumé .txt",
            data=summary_to_txt(st.session_state["summary"]),
            file_name="resume_reunion.txt",
            mime="text/plain",
        )
    with col_exp4:
        st.download_button(
            "Exporter résumé .docx",
            data=summary_to_docx(st.session_state["summary"]),
            file_name="resume_reunion.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )