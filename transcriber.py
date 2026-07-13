"""
transcriber.py
Converts audio (ogg/mp3/m4a/wav) to 16kHz mono WAV via ffmpeg,
then transcribes with faster-whisper. Handles Urdu-English code-switched speech.
"""

import subprocess
import tempfile
import os
from pathlib import Path

from faster_whisper import WhisperModel

# Model size tradeoffs (CPU):
#   tiny/base  -> fast, weak on Urdu
#   small      -> good default, decent code-switching
#   medium     -> better Urdu accuracy, ~2-3x slower
MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")

_model = None


def get_model() -> WhisperModel:
    """Lazy-load the whisper model (downloads on first run, then cached)."""
    global _model
    if _model is None:
        print(f"[transcriber] loading faster-whisper '{MODEL_SIZE}' (first run downloads the model)...")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def convert_to_wav(input_path: str) -> str:
    """Convert any audio file to 16kHz mono WAV using ffmpeg."""
    input_path = str(Path(input_path).resolve())
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-loglevel", "error",
        tmp.name,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Install it first:\n"
            "  Windows: winget install ffmpeg  (or choco install ffmpeg)\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  macOS:   brew install ffmpeg"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed to convert '{input_path}':\n{e.stderr}")

    return tmp.name


def transcribe(audio_path: str, language: str | None = None) -> dict:
    """
    Transcribe an audio file.

    Args:
        audio_path: path to any audio file (ogg, mp3, m4a, wav...)
        language: force a language code ('ur', 'en') or None for auto-detect.
                  For Urdu-English mixed notes, auto-detect usually works best.

    Returns:
        dict with 'text', 'language', 'language_probability', 'duration'
    """
    wav_path = convert_to_wav(audio_path)
    try:
        model = get_model()
        segments, info = model.transcribe(
            wav_path,
            language=language,
            vad_filter=True,          # skip silences - big speedup on voice notes
            beam_size=5,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return {
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "duration": round(info.duration, 1),
        }
    finally:
        os.unlink(wav_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python transcriber.py <audio_file>")
        sys.exit(1)
    result = transcribe(sys.argv[1])
    print(f"\nDetected language: {result['language']} ({result['language_probability']})")
    print(f"Duration: {result['duration']}s\n")
    print(result["text"])
