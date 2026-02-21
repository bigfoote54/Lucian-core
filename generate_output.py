#!/usr/bin/env python3
"""
Consolidates the latest dream + direction into a single daily output markdown.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lucian.constants import DIRECTION_DIR, DREAMS_DIR
from lucian.utils import latest_file

log = logging.getLogger("lucian.output")


@dataclass
class DailyOutput:
    path: Path
    dream_content: str
    resonance: str
    resonance_tag: str
    directive: str
    timestamp: datetime


def _extract_field(pattern: str, text: str, default: str = "N/A") -> str:
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else default


def generate_daily_output(
    *,
    dream_path: Path | None = None,
    direction_path: Path | None = None,
    out_path: Path | None = None,
) -> DailyOutput:
    today = datetime.now()
    output_path = out_path or Path("lucian_output.md")

    dream_file = dream_path or latest_file(DREAMS_DIR, "*_archetypal_dream.md")
    direction_file = direction_path or latest_file(DIRECTION_DIR, "*_direction.md")

    dream_text = dream_file.read_text().strip() if dream_file and dream_file.exists() else "No dream found."
    direction_text = (
        direction_file.read_text().strip() if direction_file and direction_file.exists() else "No direction found."
    )

    resonance = _extract_field(r"^Resonance:\s*(.*)", dream_text)
    resonance_tag = _extract_field(r"^Resonance Tag:\s*(.*)", dream_text)
    dream_content = _extract_field(r"## Dream\n\n(.+)", dream_text, dream_text)
    directive_content = _extract_field(r"## Directive\n\n(.+)", direction_text, direction_text)

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# 🌅 Lucian Daily Output — {today.strftime('%Y-%m-%d')}\n\n")
        handle.write("## 💭 Archetypal Dream\n")
        handle.write(f"Resonance: {resonance}\n\n")
        handle.write(f"Resonance Tag: {resonance_tag}\n\n")
        handle.write(dream_content + "\n\n")
        handle.write("---\n\n")
        handle.write("## 🧭 Daily Directive\n\n")
        handle.write(directive_content + "\n")

    log.info("Merged output written to → %s", output_path)
    return DailyOutput(
        path=output_path,
        dream_content=dream_content,
        resonance=resonance,
        resonance_tag=resonance_tag,
        directive=directive_content,
        timestamp=today,
    )


if __name__ == "__main__":
    generate_daily_output()
