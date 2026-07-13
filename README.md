# 🎙️ Voice Note Summarizer

Turn long WhatsApp voice notes into short summaries with action items — **including Urdu-English mixed (code-switched) speech**.

Built with **faster-whisper** (local, free transcription) + **Gemini free tier** (summarization). No paid APIs.

## How it works

```
voice note (.ogg) → ffmpeg (16kHz mono wav) → faster-whisper → transcript → Gemini Flash → summary + action items + tone
```

## Features

- 🇵🇰 Handles Urdu-English code-switched speech (auto language detection)
- 📝 2-3 line summary in plain English
- ✅ Extracts action items automatically
- 🎭 Detects tone (casual / urgent / formal ...)
- 🖥️ CLI + Streamlit web UI
- 💸 100% free — whisper runs locally, Gemini free tier covers ~1500 notes/day

## Setup

**1. Install ffmpeg**

```bash
# Windows
winget install ffmpeg
# Ubuntu/Debian
sudo apt install ffmpeg
# macOS
brew install ffmpeg
```

**2. Install Python deps**

```bash
pip install -r requirements.txt
```

**3. Get a free Gemini API key**

Grab one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (no credit card), then:

```bash
cp .env.example .env
# paste your key into .env
```

## Usage

**CLI:**

```bash
python main.py voicenote.ogg
python main.py voicenote.ogg --show-transcript
python main.py voicenote.ogg --language ur   # force Urdu if auto-detect struggles
```

**Web UI:**

```bash
streamlit run app.py
```

Drag-drop a voice note → get transcript + summary side by side.

## Notes on accuracy

- Default whisper model is `small` — good balance on CPU. If Urdu accuracy is weak, set `WHISPER_MODEL=medium` in `.env` (slower but noticeably better).
- First run downloads the whisper model (~460MB for small) — cached after that.
- `vad_filter=True` skips silences, which speeds up typical voice notes a lot.

## Roadmap

- [ ] Telegram bot — forward a voice note, get a summary back
- [ ] Batch mode — summarize a folder of notes
- [ ] Roman Urdu normalization pass
