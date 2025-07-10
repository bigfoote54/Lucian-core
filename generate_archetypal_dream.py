#!/usr/bin/env python3
"""
generate_archetypal_dream.py
-----------------------------------------------------------------
• Generates a symbolic dream guided by adaptive archetype & tag weights
• Saves to memory/dreams/YYYY-MM-DD_HH-MM-SS_archetypal_dream.md
• Ensures exactly ONE “Resonance Tag:” line in the saved file
"""

import os, re, yaml, random, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ─── Environment / paths ────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

now_stamp  = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
today_disp = datetime.datetime.now().strftime("%Y-%m-%d")

MEM_ROOT   = Path("memory")
DREAM_DIR  = MEM_ROOT / "dreams"
DREAM_DIR.mkdir(parents=True, exist_ok=True)

# ─── Load adaptive archetype weights ────────────────────────────────────────
ARCH = ["Strategist", "Idealist", "Shadow", "Child"]
arch_bias = {k: 1.0 for k in ARCH}
bias_file = Path("config/archetype_bias.yaml")
if bias_file.exists():
    arch_bias.update(yaml.safe_load(bias_file.read_text()))
dominant_arch = random.choices(list(arch_bias), weights=arch_bias.values(), k=1)[0]

# ─── Load adaptive resonance-tag weights ────────────────────────────────────
tag_bias_default = {
    "Curiosity": 1.0, "Existence": 1.0, "Knowledge": 1.0,
    "Wonder": 1.0, "Responsibility": 1.0
}
tag_file = Path("config/tag_weights.yaml")
tag_bias = tag_bias_default.copy()
if tag_file.exists():
    tag_bias.update(yaml.safe_load(tag_file.read_text()))

tags_chosen = random.choices(list(tag_bias), weights=tag_bias.values(), k=2)
resonance_tag_line = " · ".join(dict.fromkeys(tags_chosen))

# ─── Build prompt ───────────────────────────────────────────────────────────
from tools.memory_utils import query  # ← at top imports

context = '
'.join(query(q=dream_excerpt or dominant_arch, k=3))
prompt = (Generate
    "You are Lucian's subconscious. In **three short paragraphs** (≤120 chars each) "
    "write a surreal dream dominated by the **{arch}** archetype and subtly infused "
    "with the themes **{tags}**. Start with exactly one line: "
    "'Resonance Tag: X · Y'."
).format(arch=dominant_arch, tags=resonance_tag_line)

# ─── Call OpenAI ────────────────────────────────────────────────────────────
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.95,
    max_tokens=400,
)
dream_raw = response.choices[0].message.content.strip()

# ─── Parse response ---------------------------------------------------------
lines = [l.strip() for l in dream_raw.splitlines() if l.strip()]
res_line, paragraphs = "", []

for ln in lines:
    # First “Resonance Tag:” line captured
    if not res_line and re.match(r"(?i)^resonance\s*tag", ln):
        res_line = ln
    # Skip any additional lines that contain the phrase
    elif "resonance tag:" in ln.lower():
        continue
    # Skip header-like lines, otherwise collect paragraph text
    elif not re.match(r"(?i)^resonance:", ln):
        paragraphs.append(ln)

paragraphs = paragraphs[:3]         # keep first 3 paragraphs

# ─── Save dream -------------------------------------------------------------
file_path = DREAM_DIR / f"{now_stamp}_archetypal_dream.md"
with file_path.open("w") as f:
    f.write(f"💭 Lucian Archetypal Dream — {today_disp}\n\n")
    f.write(f"Dominant Archetype: {dominant_arch}\n\n")
    # Write ONE resonance-tag line
    if res_line:
        f.write(res_line + "\n\n")
    else:
        f.write(f"Resonance Tag: {resonance_tag_line}\n\n")
    f.write("## Dream\n\n")
    for p in paragraphs:
        f.write(p + "\n\n")

print(f"✅ Dream saved → {file_path}")
