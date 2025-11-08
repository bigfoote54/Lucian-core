#!/usr/bin/env python3
"""
Stage 4 – Adaptive Archetype Weights
Reads the newest weekly report, detects imbalances, and updates
`config/archetype_bias.yaml`, which the daily generators import.

Refactored to expose adapt_archetype_weights() for orchestration.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

ARCH = ["Strategist", "Idealist", "Shadow", "Child"]
TARGET_SHARE = 1 / len(ARCH)  # ideal 25% each
MIN_W, MAX_W = 0.3, 3.0  # clip range for weights

MEM_ROOT = Path("memory")
weekly_dir = MEM_ROOT / "weekly"
bias_path = Path("config/archetype_bias.yaml")


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
    """

    report = _latest_weekly_report()
    if not report:
        raise FileNotFoundError("No weekly reports found; cannot adapt archetype weights.")

    counts = _parse_counts(report.read_text())
    total = sum(counts.values())
    if total < len(ARCH):
        raise RuntimeError("Fewer than 4 dreams this week; skipping weight update.")

    bias = {k: 1.0 for k in ARCH}
    if bias_path.exists():
        bias.update({k: float(v) for k, v in yaml.safe_load(bias_path.read_text()).items()})

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
        print("No bias change needed.")
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
        print("Diff:\n" + diff)

    bias_path.parent.mkdir(parents=True, exist_ok=True)
    bias_path.write_text(new_yaml)
    print(f"✅ Updated archetype weights → {bias_path}")
    return WeightUpdateResult(weights=bias, path=bias_path, updated=True, source_report=report)


if __name__ == "__main__":
    adapt_archetype_weights()
