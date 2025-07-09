#!/usr/bin/env python3
import re, csv
from pathlib import Path

weekly = Path("memory/weekly")
out    = Path("memory/system/metrics.csv")
out.parent.mkdir(parents=True, exist_ok=True)

rows = []
for p in sorted(weekly.glob("*_report.md")):     # ← match correct filenames
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p.name)
    if not m:                                     # safety
        continue
    date = m.group(1)
    txt  = p.read_text()

    def grab(k):
        m2 = re.search(rf"\*\*{k}\*\*:\s+(\d+)", txt)
        return int(m2.group(1)) if m2 else 0

    rows.append([
        date,
        grab("Strategist"), grab("Idealist"),
        grab("Shadow"),     grab("Child"),
        grab("Aligned"),    grab("Challenged"), grab("Ignored")
    ])

with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date","strategist","idealist","shadow","child",
                "aligned","challenged","ignored"])
    w.writerows(rows)

print(f"✅ metrics.csv written → {len(rows)} rows")
