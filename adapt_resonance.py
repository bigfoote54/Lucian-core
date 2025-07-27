#!/usr/bin/env python3
"""
Stage 5 – Adaptive Resonance Tags
Scans the last 7 days of dreams, adjusts tag weights, and writes
config/tag_weights.yaml for use in future prompts.
"""

import re, yaml
from pathlib import Path
from datetime import datetime, timedelta

# ── Config ─────────────────────────────────────────────────────────────────
MEM   = Path("memory")
TAGS  = Path("config/tag_weights.yaml")
MIN_W, MAX_W = 0.5, 2.0

# ── 1. Gather dreams from past 7 days ──────────────────────────────────────
cutoff = datetime.utcnow() - timedelta(days=7)
dreams = [
    p for p in (MEM/"dreams").glob("*.md")
    if datetime.utcfromtimestamp(p.stat().st_mtime) >= cutoff
]

if len(dreams) < 4:
    print("⚠️  Fewer than 4 dreams this week; skipping tag update.")
    raise SystemExit

# ── 2. Extract resonance tags & tally counts ───────────────────────────────
counts = {}
for p in dreams:
    txt = p.read_text()
    m = re.search(r"Resonance Tag:\s*(.+)", txt)
    if m:
        tags = [t.strip() for t in re.split(r"[·,|]", m.group(1))]
        for t in tags:
            if t:
                counts[t] = counts.get(t, 0) + 1

if not counts:
    print("⚠️  No resonance tags found; abort.")
    raise SystemExit

# ── 3. Load existing weights or default to 1.0 ─────────────────────────────
weights = {tag: 1.0 for tag in counts}
if TAGS.exists():
    weights.update(yaml.safe_load(TAGS.read_text()))

# ── 4. Adjust weights: under-used ↑, over-used ↓ ───────────────────────────
avg = sum(counts.values()) / len(counts)
for tag, cnt in counts.items():
    factor = avg / cnt if cnt > 0 else 1.2
    new_w  = max(MIN_W, min(MAX_W, round(weights.get(tag,1.0)*factor,3)))
    weights[tag] = new_w

# Tags seen for first time get a small boost
for tag in weights:
    if tag not in counts:
        weights[tag] = min(MAX_W, round(weights[tag]+0.1,3))

# ── 5. Save file & report diff ─────────────────────────────────────────────
TAGS.parent.mkdir(parents=True, exist_ok=True)
TAGS.write_text(yaml.safe_dump(weights, sort_keys=False))
print(f"✅ Updated resonance weights → {TAGS}")
