#!/usr/bin/env python3
"""
Uses the latest mood tag + the last two journal paragraphs to craft a
symbolic dream.  Saves dream to memory/dreams/<date>_dream.md and logs the
mood used.
"""

import os, glob, pathlib, textwrap
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# ── config ──────────────────────────────────────────────────────────────────────
JOURNAL_DIR   = pathlib.Path("memory/journal")
DREAM_DIR     = pathlib.Path("memory/dreams")
MOOD_FILE     = DREAM_DIR / "_latest_mood.txt"
MODEL         = "gpt-4"
MAX_WORDS     = 160            # soft cap for dream narrative

# ── init ────────────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise RuntimeError("OPENAI_API_KEY not found in environment / secrets")

# ── helpers ─────────────────────────────────────────────────────────────────────
def latest_journal_path() -> pathlib.Path | None:
    files = sorted(JOURNAL_DIR.glob("*_journal.md"))
    return files[-1] if files else None

def last_two_paragraphs(path: pathlib.Path) -> str:
    if not path or not path.exists():
        return "_No recent journal paragraphs found._"
    paras = [p.strip() for p in path.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    return "\n\n".join(paras[-2:])

def build_prompt(mood: str, seeds: str) -> str:
    return textwrap.dedent(f"""
        {mood}

        Journal fragments:
        ---
        {seeds}
        ---

        Using the mood and fragments above, write a SYMBOLIC DREAM scene (≈150 words).
        • Surreal imagery, clear narrative arc, third-person present tense.
        • Conclude with a line starting exactly: Resonance: <Tag1> · <Tag2>
    """).strip()

def generate_dream_text(prompt: str) -> str:
    resp = client.chat.completions.create(
        model   = MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()

def save_dream(mood: str, seeds: str, dream_body: str):
    DREAM_DIR.mkdir(parents=True, exist_ok=True)
    path = DREAM_DIR / f"{datetime.now():%Y-%m-%d}_dream.md"

    doc = f"""### Dream – {datetime.now():%Y-%m-%d}

{mood}

> **Journal fragments used**  
{seeds.replace('\n', '\n> ')}

{dream_body}
"""
    path.write_text(doc, encoding="utf-8")
    print(f"🌌 Dream saved → {path}")

# ── main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mood = MOOD_FILE.read_text(encoding="utf-8").strip() if MOOD_FILE.exists() else "Mood: Undefined · Neutral"
    seeds_path = latest_journal_path()
    seeds      = last_two_paragraphs(seeds_path)

    prompt = build_prompt(mood, seeds)
    dream  = generate_dream_text(prompt)
    save_dream(mood, seeds, dream)
