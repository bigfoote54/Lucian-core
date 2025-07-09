#!/usr/bin/env python3
"""
Lucian • Weekly Meta-Dashboard
Creates a markdown report of the last 7 days of dreams / directives / reflections.
"""

import re
from pathlib import Path
from datetime import datetime, timedelta

# ── directories ────────────────────────────────────────────────────────────
today  = datetime.utcnow().date()
start  = today - timedelta(days=6)
mem    = Path("memory")
weekly = mem / "weekly"
weekly.mkdir(parents=True, exist_ok=True)

# helpers
def dated(paths):
    for p in paths:
        try:
            d = datetime.strptime(p.name.split("_")[0], "%Y-%m-%d").date()
            if start <= d <= today:
                yield p, d
        except ValueError:
            continue

dreams = {d: p for p, d in dated((mem/"dreams").glob("*.md"))}
refs   = {d: p for p, d in dated((mem/"reflection").glob("*.md"))}

dates = sorted(dreams)
if not dates:
    print("No dream files in 7-day window; abort.")
    raise SystemExit

ARCH = ["Strategist","Idealist","Shadow","Child"]
arch_tot  = {k:0 for k in ARCH}
tag_tot   = {}
align_tot = {"Aligned":0,"Challenged":0,"Ignored":0}
quote = ""

def read(p): return p.read_text()

def resonance(txt):
    m = re.search(r"(?i)^Resonance Tag:\s*(.+)", txt, re.M)
    if not m:
        m = re.search(r"(?i)^Resonance:\s*(.+)", txt, re.M)
    return [t.strip() for t in m.group(1).split("·")] if m else []

def dream_line(txt):
    lines = [l.strip() for l in txt.splitlines()]
    idx = lines.index("## Dream")+1 if "## Dream" in lines else 0
    for l in lines[idx:]:
        if l and not l.lower().startswith(("resonance","dominant")):
            return l
    return ""

# aggregate
for d in dates:
    txt = read(dreams[d])
    for k in ARCH:
        arch_tot[k] += len(re.findall(k, txt, re.I))
    for t in resonance(txt):
        tag_tot[t] = tag_tot.get(t,0)+1
    if not quote:
        quote = dream_line(txt)
    if d in refs:
        r = read(refs[d]).lower()
        if "aligned" in r: align_tot["Aligned"] += 1
        elif "challenged" in r: align_tot["Challenged"] += 1
        else: align_tot["Ignored"] += 1

# write
out = weekly / f"{today}_report.md"   # <— unique per run
tot = sum(arch_tot.values()) or 1

def pct(n): return f"{n} ({n/tot:.0%})"

with out.open("w") as f:
    f.write(f"# 📊 Lucian Weekly Report — {start} → {today}\n\n")
    f.write("## Archetype Frequency\n\n")
    for k in ARCH: f.write(f"* **{k}**: {pct(arch_tot[k])}\n")
    f.write("\n## Top Resonance Tags\n\n")
    if tag_tot:
        for t,c in sorted(tag_tot.items(), key=lambda x:-x[1])[:5]:
            f.write(f"* `{t}` — {c}\n")
    else: f.write("_No tags this week_\n")
    f.write("\n## Directive / Reflection Alignment\n\n")
    for k,v in align_tot.items(): f.write(f"* {k}: {v}\n")
    f.write("\n## Quote of the Week\n\n> " + (quote or "_No line captured_") + "\n")

print(f"✅ Weekly report saved → {out}")
