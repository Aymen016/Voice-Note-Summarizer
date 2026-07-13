"""
summarizer.py
Sends a transcript to Gemini (free tier) and returns a structured summary.
Handles Urdu-English mixed transcripts - output is always in English.
"""

import os
import json

import google.generativeai as genai

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

PROMPT_TEMPLATE = """You are a voice note summarizer. The transcript below may mix Urdu and English (code-switched), and Urdu may appear in Urdu script or roman Urdu.

Respond ONLY with valid JSON, no markdown fences, in this exact shape:
{{
  "summary": "2-3 sentence summary in plain English",
  "action_items": ["list of action items, empty list if none"],
  "tone": "one word: casual / urgent / formal / emotional / informational",
  "key_points": ["2-4 short bullet points"]
}}

Transcript:
\"\"\"{transcript}\"\"\"
"""


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set.\n"
            "Get a free key at https://aistudio.google.com/apikey then:\n"
            "  export GEMINI_API_KEY=your_key_here   (Linux/macOS)\n"
            "  set GEMINI_API_KEY=your_key_here      (Windows cmd)\n"
            "Or put it in a .env file."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def summarize(transcript: str) -> dict:
    """
    Summarize a transcript. Returns dict with summary, action_items, tone, key_points.
    Falls back to raw text in 'summary' if JSON parsing fails.
    """
    if not transcript.strip():
        return {
            "summary": "(empty transcript - no speech detected)",
            "action_items": [],
            "tone": "n/a",
            "key_points": [],
        }

    model = get_client()
    response = model.generate_content(PROMPT_TEMPLATE.format(transcript=transcript))
    raw = response.text.strip()

    # strip markdown fences if the model added them anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "summary": raw,
            "action_items": [],
            "tone": "unknown",
            "key_points": [],
        }


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Yaar meeting kal 3 baje hai, please slides ready kar lena and send me the file before lunch."
    print(json.dumps(summarize(text), indent=2, ensure_ascii=False))
