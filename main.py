"""
main.py
CLI entry point.

Usage:
    python main.py path/to/voicenote.ogg
    python main.py note.ogg --show-transcript
    python main.py note.ogg --language ur
"""

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()  # loads GEMINI_API_KEY from .env if present

from transcriber import transcribe   # noqa: E402
from summarizer import summarize     # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Summarize a voice note (Urdu/English mixed supported)")
    parser.add_argument("audio", help="path to audio file (.ogg, .mp3, .m4a, .wav ...)")
    parser.add_argument("--show-transcript", action="store_true", help="print full transcript")
    parser.add_argument("--language", default=None, help="force language code (ur/en). default: auto-detect")
    args = parser.parse_args()

    print(f"\n🎙️  Transcribing: {args.audio}")
    result = transcribe(args.audio, language=args.language)
    print(f"   language={result['language']} (conf {result['language_probability']}) | {result['duration']}s")

    if args.show_transcript:
        print("\n--- TRANSCRIPT ---")
        print(result["text"])
        print("------------------")

    print("\n🤖 Summarizing with Gemini...")
    summary = summarize(result["text"])

    print("\n" + "=" * 50)
    print("📝 SUMMARY")
    print("=" * 50)
    print(summary.get("summary", ""))

    key_points = summary.get("key_points") or []
    if key_points:
        print("\n🔑 Key points:")
        for p in key_points:
            print(f"  • {p}")

    actions = summary.get("action_items") or []
    if actions:
        print("\n✅ Action items:")
        for a in actions:
            print(f"  [ ] {a}")

    print(f"\n🎭 Tone: {summary.get('tone', 'n/a')}")
    print()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"\n❌ {e}", file=sys.stderr)
        sys.exit(1)
