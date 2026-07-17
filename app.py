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
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
            padding-bottom: 3rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1200px;
        }
        .hero {
            padding: 1.5rem 1.6rem;
            border: 1px solid rgba(31, 41, 55, 0.08);
            border-radius: 1.25rem;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(10px);
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            margin-bottom: 0.25rem;
            font-size: 2.2rem;
        }
        .hero p {
            margin: 0;
            color: rgba(55, 65, 81, 0.9);
            font-size: 1rem;
        }
        .section-label {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.75rem;
            font-weight: 700;
            color: #b45309;
            margin-bottom: 0.6rem;
        }
        .feature-card strong {
            display: block;
            margin-bottom: 0.3rem;
            color: #111827;
            font-size: 1.02rem;
        }
        .feature-card span {
            color: #4b5563;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        /* Give every native bordered container (st.container(border=True))
           the same card treatment as the custom .feature-card blocks, so
           uploads, tips, summary, and transcript all read as one system. */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 1rem !important;
            border: 1px solid rgba(31, 41, 55, 0.08) !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            background: white;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border-radius: 1rem !important;
        }

        .stButton > button {
            border-radius: 0.65rem;
            font-weight: 600;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(220, 38, 38, 0.18);
        }

        [data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.02);
            border-radius: 0.75rem;
            padding: 0.6rem 0.75rem;
        }

        .stTextArea textarea {
            border-radius: 0.75rem;
        }

        /* Mobile: tighten padding and scale the hero heading down. */
        @media (max-width: 768px) {
            .block-container,
            [data-testid="stMainBlockContainer"] {
                padding-top: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .hero {
                padding: 1.1rem 1.2rem;
                border-radius: 1rem;
            }
            .hero h1 {
                font-size: 1.6rem;
            }
            .hero p {
                font-size: 0.9rem;
            }
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

left, right = st.columns([1.15, 0.85], vertical_alignment="top", gap="medium")

with left:
    st.markdown('<div class="section-label">Step 1</div>', unsafe_allow_html=True)
    with st.container(border=True):
        uploaded = st.file_uploader(
            "Upload a voice note",
            type=["ogg", "oga", "mp3", "m4a", "wav", "opus", "aac"],
            help="Drag and drop a file from WhatsApp, Telegram, or your phone.",
        )
        st.markdown(
            "<strong>Supported inputs</strong>"
            "<span>OGG, MP3, M4A, WAV, OPUS, AAC. The app converts audio automatically before transcription.</span>",
            unsafe_allow_html=True,
        )

with right:
    st.markdown('<div class="section-label">Tips</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            "<strong>Best results</strong>"
            "<span>Use one voice note per run, keep the file clear of long silences, and "
            "force Urdu or English only if auto-detection misses the language.</span>",
            unsafe_allow_html=True,
        )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

col_lang, col_action = st.columns([1, 2], vertical_alignment="center")
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

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.audio(uploaded)
        st.metric("Selected file", current_file_name)
        transcribe_clicked = st.button(
            "Transcribe & Summarize",
            type="primary",
            use_container_width=True,
        )

    if transcribe_clicked:
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
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        summary_box, transcript_box = st.columns([1, 1.2], gap="medium")
        result = payload["result"]
        summary = payload["summary"]

        with summary_box:
            st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)
            with st.container(border=True):
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
                    for idx, action in enumerate(actions):
                        st.checkbox(action, key=f"action_{idx}_{current_file_name}")

                tone_col, conf_col, dur_col = st.columns(3)
                tone_col.metric("Tone", summary.get("tone", "n/a"))
                conf_col.metric("Language", result["language"])
                dur_col.metric("Duration", f"{result['duration']}s")

        with transcript_box:
            st.markdown('<div class="section-label">Transcript</div>', unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("Full transcript")
                st.caption(f"Confidence {result['language_probability']} • {result['language']}")
                st.text_area("", value=result["text"], height=420, label_visibility="collapsed")

elif "voice_note_result" in st.session_state:
    st.info("Upload a voice note to generate a new transcript and summary.")
