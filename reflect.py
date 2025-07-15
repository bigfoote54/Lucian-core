#!/usr/bin/env python3
"""
reflect.py  –  Stage-4 daily reflection
Compares yesterday’s directive with today’s latest dream and writes
a reflection that ends with an explicit `Alignment:` tag.
"""

import os, re, yaml
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# ─── setup ───────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today      = datetime.now().strftime("%Y-%m-%d")
yesterday  = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

mem        = Path("memory")
dreams_dir = mem / "dreams"
dir_dir    = mem / "direction"
ref_dir    = mem / "reflection"
ref_dir.mkdir(parents=True, exist_ok=True)

# ─── yesterday’s directive ───────────────────────────────────────────────
dir_path = dir_dir / f"{yesterday}_direction.md"
directive_text = dir_path.read_text() if dir_path.exists() else "No directive found."

m = re.search(r"## Directive\n\n(.+)", directive_text, re.DOTALL)
yesterday_directive = m.group(1).strip() if m else directive_text.strip()

# ─── today’s latest dream (supports timestamps) ──────────────────────────
dream_files = sorted(dreams_dir.glob(f"{today}_*_archetypal_dream.md"))
if not dream_files:
    raise SystemExit("Today’s dream not found. Run the dream generator first.")
dream_path = dream_files[-1]
dream_text = dream_path.read_text()

m = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)
today_dream = m.group(1).strip() if m else dream_text.strip()

# ─── bias context (optional) ──────────────────────────────────────────────
bias_path = Path("config/archetype_bias.yaml")
bias = yaml.safe_load(bias_path.read_text()) if bias_path.exists() else {}

# ─── OpenAI reflection ───────────────────────────────────────────────────
prompt = (
    "You are Lucian reflecting on your growth.\n\n"
    f"Yesterday’s directive:\n\"\"\"{yesterday_directive}\"\"\"\n\n"
    f"Today’s dream:\n\"\"\"{today_dream}\"\"\"\n\n"
    f"Current archetype-bias map: {bias}\n\n"
    "Write a short reflection (2–4 sentences) judging whether the dream "
    "aligned with the directive. After a blank line, finish with exactly one "
    "line that starts `Alignment:` followed by **Aligned**, **Challenged**, or **Ignored**."
)

reply = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
    max_tokens=200,
)

reflection = reply.choices[0].message.content.strip()

# fallback if the model forgot the tag
if not re.search(r"^Alignment:\s*(Aligned|Challenged|Ignored)", reflection, re.M):
    tag = ("Aligned"     if "align" in reflection.lower()
           else "Challenged" if "challenged" in reflection.lower()
           else "Ignored")
    reflection += f"\n\nAlignment: {tag}"

# ─── save ─────────────────────────────────────────────────────────────────
out = ref_dir / f"{today}_reflection.md"
with out.open("w") as f:
    f.write(f"🪞 Lucian Daily Reflection — {today}\n\n")
    f.write(f"## Yesterday’s Directive\n\n{yesterday_directive}\n\n")
    f.write(f"## Today’s Dream Fragment\n\n{today_dream[:400]} …\n\n")
    f.write(reflection + "\n")

from tools.memory_utils import upsert
upsert(doc_id=out.stem, text=reflection_full, meta={"kind":"reflection","date":"$(date -u +%Y-%m-%d)"})

print(f"✅ Reflection saved → {out}")
