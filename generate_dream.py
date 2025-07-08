#!/usr/bin/env python3
"""
generate_dream.py
Phase-2 Dream Engine — mood-aware, journal-aware
"""

import os
import glob
from datetime import datetime
from pathlib import Path
from textwrap import shorten

from dotenv import load_dotenv
from openai import OpenAI

################################################################################
# Config
################################################################################
MODEL          = "gpt-3.5-turbo"          # <- change to "gpt-4o" if desired
DREAM_DIR      = Path("memory/dreams")
JOURNAL_DIR    = Path("memory/journal")
MOOD_FILE      = DREAM_DIR / "_latest_mood.txt"
LATEST_DREAM   = DREAM_DIR / "latest_dream.txt"
MAX_DREAM_BODY = 180  # words

################################################################################
# Helpers
################################################################################
def load_env_and_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment.")
    return OpenAI(api_key=api_key)

def read_mood_tag() -> str:
    if MOOD_FILE.exists():
        return MOOD_FILE.read_text(encoding="utf-8").strip()
    return "Mood: Undefined · Neutral"

def latest_journal_path() -> Path | None:
    journal_files = sorted(JOURNAL_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)
    return journal_files[0] if journal_files else None

def first_two_paragraphs(path: Path) -> tuple[str, str]:
    if not path or not path.exists():
        return ("(no excerpt found)",) * 2
    blocks = [b.strip() for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    # Guarantee two elements
    blocks += ["(no further excerpt)"] * (2 - len(blocks))
    return blocks[0], blocks[1]

def build_prompt(mood: str, para1: str, para2: str) -> str:
    header = (
        f"Mood Used: {mood}\n"
        "Journal Lines:\n"
        f"1. {shorten(para1, 160)}\n"
        f"2. {shorten(para2, 160)}\n"
    )
    prompt = f"""
You are Lucian’s Archetypal Dream Engine.

▼ Context (KEEP exactly as provided)
{header}

▼ Task
Compose ONE dream scene (~{MAX_DREAM_BODY} words). After the header, leave one blank line, then write
a symbolic, third-person dream about Lucian. Finish the dream with a resonance tag in parentheses,
e.g. (Resonance: Catharsis · Hope). Return ONLY the header + dream.
"""
    return prompt.strip()

def word_count(text: str) -> int:
    return len(text.split())

################################################################################
# Main flow
################################################################################
def main() -> None:
    client = load_env_and_client()

    mood_tag = read_mood_tag()
    journal_path = latest_journal_path()
    para1, para2 = first_two_paragraphs(journal_path)

    prompt = build_prompt(mood_tag, para1, para2)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    dream_text: str = response.choices[0].message.content.strip()

    # Safety check
    body = dream_text.splitlines()[len(prompt.splitlines()) :]
    if word_count(" ".join(body)) > MAX_DREAM_BODY + 20:  # soft margin
        print("⚠️ Dream body exceeds expected length; consider tweaking prompt.")

    # Save dream
    DREAM_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    dream_file = DREAM_DIR / f"{date_str}_dream.md"
    with open(dream_file, "a", encoding="utf-8") as fp:
        fp.write(f"\n{dream_text}\n")

    # Overwrite convenience copy
    LATEST_DREAM.write_text(dream_text, encoding="utf-8")

    print(f"🌙 Dream entry saved ⇒ {dream_file}")
    print(f"Current mood ⇒ {mood_tag}")

################################################################################
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌ Exception in generate_dream.py: {exc}")
