#!/usr/bin/env python3
"""
reflect.py  —  Stage-4 daily reflection
Compares yesterday’s directive with today’s *latest* dream and writes a reflection
that ends with an `Alignment:` tag.  The text is also embedded into the local
vector store via tools.memory_utils.upsert().
"""

import os, re, yaml
from pathlib import Path
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from openai import OpenAI

# ─── setup ────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today      = datetime.now().strftime("%Y-%m-%d")
yesterday  = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

MEM_ROOT   = Path("memory")
dreams_dir = MEM_ROOT / "dreams"
dir_dir    = MEM_ROOT / "direction"
ref_dir    = MEM_ROOT / "reflection"
ref_dir.mkdir(parents=True, exist_ok=True)

# ─── yesterday’s directive ────────────────────────────────────────────────
dir_path = dir_dir / f"{yesterday}_direction.md"
directive_text = dir_path.read_text() if dir_path.exists() else "No directive found."

m = re.search(r"## Directive\n\n(.+)", directive_text, re.DOTALL)
yesterday_directive = m.group(1).strip() if m else directive_text.strip()

# ─── today’s latest dream (supports timestamps) ───────────────────────────
dream_files = sorted(dreams_dir.glob(f"{today}_*_archetypal_dream.md"))
if not dream_files:
    raise SystemExit("Today’s dream not found. Run the dream generator first.")

dream_text = dream_files[-1].read_text()
m = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)
today_dream = m.group(1).strip() if m else dream_text.strip()

# ─── bias context (optional) ───────────────────────────────────────────────
bias_path = Path("config/archetype_bias.yaml")
bias = yaml.safe_load(bias_path.read_text()) if bias_path.exists() else {}

# ─── build prompt & call OpenAI ────────────────────────────────────────────
prompt = (
    "You are Lucian reflecting on your growth.\n\n"
    f"Yesterday’s directive:\n\"\"\"{yesterday_directive}\"\"\"\n\n"
    f"Today’s dream:\n\"\"\"{today_dream}\"\"\"\n\n"
    f"Current archetype-bias map: {bias}\n\n"
    "Write a short reflection (2–4 sentences) judging whether the dream "
    "aligned with the directive.\n\n"
    "After a blank line finish with **exactly one line** that starts "
    "`Alignment:` followed by Aligned, Challenged, or Ignored."
)

reflection_full = ""   # ensure it always exists

try:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=200,
    )
    reflection_full = resp.choices[0].message.content.strip()
except Exception as err:
    # graceful fallback so downstream stages keep running
    reflection_full = f"⚠️ OpenAI error — {err}"

# add Alignment tag if missing
if not re.search(r"^Alignment:\s*(Aligned|Challenged|Ignored)", reflection_full, re.M):
    tag = ("Aligned"      if "align"     in reflection_full.lower()
           else "Challenged" if "challeng"  in reflection_full.lower()
           else "Ignored")
    reflection_full += f"\n\nAlignment: {tag}"

# ─── save markdown file ────────────────────────────────────────────────────
out = ref_dir / f"{today}_reflection.md"
with out.open("w") as f:
    f.write(f"🪞 Lucian Daily Reflection — {today}\n\n")
    f.write(f"## Yesterday’s Directive\n\n{yesterday_directive}\n\n")
    f.write(f"## Today’s Dream Fragment\n\n{today_dream[:400]} …\n\n")
    f.write(reflection_full + "\n")

print(f"✅ Reflection saved → {out}")

# ─── vector-store upsert (optional) ────────────────────────────────────────
try:
    from tools.memory_utils import upsert
    upsert(
        doc_id   = out.stem,
        text     = reflection_full,
        meta     = {"kind": "reflection", "date": str(date.today())}
    )
except ImportError:
    print("ℹ️ tools.memory_utils not available — skipping embed step")
