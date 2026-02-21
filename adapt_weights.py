#!/usr/bin/env python3
"""
Stage 4 – Adaptive Archetype Weights
Reads the newest weekly report, detects imbalances, and updates
`config/archetype_bias.yaml`, which the daily generators import.

Refactored to expose adapt_archetype_weights() for orchestration.
"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

from lucian.constants import (
    ARCHETYPE_BIAS_PATH,
    ARCHETYPE_MAX_W,
    ARCHETYPE_MIN_W,
    ARCHETYPES,
    TARGET_ARCHETYPE_SHARE,
    WEEKLY_DIR,
)
from lucian.exceptions import StageError, StageFileNotFound

log = logging.getLogger("lucian.adapt_weights")

ARCH = ARCHETYPES
TARGET_SHARE = TARGET_ARCHETYPE_SHARE
MIN_W, MAX_W = ARCHETYPE_MIN_W, ARCHETYPE_MAX_W

MEM_ROOT = WEEKLY_DIR.parent  # kept for compatibility
weekly_dir = WEEKLY_DIR
bias_path = ARCHETYPE_BIAS_PATH


@dataclass
class WeightUpdateResult:
    weights: Mapping[str, float]
    path: Path | None
    updated: bool
    source_report: Path | None


def _latest_weekly_report() -> Path | None:
    reports = sorted(weekly_dir.glob("*_report.md"))
    return reports[-1] if reports else None


def _parse_counts(markdown: str) -> dict[str, int]:
    counts = {k: 0 for k in ARCH}
    for archetype in ARCH:
        match = re.search(rf"\*\*{archetype}\*\*:\s+(\d+)", markdown)
        if match:
            counts[archetype] = int(match.group(1))
    return counts


def adapt_archetype_weights(*, apply: bool = True) -> WeightUpdateResult:
    """
    Compute and optionally persist updated archetype weights.

    The algorithm normalises each archetype's observed frequency against
    a uniform target share (25 %) and multiplies the current bias weight
    by the resulting correction factor, clamped to [MIN_W, MAX_W].
    """

    report = _latest_weekly_report()
    if not report:
        raise StageFileNotFound("No weekly reports found; cannot adapt archetype weights.")

    counts = _parse_counts(report.read_text())
    total = sum(counts.values())
    if total < len(ARCH):
        raise StageError("Fewer than 4 dreams this week; skipping weight update.")

    bias = {k: 1.0 for k in ARCH}
    if bias_path.exists():
        loaded = yaml.safe_load(bias_path.read_text())
        if isinstance(loaded, dict):
            bias.update({k: float(v) for k, v in loaded.items()})

    for archetype in ARCH:
        actual_share = counts[archetype] / total if total else TARGET_SHARE
        factor = TARGET_SHARE / actual_share if actual_share else 2.0
        new_weight = max(MIN_W, min(MAX_W, round(bias[archetype] * factor, 3)))
        bias[archetype] = new_weight

    new_yaml = yaml.safe_dump(bias, sort_keys=False)

    if not apply:
        return WeightUpdateResult(weights=bias, path=None, updated=False, source_report=report)

    old_yaml = bias_path.read_text() if bias_path.exists() else ""
    if old_yaml == new_yaml:
        log.info("No bias change needed.")
        return WeightUpdateResult(weights=bias, path=bias_path, updated=False, source_report=report)

    diff = "\n".join(
        difflib.unified_diff(
            old_yaml.splitlines(),
            new_yaml.splitlines(),
            fromfile="old",
            tofile="new",
            lineterm="",
        )
    )
    if diff:
        log.debug("Weight diff:\n%s", diff)

    bias_path.parent.mkdir(parents=True, exist_ok=True)
    bias_path.write_text(new_yaml)
    log.info("Updated archetype weights → %s", bias_path)
    return WeightUpdateResult(weights=bias, path=bias_path, updated=True, source_report=report)


if __name__ == "__main__":
    adapt_archetype_weights()
