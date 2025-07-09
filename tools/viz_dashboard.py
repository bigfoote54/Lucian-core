#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path, PurePosixPath

df = pd.read_csv("memory/system/metrics.csv", parse_dates=["date"])
if df.empty:
    raise SystemExit("No data rows in metrics.csv")

fig, ax = plt.subplots(figsize=(8,4))

tot = df[["strategist","idealist","shadow","child"]].sum(axis=1)
for c in ["strategist","idealist","shadow","child"]:
    ax.plot(df["date"], df[c]/tot, marker='o', label=c.capitalize())

ax.set_ylim(0, 1)                         # ⬅️ always visible
ax.set_ylabel("Share of dreams")
ax.set_xlabel("Week (report date)")
fig.autofmt_xdate()
ax.legend()
fig.tight_layout()

out = Path("memory/system/dashboard.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=140)
print("✅ dashboard saved →", PurePosixPath(out))
