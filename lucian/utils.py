"""
Shared helper functions used by multiple stage modules.

Consolidates ``_load_client``, ``_latest_file``, ``_load_weights``,
and ``_choose`` which were previously duplicated across 5+ files.
"""

from __future__ import annotations

import logging
import os
import random
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from lucian.exceptions import APIKeyMissing

log = logging.getLogger("lucian")


def load_client(client: OpenAI | None = None) -> OpenAI:
    """Return the provided client, or create one from the environment."""
    if client is not None:
        return client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise APIKeyMissing()
    return OpenAI(api_key=api_key)


def latest_file(directory: Path, pattern: str) -> Path | None:
    """Return the most recent file matching *pattern* inside *directory*."""
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def load_weights(path: Path, defaults: dict[str, float]) -> dict[str, float]:
    """Load YAML weights from *path*, merging with *defaults*.

    Returns a new dict (does not mutate *defaults*).
    """
    merged = dict(defaults)
    if path.exists():
        loaded = yaml.safe_load(path.read_text())
        if isinstance(loaded, dict):
            merged.update({k: float(v) for k, v in loaded.items()})
    return merged


def weighted_choice(
    values: Iterable[str],
    weights: Sequence[float],
    *,
    k: int = 1,
) -> list[str]:
    """Weighted random sample from *values* (with replacement)."""
    pool = list(values)
    if not pool:
        return []
    return random.choices(pool, weights=weights, k=k)
