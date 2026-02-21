#!/usr/bin/env python3
"""
Stage 5 – Adaptive Resonance Tags
Scans the last 7 days of dreams, adjusts tag weights, and writes
config/tag_weights.yaml for use in future prompts.

Refactored to expose adapt_resonance_weights() for orchestration.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping

import yaml

from lucian.constants import (
    DREAMS_DIR,
    RESONANCE_MAX_W,
    RESONANCE_MIN_W,
    TAG_WEIGHTS_PATH,
)
from lucian.exceptions import StageError

log = logging.getLogger("lucian.adapt_resonance")

MEM_ROOT = DREAMS_DIR.parent  # kept for test-patching compatibility
TAGS_PATH = TAG_WEIGHTS_PATH
MIN_W, MAX_W = RESONANCE_MIN_W, RESONANCE_MAX_W


@dataclass
class ResonanceUpdateResult:
    weights: Mapping[str, float]
    path: Path | None
    updated: bool
    inspected_files: list[Path]


def _recent_dreams(days: int = 7) -> list[Path]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return [
        path
        for path in DREAMS_DIR.glob("*.md")
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

    The algorithm counts tag occurrences across dreams from the last 7 days
    and adjusts each tag's weight inversely to its frequency so that
    under-represented tags are boosted. Unused tags receive a small +0.1
    nudge each cycle. All weights are clamped to [MIN_W, MAX_W].
    """

    dreams = _recent_dreams()
    if len(dreams) < 4:
        raise StageError("Fewer than 4 dreams this week; skipping tag update.")

    counts: dict[str, int] = {}
    for path in dreams:
        for tag in _extract_tags(path.read_text()):
            counts[tag] = counts.get(tag, 0) + 1

    if not counts:
        raise StageError("No resonance tags found; aborting tag update.")

    weights = {tag: 1.0 for tag in counts}
    if TAGS_PATH.exists():
        loaded = yaml.safe_load(TAGS_PATH.read_text())
        if isinstance(loaded, dict):
            weights.update({k: float(v) for k, v in loaded.items()})

    avg = sum(counts.values()) / len(counts)
    for tag, count in counts.items():
        factor = avg / count if count else 1.2
        weights[tag] = max(MIN_W, min(MAX_W, round(weights.get(tag, 1.0) * factor, 3)))

    # Boost tags that weren't seen this cycle so they get a chance next time
    for tag in list(weights):
        if tag not in counts:
            weights[tag] = min(MAX_W, round(weights[tag] + 0.1, 3))

    if not apply:
        return ResonanceUpdateResult(weights=weights, path=None, updated=False, inspected_files=dreams)

    TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TAGS_PATH.write_text(yaml.safe_dump(weights, sort_keys=False))
    log.info("Updated resonance weights → %s", TAGS_PATH)
    return ResonanceUpdateResult(weights=weights, path=TAGS_PATH, updated=True, inspected_files=dreams)


if __name__ == "__main__":
    adapt_resonance_weights()
