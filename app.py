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

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 206, 120, 0.18), transparent 28%),
                radial-gradient(circle at top right, rgba(120, 180, 255, 0.12), transparent 24%),
                linear-gradient(180deg, #fffaf3 0%, #ffffff 38%, #f7f5f0 100%);
        }
        .hero {
            padding: 1.5rem 1.6rem;
            border: 1px solid rgba(31, 41, 55, 0.08);
            border-radius: 1.25rem;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(10px);
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin-bottom: 0.25rem;
        }
        .hero p {
            margin: 0;
            color: rgba(55, 65, 81, 0.9);
            font-size: 1rem;
        }
        .feature-card {
            padding: 1rem 1.1rem;
            border-radius: 1rem;
            background: white;
            border: 1px solid rgba(31, 41, 55, 0.08);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            height: 100%;
        }
        .feature-card strong {
            display: block;
            margin-bottom: 0.3rem;
            color: #111827;
        }
        .feature-card span {
            color: #4b5563;
            font-size: 0.95rem;
        }
        .section-label {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.75rem;
            font-weight: 700;
            color: #b45309;
            margin-bottom: 0.4rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="section-label">Audio to summary</div>
        <h1>Voice Note Summarizer</h1>
        <p>Upload a voice note to get a transcript, a compact summary, key points, and action items in one pass.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 0.85], vertical_alignment="top")

with left:
    st.markdown('<div class="section-label">Step 1</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload a voice note",
        type=["ogg", "oga", "mp3", "m4a", "wav", "opus", "aac"],
        help="Drag and drop a file from WhatsApp, Telegram, or your phone.",
    )

    st.markdown(
        "<div class='feature-card'><strong>Supported inputs</strong><span>OGG, MP3, M4A, WAV, OPUS, AAC. The app converts audio automatically before transcription.</span></div>",
        unsafe_allow_html=True,
    )

with right:
    st.markdown('<div class="section-label">Tips</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='feature-card'><strong>Best results</strong><span>Use one voice note per run, keep the file clear of long silences, and force Urdu or English only if auto-detection misses the language.</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

col_lang, col_action = st.columns([1, 2])
with col_lang:
    lang_choice = st.selectbox("Language", ["auto-detect", "ur (Urdu)", "en (English)"])

with col_action:
    st.caption("The model handles Urdu-English mixed speech and returns transcript plus structured notes.")

lang = None
if lang_choice.startswith("ur"):
    lang = "ur"
elif lang_choice.startswith("en"):
    lang = "en"

if uploaded is not None:
    current_file_name = uploaded.name
    cached_file_name = st.session_state.get("voice_note_file_name")
    if cached_file_name != current_file_name:
        st.session_state.pop("voice_note_result", None)

    summary_col, transcript_col = st.columns([1, 1.2], gap="large")

    with summary_col:
        st.audio(uploaded)
        st.metric("Selected file", current_file_name)

        if st.button("Transcribe & Summarize", type="primary", use_container_width=True):
            suffix = Path(uploaded.name).suffix or ".ogg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name

            with st.spinner("Transcribing (first run downloads the whisper model)..."):
                result = transcribe(tmp_path, language=lang)

            with st.spinner("Summarizing..."):
                summary = summarize(result["text"])

            st.session_state["voice_note_result"] = {
                "file_name": current_file_name,
                "result": result,
                "summary": summary,
            }
            st.session_state["voice_note_file_name"] = current_file_name

    payload = st.session_state.get("voice_note_result")
    if payload:
        result = payload["result"]
        summary = payload["summary"]

        summary_box, transcript_box = st.columns(2, gap="large")

        with summary_box:
            st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)
            st.subheader("Summary")
            st.write(summary.get("summary", ""))

            key_points = summary.get("key_points") or []
            if key_points:
                st.markdown("**Key points**")
                for point in key_points:
                    st.markdown(f"- {point}")

            actions = summary.get("action_items") or []
            if actions:
                st.markdown("**Action items**")
                for action in actions:
                    st.checkbox(action, key=f"action_{action}")

            tone_col, conf_col, dur_col = st.columns(3)
            tone_col.metric("Tone", summary.get("tone", "n/a"))
            conf_col.metric("Language", result["language"])
            dur_col.metric("Duration", f"{result['duration']}s")

        with transcript_box:
            st.markdown('<div class="section-label">Transcript</div>', unsafe_allow_html=True)
            st.subheader("Full transcript")
            st.caption(f"Confidence {result['language_probability']} • {result['language']}")
            st.text_area("", value=result["text"], height=420, label_visibility="collapsed")

elif "voice_note_result" in st.session_state:
    st.info("Upload a voice note to generate a new transcript and summary.")
