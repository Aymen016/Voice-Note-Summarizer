---
title: Voice Note Summarizer
emoji: 🎙️
colorFrom: yellow
colorTo: blue
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
---

# 🎙️ Voice Note Summarizer

Turn long WhatsApp voice notes into short summaries with action items — **including Urdu-English mixed (code-switched) speech**.

Built with **faster-whisper** (local, free transcription) + **Groq** (summarization). No paid APIs.

## How it works

```
voice note (.ogg) → ffmpeg (16kHz mono wav) → faster-whisper → transcript → Groq chat completion → summary + action items + tone
```

## Features

- 🇵🇰 Handles Urdu-English code-switched speech (auto language detection)
- 📝 2-3 line summary in plain English
- ✅ Extracts action items automatically
- 🎭 Detects tone (casual / urgent / formal ...)
- 🖥️ CLI + Streamlit web UI
- 💸 100% free — whisper runs locally, Groq free tier covers generous daily usage

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

**3. Get a free Groq API key**

Grab one at [console.groq.com/keys](https://console.groq.com/keys) (no credit card), then:

```bash
cp .env.example .env
# paste your key into .env
```

## Deploy on Hugging Face Spaces

This project can run as a Streamlit Space.

1. Create a new Space on Hugging Face and choose the Streamlit SDK.
2. Push this repository to the Space.
3. Add `GROQ_API_KEY` in the Space secrets/settings panel.
4. Keep `packages.txt` in the repo so Hugging Face installs `ffmpeg`.

Recommended Space settings:

- SDK: Streamlit
- Python version: 3.10 or newer
- App file: `app.py`

If the Space feels slow on CPU, set `WHISPER_MODEL=base` or `WHISPER_MODEL=tiny` in the Space environment variables.

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
