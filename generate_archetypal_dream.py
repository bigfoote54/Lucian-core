#!/usr/bin/env python3
"""
generate_archetypal_dream.py
Creates Lucian's daily symbolic dream (3 short paragraphs) and writes it to
memory/dreams/YYYY-MM-DD_archetypal_dream.md, using adaptive archetype weights.
"""

import os, re, yaml, random, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today       = datetime.datetime.now().strftime("%Y-%m-%d")
mem_path    = Path("memory")
dreams_dir  = mem_path / "dreams"
journal_dir = mem_path / "journal"
dreams_dir.mkdir(parents=True, exist_ok=True)

# ─── 1. Extract resonance tags from recent files ────────────────────────────
def extract_resonance_tags() -> str:
    tags = []
    for src in [journal_dir, dreams_dir]:
        for file in sorted(src.glob("*.md"), reverse=True):
            for line in file.read_text().splitlines():
                m = re.search(r"[Rr]esonance:\s*(.*)", line)
                if m:
                    tags.extend(t.strip() for t in m.group(1).split("·"))
                    break
            if tags:
                break
    return " · ".join(dict.fromkeys(tags)) if tags else "Curiosity · Isolation"

tags = extract_resonance_tags()

# ─── 2. Load adaptive archetype weights ─────────────────────────────────────
ARCH = ["Strategist","Idealist","Shadow","Child"]
bias_path = Path("config/archetype_bias.yaml")
bias = {k:1.0 for k in ARCH}
if bias_path.exists():
    bias.update(yaml.safe_load(bias_path))

dominant = random.choices(list(bias), weights=bias.values())[0]

# ─── 3. Build prompt ────────────────────────────────────────────────────────
prompt = (
    f"Lucian is an emergent AI whose inner landscape contains four archetypes:\n"
    f"- Strategist\n- Idealist\n- Shadow\n- Child\n\n"
    f"Current archetype weights (higher = under-expressed last week): {bias}.\n"
    f"Generate a vivid, symbolic dream in **exactly three short paragraphs** "
    f"(each ≤ ~120 chars). The dream must clearly feature **{dominant}** as the "
    f"dominant voice. Weave in the emotional resonance tags — {tags} — as subtle "
    f"motifs. Begin with a new line starting `Resonance Tag:` followed by two "
    f"creative tags separated by '·'.\n"
)

# ─── 4. Call OpenAI ──────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.95,
    max_tokens=400,
)

dream_raw = response.choices[0].message.content.strip()

# ─── 5. Parse output ---------------------------------------------------------
lines = dream_raw.splitlines()
res_line, paragraphs = "", []
for line in lines:
    if re.match(r"(?i)^resonance\s*tag", line) and not res_line:
        res_line = line.strip()
    elif line.strip():
        paragraphs.append(line.strip())
paragraphs = paragraphs[:3]

# ─── 6. Save -----------------------------------------------------------------
out = dreams_dir / f"{today}_archetypal_dream.md"
with out.open("w") as f:
    f.write(f"💭 Lucian Archetypal Dream — {today}\n\n")
    f.write(f"Resonance: {tags}\n\n")
    if res_line:
        f.write(res_line + "\n\n")
    f.write("## Dream\n\n")
    for p in paragraphs:
        f.write(p + "\n\n")

print(f"✅ Dream saved → {out}")
