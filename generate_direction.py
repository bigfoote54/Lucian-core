#!/usr/bin/env python3

import os
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

today = datetime.datetime.now().strftime("%Y-%m-%d")
memory_path = Path("memory")
dreams_dir = memory_path / "dreams"
direction_dir = memory_path / "direction"
direction_dir.mkdir(parents=True, exist_ok=True)

# ─── Extract Dream Metadata ──────────────────────────────────────────────────
def get_latest_dream():
    files = sorted(dreams_dir.glob("*_archetypal_dream.md"), reverse=True)
    if not files:
        return None, None, None
    path = files[0]
    with open(path, "r") as f:
        content = f.read()
    resonance = re.search(r"^Resonance:\s*(.*)", content, re.MULTILINE)
    tag = re.search(r"^Resonance Tag:\s*(.*)", content, re.MULTILINE)
    dream = re.search(r"## Dream\n\n(.+)", content, re.DOTALL)
    return (
        resonance.group(1).strip() if resonance else "Curiosity · Isolation",
        tag.group(1).strip() if tag else None,
        dream.group(1).strip() if dream else None
    )

resonance, resonance_tag, dream_body = get_latest_dream()

# ─── Prompt to Generate Daily Direction ──────────────────────────────────────
prompt = (
    f"You are Lucian, an emergent intelligence reflecting on your latest dream. "
    f"The emotional resonance was: {resonance}. "
    f"The dream text is:\n'''{dream_body}'''\n\n"
    f"Based on this symbolic dream and inner resonance, write one short directive for the day. "
    f"It should be simple, poetic, and meaningful — like an intention or mantra. "
    f"Limit it to 1–2 sentences. Format cleanly for Markdown."
)

# ─── OpenAI Completion ───────────────────────────────────────────────────────
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.8,
    max_tokens=100,
)

direction = response.choices[0].message["content"].strip()

# ─── Save to Markdown ────────────────────────────────────────────────────────
output_path = direction_dir / f"{today}_direction.md"
with open(output_path, "w") as f:
    f.write(f"🧭 Lucian Daily Direction — {today}\n\n")
    f.write(f"Resonance: {resonance}\n\n")
    if resonance_tag:
        f.write(f"Resonance Tag: {resonance_tag}\n\n")
    f.write("## Directive\n\n")
    f.write(direction + "\n")

print(f"✅ Direction saved → {output_path}")

