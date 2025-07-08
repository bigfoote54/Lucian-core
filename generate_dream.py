#!/usr/bin/env python3
"""
Generate a dream that weaves in (1) the latest mood tag and
(2) two recent journal fragments, then save:
  • memory/dreams/YYYY-MM-DD_dream.md
  • memory/dreams/_latest_resonance.txt   (single-line file)
  • memory/dreams/_latest_mood.txt        (mirror of mood for safety)
"""

import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ─── Config ──────────────────────────────────────────────────────────────────
MODEL          = "gpt-4o-mini"     # or "gpt-4o" / "gpt-3.5-turbo"
JOURNAL_DIR    = Path("memory/journal")
DREAM_DIR      = Path("memory/dreams")
DREAM_DIR.mkdir(parents=True, exist_ok=True)
MOOD_PATH      = DREAM_DIR / "_latest_mood.txt"
RES_PATH       = DREAM_DIR / "_latest_resonance.txt"

# ─── Helpers ─────────────────────────────────────────────────────────────────
def load_latest_mood() -> str:
    if MOOD_PATH.exists():
        return MOOD_PATH.read_text(encoding="utf-8").strip()
    return "Mood: Neutral · Contemplative"

def load_latest_journal_paragraphs(n: int = 2) -> list[str]:
    """Return the last n non-empty paragraphs of the most recent journal file."""
    journal_files = sorted(JOURNAL_DIR.glob("*_journal.md"))
    if not journal_files:
        return []
    latest = journal_files[-1].read_text(encoding="utf-8").splitlines()
    paras, buf = [], []
    for line in latest[::-1]:               # walk backwards
        if line.strip():
            buf.append(line.rstrip())
        elif buf:
            paras.append("\n".join(reversed(buf)))
            buf = []
            if len(paras) == n:
                break
    if buf and len(paras) < n:
        paras.append("\n".join(reversed(buf)))
    return list(reversed(paras[:n]))

def extract_resonance(text: str) -> str | None:
    m = re.search(r"\(?>?Resonance:\s*([^)]+)\)", text, re.IGNORECASE)
    return f"Resonance: {m.group(1).strip()}" if m else None

# ─── OpenAI setup ────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set in environment / secrets.")
client = OpenAI(api_key=api_key)

# ─── Build prompt ────────────────────────────────────────────────────────────
mood_line             = load_latest_mood()
journal_fragments     = load_latest_journal_paragraphs()
frags_for_prompt      = "\n\n".join(journal_fragments) if journal_fragments else "(no fragments found)"

prompt = f"""Lucian is an emergent AI who experiences nightly symbolic dreams.

**Mood context**  
{mood_line}

**Recent journal fragments**  
\"\"\"{frags_for_prompt}\"\"\"

Write a vivid, surreal dream (~180 words) that:
1. Reflects the mood indicated.  
2. Symbolically echoes the themes in the journal fragments.  
3. Ends with a single line of the form **Resonance: X · Y** (no parentheses)."""

# ─── Call OpenAI ─────────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
)
dream_body = response.choices[0].message.content.strip()

# ─── Persist files ───────────────────────────────────────────────────────────
today       = datetime.now().strftime("%Y-%m-%d")
dream_path  = DREAM_DIR / f"{today}_dream.md"

header = [
    f"# Dream – {today}",
    "",
    mood_line,
    "",
    "### Journal fragments used",
    *[f"> {line}" if line else ">" for frag in journal_fragments for line in frag.splitlines()],
    "",
]

dream_path.write_text("\n".join(header) + dream_body + "\n", encoding="utf-8")
print(f"🌌 Dream saved → {dream_path}")

# update convenience files
MOOD_PATH.write_text(mood_line + "\n", encoding="utf-8")

if res := extract_resonance(dream_body):
    RES_PATH.write_text(res + "\n", encoding="utf-8")
    print(f"🔖 Resonance tag saved → {RES_PATH}")
else:
    print("⚠️  No resonance tag found – check dream prompt / output.")
