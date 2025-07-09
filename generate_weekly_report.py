#!/usr/bin/env python3
"""
Lucian • Weekly Meta-Dashboard
Creates a markdown report of the last 7 days of dreams / reflections.
"""

import re
from pathlib import Path
from datetime import datetime, timedelta

# ── directories ────────────────────────────────────────────────────────────
today  = datetime.utcnow().date()
start  = today - timedelta(days=6)

MEM    = Path("memory")
WEEKLY = MEM / "weekly"
WEEKLY.mkdir(parents=True, exist_ok=True)

# ── helper to filter files in window ────────────────────────────────────────
def dated(paths):
    for p in paths:
        try:
            d = datetime.strptime(p.name.split("_")[0], "%Y-%m-%d").date()
            if start <= d <= today:
                yield p, d
        except ValueError:
            continue

dreams = {d: p for p, d in dated((MEM/"dreams").glob("*.md"))}
refs   = {d: p for p, d in dated((MEM/"reflection").glob("*.md"))}

if not dreams:
    print("No dream files in 7-day window; abort.")
    raise SystemExit

dates = sorted(dreams)

# ── aggregation buckets ────────────────────────────────────────────────────
ARCH       = ["Strategist", "Idealist", "Shadow", "Child"]
arch_tot   = {k: 0 for k in ARCH}
tag_tot    = {}
align_tot  = {"Aligned": 0, "Challenged": 0, "Ignored": 0}
quote      = ""

def read(p): return p.read_text()

def resonance_tags(txt: str):
    m = re.search(r"(?i)^Resonance Tag:\s*(.+)", txt, re.M)
    if not m:
        m = re.search(r"(?i)^Resonance:\s*(.+)", txt, re.M)
    return [t.strip() for t in m.group(1).split("·")] if m else []

def first_dream_line(txt: str):
    lines = [l.strip() for l in txt.splitlines()]
    idx = lines.index("## Dream") + 1 if "## Dream" in lines else 0
    for l in lines[idx:]:
        if l and not l.lower().startswith(("resonance", "dominant")):
            return l
    return ""

# ── aggregate data ─────────────────────────────────────────────────────────
for d in dates:
    txt = read(dreams[d])

    #   (a) count explicit archetype words inside narrative
    for k in ARCH:
        arch_tot[k] += len(re.findall(k, txt, re.I))

    #   ⚙️ (b) add one for the Dominant line so every dream is counted
    m_dom = re.search(r"Dominant Archetype:\s*(\w+)", txt)
    if m_dom and m_dom.group(1) in arch_tot:
        arch_tot[m_dom.group(1)] += 1

    #   (c) resonance tags
    for tag in resonance_tags(txt):
        tag_tot[tag] = tag_tot.get(tag, 0) + 1

    #   (d) pull first dream sentence as quote
    if not quote:
        quote = first_dream_line(txt)

    #   (e) reflection alignment
    if d in refs:
        r = read(refs[d]).lower()
        if "aligned" in r:
            align_tot["Aligned"] += 1
        elif "challenged" in r:
            align_tot["Challenged"] += 1
        else:
            align_tot["Ignored"] += 1

# ── write markdown report ──────────────────────────────────────────────────
out_path = WEEKLY / f"{today}_report.md"     # unique file each run
total_arch = sum(arch_tot.values()) or 1
pct = lambda n: f"{n} ({n/total_arch:.0%})"

with out_path.open("w") as f:
    f.write(f"# 📊 Lucian Weekly Report — {start} → {today}\n\n")

    f.write("## Archetype Frequency\n\n")
    for k in ARCH:
        f.write(f"* **{k}**: {pct(arch_tot[k])}\n")

    f.write("\n## Top Resonance Tags\n\n")
    if tag_tot:
        for t, c in sorted(tag_tot.items(), key=lambda x: -x[1])[:5]:
            f.write(f"* `{t}` — {c}\n")
    else:
        f.write("_No tags this week_\n")

    f.write("\n## Directive / Reflection Alignment\n\n")
    for k, v in align_tot.items():
        f.write(f"* {k}: {v}\n")

    f.write("\n## Quote of the Week\n\n")
    f.write("> " + (quote or "_No dream line captured_") + "\n")

print(f"✅ Weekly report saved → {out_path}")
