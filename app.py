"""
app.py
Streamlit UI - drag & drop a voice note, get transcript + summary.

Run:  streamlit run app.py
"""

import html
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from transcriber import transcribe  # noqa: E402
from summarizer import summarize    # noqa: E402

st.set_page_config(page_title="Voice Note Summarizer", page_icon="🎙️", layout="wide")

# ---------------------------------------------------------------------------
# Design tokens + component overrides
#
# Selectors below target Streamlit's public data-testid hooks (stable across
# 1.3x+) plus the "st-key-<key>" classes Streamlit adds to widgets/containers
# created with key=..., so styling stays scoped instead of leaking globally.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        :root {
            --ink: #171a20;
            --slate: #5b6472;
            --slate-soft: #8992a1;
            --mist: #eef0f3;
            --paper: #f7f8fa;
            --panel: #ffffff;
            --hair: rgba(23, 26, 32, 0.11);
            --hair-strong: rgba(23, 26, 32, 0.20);

            --signal: #c96a2e;
            --signal-ink: #7a3f19;
            --signal-soft: rgba(201, 106, 46, 0.14);
            --trace: #2f8f8f;
            --trace-soft: rgba(47, 143, 143, 0.14);

            --success: #2f8f5b;
            --warning: #b8862c;

            --font-display: "Bahnschrift", "Arial Narrow", "Segoe UI Semibold", system-ui, sans-serif;
            --font-body: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
            --font-mono: "Cascadia Mono", Consolas, "SFMono-Regular", ui-monospace, Menlo, monospace;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --ink: #eef0f3;
                --slate: #9aa2ae;
                --slate-soft: #6d7683;
                --mist: #20242c;
                --paper: #14171c;
                --panel: #1b1f26;
                --hair: rgba(238, 240, 243, 0.10);
                --hair-strong: rgba(238, 240, 243, 0.18);

                --signal: #e08a4f;
                --signal-ink: #f3c39a;
                --signal-soft: rgba(224, 138, 79, 0.16);
                --trace: #4db8b8;
                --trace-soft: rgba(77, 184, 184, 0.14);

                --success: #4cb37e;
                --warning: #d3a44a;
            }
        }

        .stApp {
            background: var(--paper);
        }
        .stApp, .stApp p, .stApp li, .stApp label {
            font-family: var(--font-body);
            color: var(--ink);
        }
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-top: 3.25rem;
            padding-bottom: 3rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1180px;
        }

        /* ---------- Top bar ---------- */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding-bottom: 1.1rem;
            border-bottom: 1px solid var(--hair);
            margin-bottom: 1.8rem;
        }
        .brand { display: flex; align-items: center; gap: 0.7rem; }
        .brand-mark { display: flex; align-items: flex-end; gap: 2px; height: 20px; }
        .brand-mark span { width: 3px; background: var(--signal); border-radius: 1px; }
        .brand-mark span:nth-child(1) { height: 40%; }
        .brand-mark span:nth-child(2) { height: 100%; }
        .brand-mark span:nth-child(3) { height: 65%; }
        .brand-mark span:nth-child(4) { height: 85%; }
        .brand-mark span:nth-child(5) { height: 50%; }
        .brand-word {
            font-family: var(--font-display);
            font-weight: 700;
            letter-spacing: 0.01em;
            font-size: 1.1rem;
            line-height: 1;
            color: var(--ink);
        }
        .brand-word b { color: var(--signal); font-weight: 700; }
        .chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            border: 1px solid var(--hair-strong);
            color: var(--slate);
            background: var(--panel);
            white-space: nowrap;
        }
        .chip .dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: var(--success);
        }

        /* ---------- Intro ---------- */
        .intro { margin-bottom: 2.1rem; max-width: 640px; }
        .eyebrow {
            font-family: var(--font-mono);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            color: var(--signal-ink);
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .eyebrow::before { content: ""; width: 14px; height: 1px; background: var(--signal); }
        .intro h1 {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: clamp(1.7rem, 3vw, 2.3rem);
            margin: 0 0 0.5rem;
            color: var(--ink);
        }
        .intro p { margin: 0; color: var(--slate); font-size: 0.96rem; max-width: 56ch; }

        /* ---------- Section labels ---------- */
        .section-label {
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            font-family: var(--font-display);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
            color: var(--slate);
            margin-bottom: 0.6rem;
        }
        .section-label .num { font-family: var(--font-mono); font-weight: 400; color: var(--signal); }

        /* ---------- Panels (bordered containers) ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px !important;
            border: 1px solid var(--hair) !important;
            box-shadow: 0 1px 2px rgba(23, 26, 32, 0.04), 0 8px 20px rgba(23, 26, 32, 0.05);
            background: var(--panel);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 10px !important; }

        .panel-title {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.02rem;
            margin: 0 0 0.9rem;
            color: var(--ink);
        }
        .subhead {
            font-family: var(--font-mono);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.68rem;
            color: var(--slate-soft);
            margin: 0.9rem 0 0.5rem;
        }

        /* ---------- Widget labels / captions ---------- */
        [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] p,
        .st-key-upload_panel [data-testid="stWidgetLabel"] p {
            font-family: var(--font-mono);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.72rem;
            color: var(--slate-soft);
        }
        [data-testid="stCaptionContainer"] {
            font-family: var(--font-mono);
            color: var(--slate);
            font-size: 0.82rem;
        }

        /* ---------- Upload dropzone ---------- */
        .st-key-upload_panel [data-testid="stFileUploaderDropzone"] {
            background: var(--mist);
            border: 1.5px dashed var(--hair-strong);
            border-radius: 8px;
            transition: border-color 0.15s ease;
        }
        .st-key-upload_panel [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--signal);
        }
        .st-key-upload_panel [data-testid="stFileUploaderDropzoneInstructions"] svg {
            fill: var(--signal) !important;
        }
        .st-key-upload_panel [data-testid="stFileUploaderDropzone"] button {
            border-radius: 7px !important;
            border: 1px solid var(--hair-strong) !important;
            background: var(--panel) !important;
            color: var(--ink) !important;
            font-weight: 600 !important;
        }
        .format-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 1rem; }
        .fmt {
            font-family: var(--font-mono);
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            color: var(--slate);
            border: 1px solid var(--hair);
            border-radius: 4px;
            padding: 0.2rem 0.45rem;
        }
        .fine-print {
            margin-top: 0.85rem;
            font-size: 0.8rem;
            color: var(--slate-soft);
            display: flex;
            justify-content: space-between;
            font-family: var(--font-mono);
        }

        /* ---------- Tips ---------- */
        .tip-row { display: flex; gap: 0.7rem; align-items: flex-start; }
        .tip-row + .tip-row { margin-top: 0.85rem; padding-top: 0.85rem; border-top: 1px solid var(--hair); }
        .tip-mark {
            flex: none;
            width: 20px; height: 20px;
            border-radius: 5px;
            background: var(--trace-soft);
            color: var(--trace);
            display: flex; align-items: center; justify-content: center;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            margin-top: 0.1rem;
        }
        .tip-copy strong { display: block; font-size: 0.87rem; color: var(--ink); margin-bottom: 0.15rem; }
        .tip-copy span { font-size: 0.84rem; color: var(--slate); }

        /* ---------- Selectbox ---------- */
        [data-testid="stSelectbox"] > div > div {
            border-radius: 8px !important;
            border-color: var(--hair-strong) !important;
            font-family: var(--font-mono);
        }

        /* ---------- Buttons ---------- */
        [data-testid="stBaseButton-primary"] {
            background: var(--signal) !important;
            border-color: var(--signal) !important;
            color: #fff8f1 !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            box-shadow: 0 6px 16px rgba(201, 106, 46, 0.28);
            transition: filter 0.12s ease, transform 0.12s ease;
        }
        [data-testid="stBaseButton-primary"]:hover { filter: brightness(1.07); transform: translateY(-1px); }
        [data-testid="stBaseButton-secondary"],
        [data-testid="stDownloadButton"] button {
            border-radius: 7px !important;
            border: 1px solid var(--hair-strong) !important;
            font-weight: 600 !important;
            color: var(--ink) !important;
        }
        [data-testid="stDownloadButton"] button {
            font-family: var(--font-mono);
            font-size: 0.82rem !important;
        }

        /* ---------- Metrics (used as compact mono readouts) ---------- */
        [data-testid="stMetric"] {
            background: var(--mist);
            border: 1px solid var(--hair);
            border-radius: 7px;
            padding: 0.6rem 0.75rem;
        }
        [data-testid="stMetricLabel"] p {
            font-family: var(--font-mono);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.64rem;
            color: var(--slate-soft);
        }
        [data-testid="stMetricValue"] {
            font-family: var(--font-mono);
            font-variant-numeric: tabular-nums;
            color: var(--ink);
            font-weight: 600;
            font-size: 1rem !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }
        .st-key-meta_row {
            border-top: 1px solid var(--hair);
            padding-top: 1.1rem;
            margin-top: 0.3rem;
        }

        /* ---------- Key points bullets ---------- */
        .st-key-summary_panel [data-testid="stMarkdownContainer"] ul {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }
        .st-key-summary_panel [data-testid="stMarkdownContainer"] ul li {
            display: flex;
            gap: 0.55rem;
            align-items: flex-start;
            font-size: 0.9rem;
            color: var(--ink);
        }
        .st-key-summary_panel [data-testid="stMarkdownContainer"] ul li::before {
            content: "";
            flex: none;
            width: 7px; height: 7px;
            margin-top: 0.42rem;
            border-radius: 1px;
            background: var(--trace);
            transform: rotate(45deg);
        }

        /* ---------- Checkboxes (action items) ---------- */
        input[type="checkbox"] { accent-color: var(--signal); }

        /* ---------- Transcript ---------- */
        .transcript-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }
        .confidence-wrap { display: flex; align-items: center; gap: 0.55rem; }
        .lang-chip {
            font-family: var(--font-mono);
            font-size: 0.72rem;
            padding: 0.2rem 0.5rem;
            border-radius: 5px;
            background: var(--trace-soft);
            color: var(--trace);
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .confidence-bar {
            width: 80px; height: 6px;
            border-radius: 999px;
            background: var(--mist);
            overflow: hidden;
        }
        .confidence-bar > span {
            display: block; height: 100%;
            background: linear-gradient(90deg, var(--warning), var(--success));
        }
        .confidence-label {
            font-family: var(--font-mono);
            font-size: 0.76rem;
            color: var(--slate);
            white-space: nowrap;
        }

        .st-key-transcript_panel [data-testid="stCode"] {
            border-radius: 6px !important;
            border: 1px solid var(--hair) !important;
            border-left: 3px solid var(--trace) !important;
            background: var(--mist) !important;
        }
        .st-key-transcript_panel [data-testid="stCode"] pre,
        .st-key-transcript_panel [data-testid="stCode"] code {
            background: transparent !important;
            font-family: var(--font-mono) !important;
            font-size: 0.9rem !important;
            line-height: 1.75 !important;
            color: var(--ink) !important;
        }

        /* ---------- Audio player ---------- */
        [data-testid="stAudio"] audio { width: 100%; border-radius: 8px; }

        /* ---------- Alerts / spinner ---------- */
        [data-testid="stAlertContainer"] {
            border-radius: 8px !important;
            font-family: var(--font-body);
        }
        [data-testid="stSpinner"] { font-family: var(--font-body); color: var(--slate); }

        footer.app-footer {
            margin-top: 2.6rem;
            padding-top: 1.1rem;
            border-top: 1px solid var(--hair);
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--slate-soft);
        }

        /* Mobile: tighten padding and scale the heading down. */
        @media (max-width: 768px) {
            .block-container,
            [data-testid="stMainBlockContainer"] {
                padding-top: 1.1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .topbar { flex-wrap: wrap; gap: 0.6rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="topbar">
        <div class="brand">
            <span class="brand-mark" aria-hidden="true">
                <span></span><span></span><span></span><span></span><span></span>
            </span>
            <span class="brand-word">VOICE NOTE <b>SUMMARIZER</b></span>
        </div>
        <span class="chip"><span class="dot"></span>local whisper model</span>
    </div>
    <div class="intro">
        <div class="eyebrow">audio &rarr; transcript &rarr; summary</div>
        <h1>Turn a voice note into a brief you can act on.</h1>
        <p>Upload a recording and get a full transcript alongside a compact summary, key points, and
        action items &mdash; Urdu, English, or mixed.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 0.85], vertical_alignment="top", gap="medium")

with left:
    st.markdown('<div class="section-label"><span class="num">01</span> Upload</div>', unsafe_allow_html=True)
    with st.container(border=True, key="upload_panel"):
        uploaded = st.file_uploader(
            "Upload a voice note",
            type=["ogg", "oga", "mp3", "m4a", "wav", "opus", "aac"],
            help="Drag and drop a file from WhatsApp, Telegram, or your phone.",
        )
        st.markdown(
            """
            <div class="format-row">
                <span class="fmt">OGG</span><span class="fmt">OGA</span><span class="fmt">MP3</span>
                <span class="fmt">M4A</span><span class="fmt">WAV</span><span class="fmt">OPUS</span><span class="fmt">AAC</span>
            </div>
            <div class="fine-print">
                <span>200 MB per file</span>
                <span>converted automatically before transcription</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

with right:
    st.markdown('<div class="section-label">Tips</div>', unsafe_allow_html=True)
    with st.container(border=True, key="tips_panel"):
        st.markdown(
            """
            <div class="tip-row">
                <span class="tip-mark">1</span>
                <div class="tip-copy">
                    <strong>One note per run</strong>
                    <span>Batching several recordings in one file blends their summaries together.</span>
                </div>
            </div>
            <div class="tip-row">
                <span class="tip-mark">2</span>
                <div class="tip-copy">
                    <strong>Trim long silences</strong>
                    <span>Dead air lowers transcription confidence more than background noise does.</span>
                </div>
            </div>
            <div class="tip-row">
                <span class="tip-mark">3</span>
                <div class="tip-copy">
                    <strong>Set language manually if needed</strong>
                    <span>Force Urdu or English when auto-detection misreads a short or mixed clip.</span>
                </div>
            </div>
            """,
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

    with st.container(border=True, key="file_panel"):
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
        st.markdown('<div class="section-label"><span class="num">02</span> Result</div>', unsafe_allow_html=True)
        summary_box, transcript_box = st.columns([1, 1.2], gap="medium")
        result = payload["result"]
        summary = payload["summary"]

        with summary_box:
            with st.container(border=True, key="summary_panel"):
                st.markdown('<h2 class="panel-title">Summary</h2>', unsafe_allow_html=True)
                st.write(summary.get("summary", ""))

                key_points = summary.get("key_points") or []
                if key_points:
                    st.markdown('<p class="subhead">Key points</p>', unsafe_allow_html=True)
                    st.markdown("\n".join(f"- {point}" for point in key_points))

                actions = summary.get("action_items") or []
                if actions:
                    st.markdown('<p class="subhead">Action items</p>', unsafe_allow_html=True)
                    for idx, action in enumerate(actions):
                        st.checkbox(action, key=f"action_{idx}_{current_file_name}")

                with st.container(key="meta_row"):
                    tone_col, conf_col, dur_col = st.columns(3)
                    tone_col.metric("Tone", summary.get("tone", "n/a"))
                    conf_col.metric("Language", result["language"])
                    dur_col.metric("Duration", f"{result['duration']}s")

        with transcript_box:
            with st.container(border=True, key="transcript_panel"):
                lang_code = html.escape(str(result["language"]))
                confidence = float(result["language_probability"])
                pct = max(0, min(100, round(confidence * 100)))
                st.markdown(
                    f"""
                    <div class="transcript-head">
                        <h2 class="panel-title" style="margin:0;">Full transcript</h2>
                        <div class="confidence-wrap">
                            <span class="lang-chip">{lang_code}</span>
                            <div class="confidence-bar"><span style="width:{pct}%;"></span></div>
                            <span class="confidence-label">{confidence:.2f} confidence</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.code(result["text"], language=None, wrap_lines=True, height=340)
                st.download_button(
                    "Download transcript (.txt)",
                    data=result["text"],
                    file_name=f"{Path(current_file_name).stem}-transcript.txt",
                    mime="text/plain",
                )

elif "voice_note_result" in st.session_state:
    st.info("Upload a voice note to generate a new transcript and summary.")

st.markdown(
    """
    <footer class="app-footer">
        <span>Runs on a local Whisper model &mdash; audio never leaves this machine.</span>
        <span>v2</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
