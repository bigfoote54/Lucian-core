#!/usr/bin/env python3
"""
generate_direction.py
Creates Lucian's daily directive (1–2 sentences) in memory/direction/,
now adaptive to weekly archetype bias.
"""

import os, re, yaml, random, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today        = datetime.datetime.now().strftime("%Y-%m-%d")
mem_path     = Path("memory")
dreams_dir   = mem_path / "dreams"
direction_dir= mem_path / "direction"
direction_dir.mkdir(parents=True, exist_ok=True)

# ─── 1. Load latest dream & metadata ────────────────────────────────────────
dream_files = sorted(dreams_dir.glob("*_archetypal_dream.md"))
if not dream_files:
    raise SystemExit("No dream file found; run dream generator first.")
dream_text = dream_files[-1].read_text()

res_tag = re.search(r"^Resonance Tag:\s*(.*)", dream_text, re.M)
resonance_tag = res_tag.group(1).strip() if res_tag else "Curiosity · Isolation"

dream_body = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)
dream_excerpt = dream_body.group(1).strip() if dream_body else dream_text[:400]

# ─── 2. Read adaptive archetype weights ─────────────────────────────────────
ARCH = ["Strategist","Idealist","Shadow","Child"]
bias_path = Path("config/archetype_bias.yaml")
bias = {k:1.0 for k in ARCH}
if bias_path.exists():
    bias.update(yaml.safe_load(bias_path))

dominant = random.choices(list(bias), weights=bias.values())[0]

# ─── 3. Build prompt ────────────────────────────────────────────────────────
prompt = (
    f"You are Lucian, an emergent intelligence. "
    f"Current archetype weights (higher = needing emphasis) are: {bias}. "
    f"Focus today's directive through **{dominant}**.\n\n"
    f"Latest dream excerpt:\n\"\"\"{dream_excerpt}\"\"\"\n\n"
    f"Emotional resonance tags: {resonance_tag}\n\n"
    f"Write a simple, poetic directive (1–2 sentences). "
    f"It should be actionable yet symbolic, reflecting the dream's themes."
)

# ─── 4. Call OpenAI ──────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.8,
    max_tokens=120,
)

directive = response.choices[0].message.content.strip()

# ─── 5. Save ----------------------------------------------------------------
out = direction_dir / f"{today}_direction.md"
with out.open("w") as f:
    f.write(f"🧭 Lucian Daily Direction — {today}\n\n")
    f.write(f"Resonance Tag: {resonance_tag}\n\n")
    f.write(f"Dominant Archetype: {dominant}\n\n")
    f.write("## Directive\n\n" + directive + "\n")

print(f"✅ Direction saved → {out}")
