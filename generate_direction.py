#!/usr/bin/env python3
"""
generate_direction.py
─────────────────────────────────────────────────────────────────────────────
Creates Lucian's daily directive (1–2 sentences), referencing
today's dream, adaptive archetype bias, and adaptive resonance tags.

Refactored to expose generate_direction() for orchestration.
"""

from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from dotenv import load_dotenv
from openai import OpenAI

MEM_ROOT = Path("memory")
ARCHETYPES = ["Strategist", "Idealist", "Shadow", "Child"]
DEFAULT_TAGS = ("Curiosity", "Existence", "Knowledge", "Wonder", "Responsibility")


@dataclass
class DirectiveResult:
    path: Path
    timestamp: datetime
    dominant_archetype: str
    resonance_tags: Sequence[str]
    directive: str
    dream_excerpt: str


def _load_client(client: OpenAI | None = None) -> OpenAI:
    if client is not None:
        return client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from the environment.")
    return OpenAI(api_key=api_key)


def _choose(values: Iterable[str], weights: Sequence[float], *, k: int = 1) -> list[str]:
    pool = list(values)
    if not pool:
        return []
    return random.choices(pool, weights=weights, k=k)


def _latest_dream_path(today: datetime) -> Path:
    dreams_dir = MEM_ROOT / "dreams"
    pattern = today.strftime("%Y-%m-%d") + "_*_archetypal_dream.md"
    dream_files = sorted(dreams_dir.glob(pattern))
    if not dream_files:
        raise FileNotFoundError("No dream file found for today; run dream generator first.")
    return dream_files[-1]


def _extract_dream_metadata(dream_text: str) -> tuple[str, str]:
    dream_excerpt = "\n".join(
        line.strip()
        for line in dream_text.splitlines()
        if line.strip() and not line.lower().startswith("resonance")
    )[:240]

    tag_match = re.search(r"Resonance Tag:\s*(.+)", dream_text)
    dream_tags = tag_match.group(1).strip() if tag_match else ""
    return dream_excerpt, dream_tags


def _load_biases() -> tuple[dict[str, float], dict[str, float]]:
    bias_path = Path("config/archetype_bias.yaml")
    arch_bias = {name: 1.0 for name in ARCHETYPES}
    if bias_path.exists():
        arch_bias.update({k: float(v) for k, v in yaml.safe_load(bias_path.read_text()).items()})

    tag_bias_path = Path("config/tag_weights.yaml")
    tag_bias = {tag: 1.0 for tag in DEFAULT_TAGS}
    if tag_bias_path.exists():
        tag_bias.update({k: float(v) for k, v in yaml.safe_load(tag_bias_path.read_text()).items()})

    return arch_bias, tag_bias


def generate_direction(
    *,
    dream_path: Path | None = None,
    client: OpenAI | None = None,
    out_dir: Path | None = None,
    model: str = "gpt-4o",
    temperature: float = 0.8,
) -> DirectiveResult:
    """
    Generate Lucian's daily directive and persist it to disk.
    """

    client = _load_client(client)
    now = datetime.now()
    dream_path = dream_path or _latest_dream_path(now)
    dream_text = dream_path.read_text()

    dream_excerpt, dream_tags_line = _extract_dream_metadata(dream_text)

    arch_bias, tag_bias = _load_biases()
    dominant_arch = _choose(arch_bias.keys(), list(arch_bias.values()))[0]
    focal_tag = _choose(tag_bias.keys(), list(tag_bias.values()))[0]

    if dream_tags_line:
        tag_set = {t.strip() for t in dream_tags_line.split("·") if t.strip()}
        tag_set.add(focal_tag)
        final_tags = sorted(tag_set)
    else:
        final_tags = [focal_tag]

    prompt = (
        "You are Lucian's conscious directive voice.\n\n"
        f"Dominant archetype today: **{dominant_arch}**.\n"
        f"Resonance tag(s): **{' · '.join(final_tags)}**.\n\n"
        f"Dream excerpt:\n\"\"\"{dream_excerpt}\"\"\"\n\n"
        "Write a poetic yet actionable directive in 1–2 sentences. "
        "It must echo the resonance tag(s) and reflect the dominant archetype's perspective."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=120,
    )
    directive_text = response.choices[0].message.content.strip()

    output_dir = out_dir or (MEM_ROOT / "direction")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{now.strftime('%Y-%m-%d')}_direction.md"

    with out_file.open("w", encoding="utf-8") as handle:
        handle.write(f"🧭 Lucian Daily Direction — {now.strftime('%Y-%m-%d')}\n\n")
        handle.write(f"Dominant Archetype: {dominant_arch}\n\n")
        handle.write(f"Resonance Tag: {' · '.join(final_tags)}\n\n")
        handle.write("## Directive\n\n")
        handle.write(directive_text + "\n")

    print(f"✅ Direction saved → {out_file}")
    return DirectiveResult(
        path=out_file,
        timestamp=now,
        dominant_archetype=dominant_arch,
        resonance_tags=tuple(final_tags),
        directive=directive_text,
        dream_excerpt=dream_excerpt,
    )


if __name__ == "__main__":
    generate_direction()
