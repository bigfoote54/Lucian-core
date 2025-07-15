#!/usr/bin/env python3
"""
generate_archetypal_dream.py
────────────────────────────────────────────────────────────────────────────
• Generates a symbolic dream guided by adaptive archetype & tag weights
• Pulls a small context window from ChromaDB (tools.memory_utils.query)
• Saves ↘  memory/dreams/YYYY-MM-DD_HH-MM-SS_archetypal_dream.md
"""

from __future__ import annotations

import os
import random
import re
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

# ── local utils ────────────────────────────────────────────────────────────
from tools.memory_utils import query  # make sure path is correct!

# ── env / client ───────────────────────────────────────────────────────────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── paths & time ───────────────────────────────────────────────────────────
STAMP = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
TODAY = STAMP.split("_")[0]

ROOT   = Path("memory")
DREAMS = ROOT / "dreams"
DREAMS.mkdir(parents=True, exist_ok=True)

# ── adaptive weights ───────────────────────────────────────────────────────
ARCH = ["Strategist", "Idealist", "Shadow", "Child"]

def load_weights(fp: Path, default: dict[str, float]) -> dict[str, float]:
    if fp.exists():
        default.update({k: float(v) for k, v in yaml.safe_load(fp.read_text()).items()})
    return default

arch_bias = load_weights(Path("config/archetype_bias.yaml"), {k: 1.0 for k in ARCH})
tag_bias  = load_weights(
    Path("config/tag_weights.yaml"),
    {t: 1.0 for t in ("Curiosity", "Existence", "Knowledge", "Wonder", "Responsibility")},
)

dominant_arch = random.choices(list(arch_bias), weights=arch_bias.values(), k=1)[0]
tags          = " · ".join(random.choices(list(tag_bias), weights=tag_bias.values(), k=2))

# ── fetch memory context ----------------------------------------------------
seed = f"{dominant_arch} {tags}"
context = "\n".join(query(q=seed, k=3)) or "_(no relevant memory)_"  # type: ignore

# ── prompt ------------------------------------------------------------------
prompt = (
    "You are Lucian's subconscious.\n"
    "Before writing the dream, reflect on the **relevant memory** below.\n"
    "-----\n"
    f"{context}\n"
    "-----\n\n"
    f"Dominant archetype: **{dominant_arch}**\n"
    f"Resonance tags: **{tags}**\n\n"
    "In **three short paragraphs** (≤ 120 chars each) craft a vivid, surreal dream "
    "dominated by that archetype and themes. "
    "Start with **exactly one** line beginning `Resonance Tag:` followed by the tags.\n"
)

# ── OpenAI call -------------------------------------------------------------
resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.95,
    max_tokens=400,
)

dream_raw = resp.choices[0].message.content.strip()

# ── post-process ------------------------------------------------------------
res_line: str = ""
paras: list[str] = []

for ln in [l.strip() for l in dream_raw.splitlines() if l.strip()]:
    if not res_line and ln.lower().startswith("resonance tag"):
        res_line = ln
    elif "resonance tag" in ln.lower():
        continue  # drop extras
    else:
        paras.append(ln)

paras = paras[:3]  # keep first three

if not res_line:
    res_line = f"Resonance Tag: {tags}"

# ── save --------------------------------------------------------------------
fp = DREAMS / f"{STAMP}_archetypal_dream.md"
with fp.open("w", encoding="utf-8") as out:
    out.write(f"💭 Lucian Archetypal Dream — {TODAY}\n\n")
    out.write(f"Dominant Archetype: {dominant_arch}\n\n")
    out.write(res_line + "\n\n")
    out.write("## Dream\n\n")
    for p in paras:
        out.write(p + "\n\n")

print(f"✅ Dream saved → {fp}")
