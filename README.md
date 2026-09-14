

<div align="center">

# 🎙️ Voice Note Summarizer

**Turn long WhatsApp voice notes into short summaries with action items —
including Urdu-English mixed (code-switched) speech.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img width="1909" height="927" alt="Screenshot 2026-09-15 003320" src="https://github.com/user-attachments/assets/63911487-2c72-4270-a8df-5894eebd453a" />

</div>

Built with **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** for local, free
transcription and **[Groq](https://groq.com/)** for fast, free summarization. No paid APIs required.

## Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deploy on Hugging Face Spaces](#deploy-on-hugging-face-spaces)
- [Project structure](#project-structure)
- [Notes on accuracy](#notes-on-accuracy)
- [Roadmap](#roadmap)
- [License](#license)

## How it works

```
voice note (.ogg/.mp3/.m4a/.wav)
        │  ffmpeg → 16kHz mono WAV
        ▼
faster-whisper (local transcription)
        │  transcript + detected language
        ▼
Groq chat completion (summarization)
        ▼
summary + key points + action items + tone
```

## Features

- 🇵🇰 Handles Urdu-English code-switched speech, with auto language detection
- 📝 2-3 sentence summary in plain English, regardless of input language
- 🔑 Extracts key points and action items automatically
- 🎭 Detects tone (casual / urgent / formal / emotional / informational)
- 🖥️ Two interfaces: a scriptable CLI and a drag-and-drop Streamlit web UI
- 💸 Free to run — Whisper runs entirely locally, Groq's free tier covers generous daily usage

## Prerequisites

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) available on your `PATH`
- A free [Groq API key](https://console.groq.com/keys) (no credit card required)

## Installation

**1. Install ffmpeg**

```bash
# Windows
winget install ffmpeg
# Ubuntu/Debian
sudo apt install ffmpeg
# macOS
brew install ffmpeg
```

**2. Install Python dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure your API key**

```bash
cp .env.example .env
# then paste your Groq API key into .env
```

## Configuration

Set these in `.env` (see [`.env.example`](.env.example)):

| Variable        | Required | Default                      | Description                                                              |
| --------------- | :------: | ----------------------------- | -------------------------------------------------------------------------- |
| `GROQ_API_KEY`  |    ✅    | —                              | Your Groq API key, from [console.groq.com/keys](https://console.groq.com/keys). |
| `GROQ_MODEL`    |          | `llama-3.3-70b-versatile`     | Groq chat model used for summarization.                                    |
| `WHISPER_MODEL` |          | `small`                       | faster-whisper model size: `tiny`, `base`, `small`, or `medium`.           |

## Usage

### CLI

```bash
python main.py voicenote.ogg
python main.py voicenote.ogg --show-transcript
python main.py voicenote.ogg --language ur   # force Urdu if auto-detect struggles
```

### Web UI

```bash
streamlit run app.py
```

Drag and drop a voice note to see the transcript and summary side by side.

## Deploy on Hugging Face Spaces

This project runs out of the box as a Streamlit Space.

1. Create a new Space on Hugging Face and choose the **Streamlit** SDK.
2. Push this repository to the Space.
3. Add `GROQ_API_KEY` under the Space's secrets/settings panel.
4. Keep [`packages.txt`](packages.txt) in the repo so Hugging Face installs `ffmpeg`.

Recommended Space settings:

- SDK: Streamlit
- Python version: 3.10 or newer
- App file: `app.py`

If the Space feels slow on CPU, set `WHISPER_MODEL=base` or `WHISPER_MODEL=tiny` in the Space's environment variables.

## Project structure

```
.
├── app.py             # Streamlit web UI
├── main.py             # CLI entry point
├── transcriber.py       # ffmpeg conversion + faster-whisper transcription
├── summarizer.py         # Groq-based summarization
├── requirements.txt       # Python dependencies
├── packages.txt            # system packages for Hugging Face Spaces (ffmpeg)
└── .env.example              # environment variable template
```

## Notes on accuracy

- The default Whisper model is `small` — a good speed/accuracy balance on CPU. If Urdu
  accuracy is weak, set `WHISPER_MODEL=medium` in `.env` (slower but noticeably better).
- The first run downloads the Whisper model (~460MB for `small`); it's cached afterward.
- Voice activity detection (`vad_filter=True`) skips silences, which meaningfully speeds up
  typical voice notes.

## Roadmap

- [ ] Telegram bot — forward a voice note, get a summary back
- [ ] Batch mode — summarize a folder of notes
- [ ] Roman Urdu normalization pass

## License

Released under the [MIT License](LICENSE).
