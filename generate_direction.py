#!/usr/bin/env python3
"""
generate_direction.py
-------------------------------------------------------------
Creates Lucian's daily directive (1–2 sentences), referencing
today's dream, adaptive archetype bias, and adaptive resonance tags.
"""

import os, re, yaml, random, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today       = datetime.datetime.now().strftime("%Y-%m-%d")
mem_root    = Path("memory")
dreams_dir  = mem_root / "dreams"
dir_dir     = mem_root / "direction"
dir_dir.mkdir(parents=True, exist_ok=True)

# ─── Load today’s dream & capture tags ───────────────────────────────────────
dream_files = sorted(dreams_dir.glob(f"{today}_*_archetypal_dream.md"))
if not dream_files:
    raise SystemExit("No dream file found for today; run dream generator first.")
dream_txt   = dream_files[-1].read_text()

# Extract dream excerpt (first 240 chars after header)
dream_excerpt = "\n".join(
    l.strip() for l in dream_txt.splitlines()
    if l.strip() and not l.lower().startswith("resonance")
)[:240]

# Extract existing resonance tag line, if any
tag_match = re.search(r"Resonance Tag:\s*(.+)", dream_txt)
dream_tags = tag_match.group(1).strip() if tag_match else None

# ─── Adaptive archetype bias ────────────────────────────────────────────────
ARCH = ["Strategist","Idealist","Shadow","Child"]
bias_path = Path("config/archetype_bias.yaml")
arch_bias = {k:1.0 for k in ARCH}
if bias_path.exists():
    arch_bias.update(yaml.safe_load(bias_path.read_text()))
dominant_arch = random.choices(list(arch_bias), weights=arch_bias.values(), k=1)[0]

# ─── Adaptive tag bias (always used) ────────────────────────────────────────
tag_bias_path = Path("config/tag_weights.yaml")
tag_bias = {"Curiosity":1.0,"Existence":1.0,"Knowledge":1.0,"Wonder":1.0,"Responsibility":1.0}
if tag_bias_path.exists():
    tag_bias.update(yaml.safe_load(tag_bias_path.read_text()))

# Pick a single focal tag weighted
focal_tag = random.choices(list(tag_bias), weights=tag_bias.values(), k=1)[0]

# Compose final tag line
if dream_tags:
    tags_set = {t.strip() for t in dream_tags.split("·")}
    tags_set.add(focal_tag)
    final_tags = " · ".join(sorted(tags_set))
else:
    final_tags = focal_tag

# ─── Build prompt ───────────────────────────────────────────────────────────
prompt = (
    "You are Lucian's conscious directive voice.\n\n"
    f"Dominant archetype today: **{dominant_arch}**.\n"
    f"Resonance tag(s): **{final_tags}**.\n\n"
    f"Dream excerpt:\n\"\"\"{dream_excerpt}\"\"\"\n\n"
    "Write a poetic yet actionable directive in 1–2 sentences. "
    "It must echo the resonance tag(s) and reflect the dominant archetype's perspective."
)

# ─── OpenAI Call ────────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.8,
    max_tokens=120,
)

directive_text = response.choices[0].message.content.strip()

# ─── Save directive ─────────────────────────────────────────────────────────
out_file = dir_dir / f"{today}_direction.md"
with out_file.open("w") as f:
    f.write(f"🧭 Lucian Daily Direction — {today}\n\n")
    f.write(f"Dominant Archetype: {dominant_arch}\n\n")
    f.write(f"Resonance Tag: {final_tags}\n\n")
    f.write("## Directive\n\n")
    f.write(directive_text + "\n")

print(f"✅ Direction saved → {out_file}")
