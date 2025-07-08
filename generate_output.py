#!/usr/bin/env python3

import re
from pathlib import Path
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")
memory_path = Path("memory")
dreams_dir = memory_path / "dreams"
direction_dir = memory_path / "direction"
output_path = Path("lucian_output.md")

# ─── Get Latest File from Folder ─────────────────────────────────────────────
def get_latest_file(directory, suffix):
    files = sorted(directory.glob(f"*{suffix}"), reverse=True)
    return files[0] if files else None

# ─── Load Dream & Direction ──────────────────────────────────────────────────
dream_file = get_latest_file(dreams_dir, "_archetypal_dream.md")
direction_file = get_latest_file(direction_dir, "_direction.md")

dream_text = dream_file.read_text().strip() if dream_file else "No dream found."
direction_text = direction_file.read_text().strip() if direction_file else "No direction found."

# ─── Extract Metadata from Dream ─────────────────────────────────────────────
resonance = re.search(r"^Resonance:\s*(.*)", dream_text, re.MULTILINE)
resonance_tag = re.search(r"^Resonance Tag:\s*(.*)", dream_text, re.MULTILINE)
dream_body = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)

resonance_str = resonance.group(1).strip() if resonance else "N/A"
resonance_tag_str = resonance_tag.group(1).strip() if resonance_tag else "N/A"
dream_content = dream_body.group(1).strip() if dream_body else dream_text

# ─── Extract Directive Body ──────────────────────────────────────────────────
directive = re.search(r"## Directive\n\n(.+)", direction_text, re.DOTALL)
directive_content = directive.group(1).strip() if directive else direction_text

# ─── Write Unified Output ────────────────────────────────────────────────────
with open(output_path, "w") as f:
    f.write(f"# 🌅 Lucian Daily Output — {today}\n\n")
    f.write(f"## 💭 Archetypal Dream\n")
    f.write(f"Resonance: {resonance_str}\n\n")
    f.write(f"Resonance Tag: {resonance_tag_str}\n\n")
    f.write(dream_content + "\n\n")
    f.write("---\n\n")
    f.write("## 🧭 Daily Directive\n\n")
    f.write(directive_content + "\n")

print(f"✅ Merged output written to → {output_path}")

