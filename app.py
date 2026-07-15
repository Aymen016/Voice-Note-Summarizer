"""
app.py
Streamlit UI - drag & drop a voice note, get transcript + summary.

Run:  streamlit run app.py
"""

import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from transcriber import transcribe  # noqa: E402
from summarizer import summarize    # noqa: E402

st.set_page_config(page_title="Voice Note Summarizer", page_icon="🎙️", layout="wide")

st.title("🎙️ Voice Note Summarizer")
st.caption("Handles Urdu-English mixed voice notes • faster-whisper + Groq (free tier)")

source = st.radio("Source", ["Upload a file", "Record directly"], horizontal=True)

if source == "Upload a file":
    uploaded = st.file_uploader(
        "Drop a voice note",
        type=["ogg", "oga", "mp3", "m4a", "wav", "opus", "aac"],
    )
else:
    uploaded = st.audio_input("Record a voice note")

col_lang, _ = st.columns([1, 3])
with col_lang:
    lang_choice = st.selectbox("Language", ["auto-detect", "ur (Urdu)", "en (English)"])

lang = None
if lang_choice.startswith("ur"):
    lang = "ur"
elif lang_choice.startswith("en"):
    lang = "en"

if uploaded is not None:
    st.audio(uploaded)

    if st.button("Transcribe & Summarize", type="primary"):
        suffix = Path(uploaded.name).suffix or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        with st.spinner("Transcribing (first run downloads the whisper model)..."):
            result = transcribe(tmp_path, language=lang)

        with st.spinner("Summarizing with Groq..."):
            summary = summarize(result["text"])

        left, right = st.columns(2)

        with left:
            st.subheader("📝 Summary")
            st.write(summary.get("summary", ""))

            key_points = summary.get("key_points") or []
            if key_points:
                st.markdown("**🔑 Key points**")
                for p in key_points:
                    st.markdown(f"- {p}")

            actions = summary.get("action_items") or []
            if actions:
                st.markdown("**✅ Action items**")
                for a in actions:
                    st.checkbox(a, key=f"action_{a}")

            st.markdown(f"**🎭 Tone:** {summary.get('tone', 'n/a')}")

        with right:
            st.subheader("🗒️ Transcript")
            st.caption(
                f"language: {result['language']} "
                f"(confidence {result['language_probability']}) • {result['duration']}s"
            )
            st.text_area("", value=result["text"], height=350, label_visibility="collapsed")
