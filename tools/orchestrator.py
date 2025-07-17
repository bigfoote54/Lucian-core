#!/usr/bin/env python3
"""
orchestrator.py
Runs Lucian’s daily pipeline end-to-end, logs every stage, retries once on failure,
and records a run report in memory/system/logs/YYYY-MM-DD.json.
"""

import subprocess, json, traceback, time
from datetime import datetime
from pathlib import Path

STAGES = [
    ("journal",    ["python3", "generate_journal.py"]),      # optional – comment out if not used
    ("dream",      ["python3", "generate_archetypal_dream.py"]),
    ("reflect",    ["python3", "reflect.py"]),
    ("direction",  ["python3", "generate_direction.py"]),
    ("weekly",     ["python3", "generate_weekly_report.py"]), # runs, but is a no-op 6/7 days
]

LOG_DIR = Path("memory/system/logs"); LOG_DIR.mkdir(parents=True, exist_ok=True)
run_id  = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
report  = {"run_id": run_id, "stages": [], "status": "started", "started": run_id}

def run_stage(name, cmd, attempt=1):
    t0 = time.time()
    try:
        subprocess.check_call(cmd)
        status = "success"
    except subprocess.CalledProcessError as e:
        if attempt == 1:
            print(f"⚠️  {name} failed (retrying once) → {e}")
            return run_stage(name, cmd, attempt=2)
        status = f"error({e.returncode})"
    finally:
        report["stages"].append({
            "name": name,
            "status": status,
            "duration_s": round(time.time() - t0, 1)
        })
    if status.startswith("error"):
        raise RuntimeError(f"{name} failed")

for stage_name, stage_cmd in STAGES:
    try:
        run_stage(stage_name, stage_cmd)
    except Exception:
        report["status"] = "failed"
        report["error"]  = traceback.format_exc()
        break
else:
    report["status"] = "success"

report["ended"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
(Path(LOG_DIR) / f"{run_id}.json").write_text(json.dumps(report, indent=2))
print(f"🗒️  Orchestrator run finished → {LOG_DIR}/{run_id}.json")
if report["status"] != "success":
    exit(1)
