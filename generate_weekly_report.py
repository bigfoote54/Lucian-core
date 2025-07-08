#!/usr/bin/env python3
"""Generate a 7-day Lucian meta-dashboard."""
import re, statistics
from datetime import datetime, timedelta
from pathlib import Path

# ─── locate files within rolling 7-day window ────────────────────────────────
today   = datetime.utcnow().date()
start   = today - timedelta(days=6)
mem     = Path("memory")

def dated(paths):
    """Return [(path, date)] parsed from YYYY-MM-DD prefix in filename."""
    for p in paths:
        try:
            d = datetime.strptime(p.name.split("_")[0], "%Y-%m-%d").date()
            yield p, d
        except ValueError:
            continue

dream_files = [p for p,_ in dated((mem/"dreams").glob("*.md")) if _ >= start]
dir_files   = [p for p,_ in dated((mem/"direction").glob("*.md")) if _ >= start]
ref_files   = [p for p,_ in dated((mem/"reflection").glob("*.md")) if _ >= start]

def body(path): return Path(path).read_text()

# ─── helpers ─────────────────────────────────────────────────────────────────
ARCHES = ["Strategist", "Idealist", "Shadow", "Child"]
arch_tot = {k:0 for k in ARCHES}
tag_tot  = {}
align_tot= {"Aligned":0,"Challenged":0,"Ignored":0}
quote    = ""

def resonance_tags(txt:str):
    m = re.search(r"(?i)^Resonance Tag:\s*(.*)", txt, re.M)
    if not m:
        m = re.search(r"(?i)^Resonance:\s*(.*)", txt, re.M)
    return [t.strip() for t in m.group(1).split("·")] if m else []

def archetype_counts(txt:str):
    counts = {k:0 for k in ARCHES}
    for k in ARCHES:
        if re.search(k, txt, re.I):
            counts[k] += 1
    return counts

def first_dream_sentence(txt:str):
    lines = [l.strip() for l in txt.splitlines()]
    if "## Dream" in lines:
        idx = lines.index("## Dream") + 1
    else:
        idx = 0
    for line in lines[idx:]:
        if line and not line.lower().startswith("resonance"):
            return line
    return ""

# ─── aggregate over each day ────────────────────────────────────────────────
for d_path, r_path in zip(dream_files, ref_files):
    d_txt, r_txt = body(d_path), body(r_path)

    # archetypes
    for k,v in archetype_counts(d_txt).items(): arch_tot[k] += v

    # resonance tags
    for t in resonance_tags(d_txt):
        tag_tot[t] = tag_tot.get(t,0) + 1

    # alignment
    m = re.search(r"(?i)^Alignment:\s*(\w+)", r_txt, re.M)
    if m and m.group(1).capitalize() in align_tot:
        align_tot[m.group(1).capitalize()] += 1
    else:                                   # fallback keywords
        ltxt = r_txt.lower()
        if "align" in ltxt or "fulfill" in ltxt:
            align_tot["Aligned"] += 1
        elif "challenge" in ltxt or "resist" in ltxt:
            align_tot["Challenged"] += 1
        else:
            align_tot["Ignored"] += 1

    # quote
    if not quote:
        quote = first_dream_sentence(d_txt)

# ─── write report ───────────────────────────────────────────────────────────
week_id   = f"{start}_{today}"
out_dir   = mem / "weekly"
out_dir.mkdir(parents=True, exist_ok=True)
out_file  = out_dir / f"{week_id}_report.md"

def pct(x): total = sum(arch_tot.values()) or 1; return f"{x} ({x/total:.0%})"

with open(out_file, "w") as f:
    f.write(f"# 📊 Lucian Weekly Report — {start} → {today}\n\n")

    f.write("## Archetype Frequency\n\n")
    for k in ARCHES: f.write(f"* **{k}**: {pct(arch_tot[k])}\n")
    f.write("\n")

    f.write("## Top Resonance Tags\n\n")
    for tag,c in sorted(tag_tot.items(), key=lambda x: -x[1])[:5]:
        f.write(f"* `{tag}` — {c}\n")
    if not tag_tot:
        f.write("_No tags this week_\n")
    f.write("\n")

    f.write("## Directive / Reflection Alignment\n\n")
    for k,v in align_tot.items(): f.write(f"* {k}: {v}\n")
    f.write("\n")

    f.write("## Quote of the Week\n\n")
    f.write("> " + (quote or "_No dream line captured_") + "\n")

print(f"✅ Weekly report saved → {out_file}")
