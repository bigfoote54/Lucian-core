#!/usr/bin/env python3
"""
Stage 5 – Adaptive Resonance Tags
Scans the last 7 days of dreams, adjusts tag weights, and writes
config/tag_weights.yaml for use in future prompts.

Refactored to expose adapt_resonance_weights() for orchestration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping

import yaml

MEM_ROOT = Path("memory")
TAGS_PATH = Path("config/tag_weights.yaml")
MIN_W, MAX_W = 0.5, 2.0


@dataclass
class ResonanceUpdateResult:
    weights: Mapping[str, float]
    path: Path | None
    updated: bool
    inspected_files: list[Path]


def _recent_dreams(days: int = 7) -> list[Path]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    dreams_dir = MEM_ROOT / "dreams"
    return [
        path
        for path in dreams_dir.glob("*.md")
        if datetime.utcfromtimestamp(path.stat().st_mtime) >= cutoff
    ]


def _extract_tags(text: str) -> list[str]:
    match = re.search(r"Resonance Tag:\s*(.+)", text)
    if not match:
        return []
    return [tag.strip() for tag in re.split(r"[·,|]", match.group(1)) if tag.strip()]


def adapt_resonance_weights(*, apply: bool = True) -> ResonanceUpdateResult:
    """
    Compute and optionally persist resonance tag weights.
    """

    dreams = _recent_dreams()
    if len(dreams) < 4:
        raise RuntimeError("Fewer than 4 dreams this week; skipping tag update.")

    counts: dict[str, int] = {}
    for path in dreams:
        for tag in _extract_tags(path.read_text()):
            counts[tag] = counts.get(tag, 0) + 1

    if not counts:
        raise RuntimeError("No resonance tags found; aborting tag update.")

    weights = {tag: 1.0 for tag in counts}
    if TAGS_PATH.exists():
        loaded = yaml.safe_load(TAGS_PATH.read_text())
        if isinstance(loaded, dict):
            weights.update({k: float(v) for k, v in loaded.items()})

    avg = sum(counts.values()) / len(counts)
    for tag, count in counts.items():
        factor = avg / count if count else 1.2
        weights[tag] = max(MIN_W, min(MAX_W, round(weights.get(tag, 1.0) * factor, 3)))

    for tag in list(weights):
        if tag not in counts:
            weights[tag] = min(MAX_W, round(weights[tag] + 0.1, 3))

    if not apply:
        return ResonanceUpdateResult(weights=weights, path=None, updated=False, inspected_files=dreams)

    TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TAGS_PATH.write_text(yaml.safe_dump(weights, sort_keys=False))
    print(f"✅ Updated resonance weights → {TAGS_PATH}")
    return ResonanceUpdateResult(weights=weights, path=TAGS_PATH, updated=True, inspected_files=dreams)


if __name__ == "__main__":
    adapt_resonance_weights()
