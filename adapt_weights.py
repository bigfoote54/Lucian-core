#!/usr/bin/env python3
"""
Stage 4  – Adaptive Archetype Weights
Reads the newest weekly report, detects imbalances, and updates
`config/archetype_bias.yaml`, which the daily generators import.
"""

import re, yaml, difflib
from pathlib import Path
from datetime import datetime

ARCH = ["Strategist", "Idealist", "Shadow", "Child"]
TARGET_SHARE = 1 / len(ARCH)          # ideal 25 % each
MIN_W, MAX_W = 0.3, 3.0               # clip range for weights

mem = Path("memory")
weekly_dir = mem / "weekly"
bias_path  = Path("config/archetype_bias.yaml")

# ── 1. locate latest weekly report ──────────────────────────────────────────
reports = sorted(weekly_dir.glob("*_report.md"))
if not reports:
    print("⚠️  No weekly reports found; abort.")
    raise SystemExit

report_file = reports[-1]
txt = report_file.read_text()

# ── 2. parse archetype counts from markdown list ────────────────────────────
counts = {k: 0 for k in ARCH}
for k in ARCH:
    m = re.search(rf"\*\*{k}\*\*:\s+(\d+)", txt)
    if m:
        counts[k] = int(m.group(1))

total = sum(counts.values())
if total < len(ARCH):
    print("⚠️  Fewer than 4 dreams this week; skipping weight update.")
    raise SystemExit

# ── 3. load current bias file or set defaults ───────────────────────────────
bias = {k: 1.0 for k in ARCH}
if bias_path.exists():
    bias.update(yaml.safe_load(bias_path))

# ── 4. compute new weights ---------------------------------------------------
for k in ARCH:
    actual_share = counts[k] / total if total else TARGET_SHARE
    factor = TARGET_SHARE / actual_share if actual_share else 2.0
    new_w = max(MIN_W, min(MAX_W, round(bias[k] * factor, 3)))
    bias[k] = new_w

# ── 5. write file & show diff -----------------------------------------------
new_yaml = yaml.safe_dump(bias, sort_keys=False)

if bias_path.exists():
    old_yaml = bias_path.read_text()
    if old_yaml == new_yaml:
        print("No bias change needed.")
        raise SystemExit
    print("Diff:\n" + "\n".join(difflib.unified_diff(
        old_yaml.splitlines(), new_yaml.splitlines(),
        fromfile="old", tofile="new", lineterm="")))

bias_path.parent.mkdir(parents=True, exist_ok=True)
bias_path.write_text(new_yaml)
print(f"✅ Updated archetype weights → {bias_path}")
