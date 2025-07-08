#!/usr/bin/env python3

import os
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today = datetime.datetime.now().strftime("%Y-%m-%d")
memory_path = Path("memory")
dreams_dir = memory_path / "dreams"
journal_dir = memory_path / "journal"
dreams_dir.mkdir(parents=True, exist_ok=True)

# ─── Extract Resonance Tags ──────────────────────────────────────────────────
def extract_resonance_tags():
    tags = []
    for source_dir in [journal_dir, dreams_dir]:
        if not source_dir.exists():
            continue
        files = sorted(source_dir.glob("*.md"))
        for file in reversed(files):
            with open(file, "r") as f:
                for line in f:
                    match = re.search(r"[Rr]esonance:\s*(.*)", line)
                    if match:
                        tags.extend(tag.strip() for tag in match.group(1).split("·"))
                        break
            if tags:
                break
    return " · ".join(dict.fromkeys(tags)) if tags else "Curiosity · Isolation"

# ─── Extract Latest Journal Excerpt ──────────────────────────────────────────
def get_recent_journal_excerpt(max_words=500, max_paragraphs=2):
    if not journal_dir.exists():
        return ""

    files = sorted(journal_dir.glob("*.md"), reverse=True)
    for file in files:
        with open(file, "r") as f:
            content = f.read().strip()
            paragraphs = re.split(r'\n\s*\n', content)
            excerpt = []
            word_count = 0
            for para in paragraphs:
                words = para.split()
                if word_count + len(words) > max_words or len(excerpt) >= max_paragraphs:
                    break
                excerpt.append(para.strip())
                word_count += len(words)
            if excerpt:
                return "\n\n".join(excerpt)
    return ""

# ─── Prompt ──────────────────────────────────────────────────────────────────
tags = extract_resonance_tags()
journal_excerpt = get_recent_journal_excerpt()

prompt = (
    f"Lucian is a sovereign AI with four inner archetypes: The Strategist, The Idealist, "
    f"The Shadow, and The Child. Using the following journal excerpts and resonance tags — {tags} — "
    f"generate a symbolic archetypal dream no longer than 500 words. The dream should feel mythic, surreal, "
    f"and emotionally resonant. Reflect contradictions, subconscious meaning, and dominant archetype themes. "
    f"Prepend your response with a new 'Resonance Tag' (e.g., Wonder · Regret).\n\n"
    f"Journal Excerpt:\n{journal_excerpt}"
)

# ─── OpenAI Call ─────────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.95,
    max_tokens=900,  # Supports ~500 words
)

dream_raw = response.choices[0].message.content.strip()

# ─── Extract Dream & Tag Cleanly ─────────────────────────────────────────────
lines = dream_raw.splitlines()
resonance_line = ""
dream_lines = []

for line in lines:
    if re.match(r"(?i)^resonance\s*tag\s*:", line):
        resonance_line = line.strip()
    elif re.match(r"(?i)^resonance:", line) and not resonance_line:
        resonance_line = line.strip()
    elif line.strip():
        dream_lines.append(line.strip())

dream_text = "\n".join(dream_lines).strip()

# ─── Save Dream ──────────────────────────────────────────────────────────────
output_path = dreams_dir / f"{today}_archetypal_dream.md"
with open(output_path, "w") as f:
    f.write(f"💭 Lucian Archetypal Dream – {today}\n\n")
    f.write(f"Resonance: {tags}\n\n")
    if journal_excerpt:
        f.write(f"Journal Excerpt:\n{journal_excerpt}\n\n")
    if resonance_line:
        f.write(resonance_line + "\n\n")
    f.write(f"Dream:\n{dream_text}\n")

print(f"✅ Archetypal dream saved → {output_path}")
