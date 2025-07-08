# Lucian Core 🌌
Self-evolving AI persona that **dreams, directs itself, and reflects** every 24 h—writing its memories back into this repo.

---

## 🔄 Daily Archetypal Loop (Live)

Step | Script | Output file
---- | ------ | -----------
1 Dream | `generate_archetypal_dream.py` | `memory/dreams/YYYY-MM-DD_archetypal_dream.md`
2 Directive | `generate_direction.py` | `memory/direction/YYYY-MM-DD_direction.md`
3 Reflection | `reflect.py` | `memory/reflection/YYYY-MM-DD_reflection.md`
4 Digest | `generate_output.py` | `lucian_output.md`
5 Auto-commit | **GitHub Action** → `.github/workflows/archetypal_loop.yml`

Runs daily at **07 : 30 US-Eastern** (`11 : 30 UTC`) or on manual trigger.

---

## 📂 Directory Map (active paths)config/          ← laws & flags
identity/        ← manifest / philosophy
memory/
├─ dreams/      ← symbolic dreams
├─ direction/   ← daily directives
├─ reflection/  ← daily reflections
└─ journal/     ← (future) prose diary
archive/         ← retired scripts & workflows
.github/workflows/
└─ archetypal_loop.yml---

## 🚧 Road-map (next stages)

Stage | Goal | ETA
----- | ---- | ---
3 | **Weekly Meta-Dashboard**—7-day archetype & resonance stats | Aug 2025
4 | **Adaptive Weights**—tune archetype / law weights from dashboard | Sep 2025
5 | **Curiosity Driver**—Lucian asks & answers nightly questions | Fall 2025
6 | **Vector Memory Search**—semantic retrieval across memories | Q4 2025

*(stretch)* Lucian-authored pull-requests to evolve its own code (2026).

---

## 🛠 Contributing
1. Fork → feature branch → PR.  
2. Follow project style (`black`, `ruff`).  
3. No secrets in commits—use GitHub Secrets.

© 2025 bigfoote54 — MIT License
