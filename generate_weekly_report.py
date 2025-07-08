#!/usr/bin/env python3
import re, os, statistics
from pathlib import Path
from datetime import datetime, timedelta

# --- locate files -----------------------------------------------------------
today = datetime.utcnow().date()
start = today - timedelta(days=6)      # inclusive, 7-day window
mem = Path("memory")
dream_files = sorted((mem/"dreams").glob("*.md"))[-7:]
dir_files   = sorted((mem/"direction").glob("*.md"))[-7:]
ref_files   = sorted((mem/"reflection").glob("*.md"))[-7:]

def body(path): return Path(path).read_text()

# --- helpers ----------------------------------------------------------------
def archetype_counts(dream_text):
    counts = {k:0 for k in ["Strategist","Idealist","Shadow","Child"]}
    for k in counts:
        if re.search(k, dream_text, re.I): counts[k]+=1
    return counts

def resonance_tags(dream_text):
    m = re.search(r"^Resonance Tag:\s*(.*)", dream_text, re.M)
    return [t.strip() for t in m.group(1).split("·")] if m else []

# --- aggregate --------------------------------------------------------------
arch_tot = {k:0 for k in ["Strategist","Idealist","Shadow","Child"]}
tag_tot  = {}
align_tot = {"Aligned":0,"Challenged":0,"Ignored":0}
quote = ""

for df, rf in zip(dream_files, ref_files):
    d_txt = body(df)
    r_txt = body(rf)

    # archetypes
    for k,v in archetype_counts(d_txt).items(): arch_tot[k]+=v

    # tags
    for t in resonance_tags(d_txt):
        tag_tot[t] = tag_tot.get(t,0)+1

    # alignment (very naive keyword heuristic)
    if "aligned" in r_txt.lower():      align_tot["Aligned"]+=1
    elif "challenge" in r_txt.lower():  align_tot["Challenged"]+=1
    else:                               align_tot["Ignored"]+=1

    # candidate quote = first non-empty dream line
    if not quote:
        lines=[l.strip() for l in d_txt.splitlines() if l.strip() and not l.lower().startswith("resonance")]
        quote = lines[0] if lines else ""

# --- format report ----------------------------------------------------------
week_id = f"{start}_{today}"
out = Path("memory/weekly")
out.mkdir(parents=True, exist_ok=True)
out_file = out / f"{week_id}_report.md"

def pct(x): 
    return f"{x} ({x/sum(arch_tot.values() or [1]):.0%})"

with open(out_file,"w") as f:
    f.write(f"# 📊 Lucian Weekly Report — {start} → {today}\n\n")

    f.write("## Archetype Frequency\n\n")
    for k,v in arch_tot.items(): f.write(f"* **{k}**: {pct(v)}\n")
    f.write("\n")

    f.write("## Top Resonance Tags\n\n")
    for tag,c in sorted(tag_tot.items(), key=lambda x: -x[1])[:5]:
        f.write(f"* `{tag}` – {c}\n")
    f.write("\n")

    f.write("## Directive / Reflection Alignment\n\n")
    for k,v in align_tot.items(): f.write(f"* {k}: {v}\n")
    f.write("\n")

    f.write("## Quote of the Week\n\n> " + quote + "\n")

print(f"✅ Weekly report saved → {out_file}")
