
#!/usr/bin/env python3
"""
reflect.py
Compares yesterday's directive with today's dream and writes a reflection
including an explicit `Alignment:` tag for downstream analytics.
"""

import os, re, yaml
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today      = datetime.now().strftime("%Y-%m-%d")
yesterday  = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

mem        = Path("memory")
dreams_dir = mem / "dreams"
dir_dir    = mem / "direction"
ref_dir    = mem / "reflection"
ref_dir.mkdir(parents=True, exist_ok=True)

# ─── Load yesterday's directive ─────────────────────────────────────────────
dir_path = dir_dir / f"{yesterday}_direction.md"
if not dir_path.exists():
    directive_text = "No directive found."
else:
    directive_text = dir_path.read_text()

dir_body = re.search(r"## Directive\n\n(.+)", directive_text, re.DOTALL)
yesterday_directive = dir_body.group(1).strip() if dir_body else directive_text.strip()

# ─── Load today's dream ─────────────────────────────────────────────────────
dream_path = dreams_dir / f"{today}_archetypal_dream.md"
if not dream_path.exists():
    raise SystemExit("Today's dream not found. Run dream generator first.")
dream_text = dream_path.read_text()

dream_body = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)
today_dream = dream_body.group(1).strip() if dream_body else dream_text.strip()

# ─── Load adaptive archetype bias (optional context) ────────────────────────
bias_path = Path("config/archetype_bias.yaml")
bias = yaml.safe_load(bias_path.read_text()) if bias_path.exists() else {}

# ─── Prompt OpenAI ───────────────────────────────────────────────────────────
prompt = (
    "You are Lucian reflecting on your growth.\n\n"
    f"Yesterday's directive:\n\"\"\"{yesterday_directive}\"\"\"\n\n"
    f"Today's dream:\n\"\"\"{today_dream}\"\"\"\n\n"
    f"Current archetype bias map: {bias}\n\n"
    "Write a short reflection (2–4 sentences) analysing whether the dream "
    "aligned with the directive. Conclude **after a blank line** with a single "
    "line starting `Alignment:` followed by one of: Aligned, Challenged, Ignored."
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
    max_tokens=200,
)

reflection_full = response.choices[0].message.content.strip()

# Ensure Alignment tag exists; fallback to heuristic if missing
m = re.search(r"^Alignment:\s*(\w+)", reflection_full, re.M)
if not m:
    tag = "Aligned" if any(w in reflection_full.lower() for w in ("aligned", "fulfilled", "met")) else \
          "Challenged" if "challenge" in reflection_full.lower() else "Ignored"
    reflection_full += f"\n\nAlignment: {tag}"

# ─── Save --------------------------------------------------------------------
out = ref_dir / f"{today}_reflection.md"
with out.open("w") as f:
    f.write(f"🪞 Lucian Daily Reflection — {today}\n\n")
    f.write(f"## Yesterday's Directive\n\n{yesterday_directive}\n\n")
    f.write(f"## Today's Dream Fragment\n\n{today_dream[:400]}...\n\n")
    f.write("## Reflection\n\n" + reflection_full + "\n")

print(f"✅ Reflection saved → {out}")

