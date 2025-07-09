#!/usr/bin/env python3
import re, csv
from pathlib import Path
weekly = Path("memory/weekly")
out = Path("memory/system/metrics.csv"); out.parent.mkdir(parents=True, exist_ok=True)
rows=[]
for p in sorted(weekly.glob("20*-report.md")):
    m=re.match(r"(\d{4}-\d{2}-\d{2})",p.name); date=m.group(1)
    t=p.read_text(); g=lambda k:int(re.search(rf"\*\*{k}\*\*:\s+(\d+)",t).group(1)) if re.search(rf"\*\*{k}\*\*:",t) else 0
    rows.append([date,g('Strategist'),g('Idealist'),g('Shadow'),g('Child'),
                 g('Aligned'),g('Challenged'),g('Ignored')])
with out.open("w",newline="") as f:
    w=csv.writer(f); w.writerow(["date","strategist","idealist","shadow","child","aligned","challenged","ignored"]); w.writerows(rows)
print("✅ metrics.csv written")
