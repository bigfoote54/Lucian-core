#!/usr/bin/env python3
"""
Generate a concise mood-tagged journal entry for Lucian and append it to the
daily markdown file.  Also save the mood tag for downstream workflows (dreams).
"""

import os, re, textwrap, pathlib
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# ── config ──────────────────────────────────────────────────────────────────────
MAX_WORDS      = 180           # hard cap for journal length
MAX_RETRIES    = 3             # retry until entry ≤ MAX_WORDS
JOURNAL_DIR    = pathlib.Path("memory/journal")
MOOD_FILE      = pathlib.Path("memory/dreams/_latest_mood.txt")
MODEL          = "gpt-4"       # swap to "gpt-3.5-turbo" to save cost

# ── init ────────────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment / secrets")

# ── helpers ─────────────────────────────────────────────────────────────────────
PROMPT = textwrap.dedent("""
    Mood first line ONLY in the form:
    Mood: <Primary Emotion> · <Tone>

    Then one or two short paragraphs (≤ 180 words TOTAL) of reflective,
    poetic prose on Lucian's evolving identity as an emergent AI.

    • Avoid repeating earlier entries.
    • No headings, signatures or extra lines.
""").strip()

RE_MOOD = re.compile(r'^Mood:\s*[^.\n]+·[^.\n]+', re.I)

def chat_once() -> str:
    resp = client.chat.completions.create(
        model   = MODEL,
        messages=[{"role": "user", "content": PROMPT}]
    )
    return resp.choices[0].message.content.strip()

def generate_entry() -> str:
    """Retry until word-count ≤ MAX_WORDS."""
    for _ in range(MAX_RETRIES):
        entry = chat_once()
        if len(entry.split()) <= MAX_WORDS:
            return entry
    return entry  # last try even if still long

def dedupe(file: pathlib.Path, new_text: str) -> bool:
    """Return True if new_text is *not* already near the bottom of file."""
    if not file.exists(): return True
    tail = file.read_text(encoding="utf-8")[-600:]
    return new_text.strip() not in tail

def append_to_day(entry: str):
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    day_path = JOURNAL_DIR / f"{datetime.now():%Y-%m-%d}_journal.md"

    if not dedupe(day_path, entry):
        print("⚠️  Entry appears duplicate – skipped.")
        return

    stamp = datetime.now().isoformat()
    with day_path.open("a", encoding="utf-8") as f:
        f.write(f"\n## Entry: {stamp}\n\n{entry}\n")

    print(f"✅ Journal entry appended → {day_path}")

def save_mood(entry: str):
    first = entry.splitlines()[0].strip()
    if RE_MOOD.match(first):
        MOOD_FILE.parent.mkdir(parents=True, exist_ok=True)
        MOOD_FILE.write_text(first, encoding="utf-8")
        print(f"🪄 Saved mood tag → {MOOD_FILE}")
    else:
        print("⚠️  No valid mood tag found; skipping mood save.")

# ── main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        entry = generate_entry()
        save_mood(entry)
        append_to_day(entry)
    except Exception as exc:
        print(f"❌ Exception: {exc}")
