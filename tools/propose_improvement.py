#!/usr/bin/env python3
"""
tools/propose_improvement.py
-------------------------------------------------
Reads the most recent metrics & weight files and asks
ChatGPT for ONE concrete growth idea (<200 words).
Writes to  proposals/YYYY-MM-DD_proposal.md
"""

from pathlib import Path
from datetime import datetime
import yaml, textwrap
from dotenv import load_dotenv
from openai import OpenAI

# ── Setup ───────────────────────────────────────
load_dotenv()
client = OpenAI()

today      = datetime.utcnow().strftime("%Y-%m-%d")
out_path   = Path("proposals"); out_path.mkdir(exist_ok=True)
outfile    = out_path / f"{today}_proposal.md"

metrics    = Path("memory/system/metrics.csv")
arch_bias  = Path("config/archetype_bias.yaml")
tag_bias   = Path("config/tag_weights.yaml")

# ── Gather context snippets ─────────────────────
ctx_parts = []

if arch_bias.exists():
    ctx_parts.append("### Archetype bias map\n" + arch_bias.read_text().strip())

if tag_bias.exists():
    ctx_parts.append("### Tag bias map\n" + tag_bias.read_text().strip())

if metrics.exists():
    last_rows = "\n".join(metrics.read_text().splitlines()[-4:])
    ctx_parts.append("### Latest metrics.csv (tail-3)\n" + last_rows)

context = "\n\n".join(ctx_parts)

# ── Prompt ──────────────────────────────────────
prompt = textwrap.dedent(f"""
    You are Lucian-core reflecting on its own metrics and bias files.

    TASK: Propose **one** tangible improvement experiment that could
    help achieve better archetype balance, richer symbolism, or clearer
    self-reflection. Keep the whole proposal under 200 words.

    Format exactly:

    # <Short title>

    ## Rationale
    <why?>

    ## Implementation Steps
    - step 1…
    - step 2…

    ----
    {context}
""").strip()

# ── OpenAI call ─────────────────────────────────
resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,
    max_tokens=300,
)

proposal = resp.choices[0].message.content.strip()

# ── Save file ───────────────────────────────────
outfile.write_text(proposal)
print("✅ Proposal saved →", outfile)
