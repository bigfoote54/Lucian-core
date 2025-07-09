#!/usr/bin/env python3
import pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
df = pd.read_csv("memory/system/metrics.csv", parse_dates=["date"])
fig, ax = plt.subplots(figsize=(8,4))
for c in ["strategist","idealist","shadow","child"]:
    ax.plot(df["date"], df[c]/df[["strategist","idealist","shadow","child"]].sum(axis=1), label=c.capitalize())
ax.set_ylabel("Share of dreams"); ax.legend(); fig.tight_layout()
out = Path("memory/system/dashboard.png"); out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=140); print("✅ dashboard saved →", out)
