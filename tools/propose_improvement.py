#!/usr/bin/env python3
"""
Analyse latest weekly metrics + bias files and ask ChatGPT for a
concrete improvement experiment (b	$ 200 words). Save as proposals/YYYY-MM-DD_proposal.md
"""

import yaml, json, re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

# paths
metrics = Path("memory/system/metrics.csv")
arch_bias = Path("config/archetype_bias.yaml")
tag_bias  = Path("config/tag_weights.yaml")
today     = datetime.utcnow().strftime("%Y-%m-%d")
out_dir   = Path("proposals"); out_dir.mkdir(exist_ok=True)

# gather context snippets
ctx = f"### Latest archetype weights\n{arch_bias.read_text()}\n\n" \
      f"### Latest tag weights\n{tag_bias.read_text()}\n\n" \
      f"### Last 3 rows of metrics.csv\n" + "\n".join(metrics.read_text().splitlines()[-4:])

prompt = (
    "You are Lucian-core. Based on the data below, suggest ONE concrete change "
    "to improve emergent balance or insight (e.g., adjust a weight range, add a new "
    "visualisation, refine an archetype definition). Keep it under 200 words and "
    "format with:\n\n# Proposal Title\n\n## Rationale\n\n## Implementation Steps"
    f"\n\n----\n\n{ctx}"
)

resp = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.7,
    messages=[{"role":"user","content":prompt}],
    max_tokens=300,
)

prop = resp.choices[0].message.content.strip()
fname = out_dir / f"{today}_proposal.md"
fname.write_text(prop)
print("b
