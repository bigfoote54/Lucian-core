#!/usr/bin/env python3
"""
Lucian • Weekly Meta-Dashboard
Summarises the last 7 days of dreams / directives / reflections.
"""

import re
from pathlib import Path
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
#  Window & file collection
# ─────────────────────────────────────────────────────────────────────────────
today  = datetime.utcnow().date()
start  = today - timedelta(days=6)
mem    = Path("memory")

def dated(paths):
    """Yield (path, date) for files starting with YYYY-MM-DD_."""
    for p in paths:
        try:
            d = datetime.strptime(p.name.split("_")[0], "%Y-%m-%d").date()
            if d >= start and d <= today:
                yield p, d
        except ValueError:
            continue

dream_map = {d: p for p, d in dated((mem / "dreams").glob("*.md"))}
ref_map   = {d: p for p, d in dated((mem / "reflection").glob("*.md"))}

dates = sorted(dream_map.keys())         # iterate over dream dates only
if not dates:
    print("No dream files in 7-day window; aborting.")
    exit(0)

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
ARCHES = ["Strategist", "Idealist", "Shadow", "Child"]
arch_tot = {k: 0 for k in ARCHES}
tag_tot  = {}
align_tot = {"Aligned": 0, "Challenged": 0, "Ignored": 0}
quote = ""

def read(p): return Path(p).read_text()

def resonance_tags(txt: str):
    m = re.search(r"(?i)^Resonance Tag:\s*(.*)", txt, re.M)
    if not m:
        m = re.search(r"(?i)^Resonance:\s*(.*)", txt, re.M)
    return [t.strip() for t in m.group(1).split("·")] if m else []

def archetype_counts(txt: str):
    counts = {k: 0 for k in ARCHES}
    for k in ARCHES:
        counts[k] += len(re.findall(k, txt, re.I))
    return counts

def first_dream_line(txt: str):
    lines = [l.strip() for l in txt.splitlines()]
    idx = lines.index("## Dream") + 1 if "## Dream" in lines else 0
    for l in lines[idx:]:
        if l and not l.startswith(("#", "💭")) and not l.lower().startswith("resonance"):
            return l
    return ""

# ─────────────────────────────────────────────────────────────────────────────
#  Aggregate
# ─────────────────────────────────────────────────────────────────────────────
for d in dates:
    d_txt = read(dream_map[d])

    # Archetype counts
    for k, v in archetype_counts(d_txt).items():
        arch_tot[k] += v

    # Resonance tags
    for t in resonance_tags(d_txt):
        tag_tot[t] = tag_tot.get(t, 0) + 1

    # Quote of the week
    if not quote:
        quote = first_dream_line(d_txt)

    # Alignment only if a reflection exists for that date
    if d in ref_map:
        r_txt = read(ref_map[d])
        m = re.search(r"(?i)^Alignment:\s*(\w+)", r_txt, re.M)
        if m and m.group(1).capitalize() in align_tot:
            align_tot[m.group(1).capitalize()] += 1
        else:
            lt = r_txt.lower()
            if any(w in lt for w in ("align", "fulfill", "met")):
                align_tot["Aligned"] += 1
            elif any(w in lt for w in ("challenge", "resist")):
                align_tot["Challenged"] += 1
            else:
                align_tot["Ignored"] += 1

# ─────────────────────────────────────────────────────────────────────────────
#  Write report
# ─────────────────────────────────────────────────────────────────────────────
out_dir = mem / "weekly"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / f"{start}_{today}_report.md"

def pct(x):
    total = sum(arch_tot.values()) or 1
    return f"{x} ({x/total:.0%})"

with open(out_path, "w") as f:
    f.write(f"# 📊 Lucian Weekly Report — {start} → {today}\n\n")

    # Archetypes
    f.write("## Archetype Frequency\n\n")
    for k in ARCHES:
        f.write(f"* **{k}**: {pct(arch_tot[k])}\n")
    f.write("\n")

    # Tags
    f.write("## Top Resonance Tags\n\n")
    if tag_tot:
        for tag, c in sorted(tag_tot.items(), key=lambda x: -x[1])[:5]:
            f.write(f"* `{tag}` — {c}\n")
    else:
        f.write("_No tags this week_\n")
    f.write("\n")

    # Alignment
    f.write("## Directive / Reflection Alignment\n\n")
    for k, v in align_tot.items():
        f.write(f"* {k}: {v}\n")
    f.write("\n")

    # Quote
    f.write("## Quote of the Week\n\n")
    f.write("> " + (quote or "_No dream line captured_") + "\n")

print(f"✅ Weekly report saved → {out_path}")
