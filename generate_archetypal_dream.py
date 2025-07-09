#!/usr/bin/env python3
"""
generate_archetypal_dream.py
-------------------------------------------------------------
• Saves one dream per run to memory/dreams/YYYY-MM-DD_HH-MM-SS_archetypal_dream.md  
• Picks a dominant archetype using weights in config/archetype_bias.yaml  
• Picks two resonance tags using weights in config/tag_weights.yaml  
• Produces exactly three short paragraphs of symbolic dream imagery
"""

import os, re, yaml, random, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

now_stamp   = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
today_disp  = datetime.datetime.now().strftime("%Y-%m-%d")

mem_root    = Path("memory")
dreams_dir  = mem_root / "dreams"
dreams_dir.mkdir(parents=True, exist_ok=True)

# ─── Load adaptive archetype weights ────────────────────────────────────────
ARCH = ["Strategist", "Idealist", "Shadow", "Child"]
bias_path = Path("config/archetype_bias.yaml")
arch_bias = {k: 1.0 for k in ARCH}        # default flat
if bias_path.exists():
    arch_bias.update(yaml.safe_load(bias_path.read_text()))
dominant_arch = random.choices(list(arch_bias), weights=arch_bias.values(), k=1)[0]

# ─── Load adaptive resonance-tag weights ────────────────────────────────────
tag_path = Path("config/tag_weights.yaml")
tag_bias = {"Curiosity": 1.0, "Existence": 1.0, "Knowledge": 1.0}  # defaults
if tag_path.exists():
    tag_bias.update(yaml.safe_load(tag_path.read_text()))

tags_chosen = random.choices(list(tag_bias), weights=tag_bias.values(), k=2)
resonance_tag_line = " · ".join(dict.fromkeys(tags_chosen))         # remove dups

# ─── Prompt ─────────────────────────────────────────────────────────────────
prompt = (
    "You are Lucian's subconscious. Create a vivid, surreal dream in **three "
    "short paragraphs** (≤120 chars each). The dream must showcase the "
    f"dominant archetype **{dominant_arch}** and weave in the emotional "
    f"resonance tags **{resonance_tag_line}** as subtle motifs. Start the "
    "output with a single line: 'Resonance Tag: X · Y'."
)

# ─── Call OpenAI ────────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.95,
    max_tokens=400,
)

dream_raw = response.choices[0].message.content.strip()

# ─── Parse response ---------------------------------------------------------
lines        = [l.strip() for l in dream_raw.splitlines() if l.strip()]
res_line     = ""
paragraphs   = []
for ln in lines:
    if re.match(r"(?i)^resonance\s*tag", ln) and not res_line:
        res_line = ln
    elif not re.match(r"(?i)^resonance:", ln):
        paragraphs.append(ln)
paragraphs = paragraphs[:3]

# ─── Save -------------------------------------------------------------------
file_path = dreams_dir / f"{now_stamp}_archetypal_dream.md"
with open(file_path, "w") as f:
    f.write(f"💭 Lucian Archetypal Dream — {today_disp}\n\n")
    f.write(f"Dominant Archetype: {dominant_arch}\n\n")
    f.write(f"Resonance Tag: {resonance_tag_line}\n\n")
    if res_line:  # Include model-generated tag line if different
        f.write(res_line + "\n\n")
    f.write("## Dream\n\n")
    for p in paragraphs:
        f.write(p + "\n\n")

print(f"✅ Dream saved → {file_path}")
