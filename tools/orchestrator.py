#!/usr/bin/env python3
"""
tools/orchestrator.py
─────────────────────────────────────────────────────────────────────────────
Central runner coordinating Lucian’s daily evolution.

Modes
-----
1. agent  (default) — uses LucianAgent to run the full pseudo-sentient cycle
2. legacy — calls individual stage scripts sequentially (previous behaviour)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

from lucian import LucianAgent, AgentConfig

# ─── configuration ─────────────────────────────────────────────────────────
STAGES = [
    ("💭 dream", "generate_archetypal_dream.py"),
    ("🪞 reflect", "reflect.py"),
    ("🧭 direction", "generate_direction.py"),
    ("⚖️  adapt-weights", "adapt_weights.py"),
    ("🎚 adapt-tags", "adapt_resonance.py"),
    ("📓 journal", "append_journal.py"),
    ("🎬 output", "generate_output.py"),
    ("🕸 core-node", "generate_core_node.py"),
]

RETRY_LIMIT = 1
LOG_DIR = Path("memory/system/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.utcnow():%Y-%m-%dT%H-%M-%SZ}_orchestrator.log"


# ─── logging helper ────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(msg)
    if LOG_FILE.exists():
        content = LOG_FILE.read_text()
        LOG_FILE.write_text(content + msg + "\n")
    else:
        LOG_FILE.write_text(msg + "\n")


# ─── legacy runner ─────────────────────────────────────────────────────────
def run_stage(label: str, script: str) -> None:
    if not Path(script).exists():
        log(f"⚠️  {label:12} — skipped (missing {script})")
        return

    for attempt in range(RETRY_LIMIT + 1):
        cmd = ["python3", script]
        log(f"▶️  {label:12} — running: {' '.join(cmd)} (try {attempt + 1})")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            log(res.stdout)
        if res.returncode == 0:
            log(f"✅ {label:12} — success\n")
            return
        log(f"❌ {label:12} — exit {res.returncode}\n{res.stderr}")
        if attempt < RETRY_LIMIT:
            time.sleep(3)
    raise RuntimeError(f"{label} failed after {RETRY_LIMIT + 1} attempts")


def run_legacy() -> None:
    log("🕰  Running legacy stage scripts\n")
    for label, script in STAGES:
        run_stage(label, script)


# ─── agent runner ──────────────────────────────────────────────────────────
def summarise_cycle(agent: LucianAgent, include_core_node: bool, include_journal: bool, include_output: bool, adapt_biases: bool) -> None:
    log("🧠 Launching LucianAgent daily cycle\n")
    result = agent.run_daily_cycle(
        include_core_node=include_core_node,
        include_journal=include_journal,
        include_output=include_output,
        adapt_biases=adapt_biases,
    )

    def stage_status(name: str, obj) -> Tuple[str, str]:
        return (name, "✅" if obj is not None else "⚪️")

    status_lines: Iterable[Tuple[str, str]] = [
        stage_status("dream", result.dream),
        stage_status("reflection", result.reflection),
        stage_status("direction", result.direction),
        stage_status("archetype", result.archetype_weights),
        stage_status("resonance", result.resonance_weights),
    ]
    if include_journal:
        status_lines = list(status_lines) + [stage_status("journal", result.journal)]
    if include_output:
        status_lines = list(status_lines) + [stage_status("output", result.output)]
    if include_core_node:
        status_lines = list(status_lines) + [stage_status("core_node", result.core_node)]

    log("🔁 Cycle summary:")
    for name, status in status_lines:
        log(f"  {status} {name}")

    if result.errors:
        log("\n⚠️  Cycle warnings:")
        for err in result.errors:
            log(f"  • {err}")
    else:
        log("\n🌟 Cycle completed without reported errors.")


# ─── CLI parsing ───────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Lucian's daily self-evolution cycle.")
    parser.add_argument("--mode", choices={"agent", "legacy"}, default="agent", help="Execution strategy (default: agent).")
    parser.add_argument("--skip-journal", action="store_true", help="Skip journal generation stage.")
    parser.add_argument("--skip-output", action="store_true", help="Skip consolidated daily output generation.")
    parser.add_argument("--include-core-node", action="store_true", help="Generate the core memory node.")
    parser.add_argument("--skip-adapt", action="store_true", help="Skip adaptive weight/tag updates.")
    return parser.parse_args()


# ─── main ──────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    log(f"🛫 Orchestrator started {datetime.utcnow():%Y-%m-%d %H:%M:%S}Z — mode={args.mode}\n")

    try:
        if args.mode == "legacy":
            run_legacy()
        else:
            agent = LucianAgent(config=AgentConfig())
            summarise_cycle(
                agent=agent,
                include_core_node=args.include_core_node,
                include_journal=not args.skip_journal,
                include_output=not args.skip_output,
                adapt_biases=not args.skip_adapt,
            )
    except Exception as exc:
        log(f"🛑 Orchestrator aborted — {exc}")
        sys.exit(1)

    log("🏁 Orchestrator finished OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
