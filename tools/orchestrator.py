#!/usr/bin/env python3
"""
tools/orchestrator.py
─────────────────────────────────────────────────────────────────────────────
Central runner that coordinates Lucian-core’s daily stages.

Order:
  1. generate_archetypal_dream.py   → memory/dreams/
  2. reflect.py                     → memory/reflection/
  3. generate_direction.py          → memory/direction/
  4. adapt_weights.py               → config/archetype_bias.yaml
  5. adapt_resonance.py             → config/tag_weights.yaml
  6. append_journal.py              → memory/journal/   (optional ❔)
  7. generate_output.py             → memory/output/    (optional ❔)
  8. generate_core_node.py          → memory/graph/     (optional ❔)
"""

from pathlib import Path
from datetime import datetime
import subprocess, sys, time, textwrap

# ─── configuration ─────────────────────────────────────────────────────────
STAGES = [
    ("💭 dream",         "generate_archetypal_dream.py"),
    ("🪞 reflect",       "reflect.py"),
    ("🧭 direction",     "generate_direction.py"),
    ("⚖️  adapt-weights","adapt_weights.py"),
    ("🎚 adapt-tags",    "adapt_resonance.py"),
    # optional extras (leave them in even if they noop – they’ll be skipped
    # gracefully when the files don’t exist)
    ("📓 journal",       "append_journal.py"),
    ("🎬 output",        "generate_output.py"),
    ("🕸 core-node",     "generate_core_node.py"),
]

RETRY_LIMIT = 1               # number of *additional* attempts on failure
LOG_DIR     = Path("memory/system/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE    = LOG_DIR / f"{datetime.utcnow():%Y-%m-%dT%H-%M-%SZ}_orchestrator.log"

# ─── helpers ───────────────────────────────────────────────────────────────
def log(msg: str):
    print(msg)
    LOG_FILE.write_text(LOG_FILE.read_text() + msg + "\n" if LOG_FILE.exists() else msg + "\n")

def run_stage(label: str, script: str):
    """Run a stage, retrying up to RETRY_LIMIT on non-zero exit."""
    if not Path(script).exists():
        log(f"⚠️  {label:12} — skipped (missing {script})")
        return

    for attempt in range(RETRY_LIMIT + 1):
        cmd = ["python3", script]
        log(f"▶️  {label:12} — running: {' '.join(cmd)} (try {attempt+1})")
        res = subprocess.run(cmd, capture_output=True, text=True)
        log(res.stdout)
        if res.returncode == 0:
            log(f"✅ {label:12} — success\n")
            return
        log(f"❌ {label:12} — exit {res.returncode}\n{res.stderr}")
        if attempt < RETRY_LIMIT:
            time.sleep(3)      # brief back-off
    # after retries
    raise RuntimeError(f"{label} failed after {RETRY_LIMIT+1} attempts")

# ─── main loop ─────────────────────────────────────────────────────────────
def main():
    log(f"🛫 Orchestrator started {datetime.utcnow():%Y-%m-%d %H:%M:%S}Z\n")

    try:
        for label, script in STAGES:
            run_stage(label, script)
    except Exception as e:
        log(f"🛑 Orchestrator aborted — {e}")
        sys.exit(1)

    log("🏁 Orchestrator finished OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
