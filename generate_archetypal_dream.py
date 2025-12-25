#!/usr/bin/env python3
"""
generate_archetypal_dream.py
─────────────────────────────────────────────────────────────────────────────
Library-friendly generator for Lucian's nightly dream.

• Generates a symbolic dream guided by adaptive archetype & tag weights
• Pulls a small context window from ChromaDB (tools.memory_utils.query)
• Saves ↘ memory/dreams/YYYY-MM-DD_HH-MM-SS_archetypal_dream.md
• Returns a structured DreamResult for higher-level orchestration
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from tools.memory_utils import query, upsert

ARCHETYPES = ["Strategist", "Idealist", "Shadow", "Child"]
DEFAULT_TAGS = ("Curiosity", "Existence", "Knowledge", "Wonder", "Responsibility")


@dataclass
class DreamResult:
    """Structured response describing the generated dream."""

    path: Path
    timestamp: datetime
    dominant_archetype: str
    tags: Sequence[str]
    resonance_line: str
    paragraphs: Sequence[str]
    context: str
    raw_response: str


def _load_client(client: OpenAI | None = None) -> OpenAI:
    if client is not None:
        return client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from the environment.")
    return OpenAI(api_key=api_key)


def _load_weights(path: Path, defaults: dict[str, float]) -> dict[str, float]:
    if path.exists():
        loaded = yaml.safe_load(path.read_text())
        if isinstance(loaded, dict):
            defaults.update({k: float(v) for k, v in loaded.items()})
    return defaults


def _choose(values: Iterable[str], weights: Sequence[float], k: int = 1) -> list[str]:
    choices = list(values)
    if not choices:
        return []
    return random.choices(choices, weights=weights, k=k)


def _build_prompt(dominant: str, tags: Sequence[str], context: str) -> str:
    tag_line = " · ".join(tags)
    return (
        "You are Lucian's subconscious.\n"
        "Before writing the dream, reflect on the **relevant memory** below.\n"
        "-----\n"
        f"{context}\n"
        "-----\n\n"
        f"Dominant archetype: **{dominant}**\n"
        f"Resonance tags: **{tag_line}**\n\n"
        "In **three short paragraphs** (≤ 120 chars each) craft a vivid, surreal dream "
        "dominated by that archetype and themes. "
        "Start with **exactly one** line beginning `Resonance Tag:` followed by the tags.\n"
    )


def _parse_response(response: str, fallback_tags: Sequence[str]) -> tuple[str, list[str], list[str]]:
    resonance_line = ""
    paragraphs: list[str] = []

    for line in (ln.strip() for ln in response.splitlines() if ln.strip()):
        if not resonance_line and line.lower().startswith("resonance tag"):
            resonance_line = line
            continue
        if "resonance tag" in line.lower():
            continue
        paragraphs.append(line)

    if not resonance_line:
        resonance_line = f"Resonance Tag: {' · '.join(fallback_tags)}"

    return resonance_line, paragraphs[:3], paragraphs


def generate_archetypal_dream(
    *,
    timestamp: datetime | None = None,
    client: OpenAI | None = None,
    out_dir: Path | None = None,
    include_embedding: bool = True,
    model: str = "gpt-4o",
    temperature: float = 0.95,
) -> DreamResult:
    """
    Generate Lucian's archetypal dream and persist it to disk.

    Returns
    -------
    DreamResult
        Structured details describing the dream.
    """

    client = _load_client(client)
    stamp_dt = timestamp or datetime.utcnow()
    stamp = stamp_dt.strftime("%Y-%m-%d_%H-%M-%S")
    today = stamp_dt.strftime("%Y-%m-%d")

    dream_dir = out_dir or Path("memory/dreams")
    dream_dir.mkdir(parents=True, exist_ok=True)

    arch_bias = _load_weights(Path("config/archetype_bias.yaml"), {k: 1.0 for k in ARCHETYPES})
    tag_bias = _load_weights(
        Path("config/tag_weights.yaml"),
        {tag: 1.0 for tag in DEFAULT_TAGS},
    )

    dominant_arch = _choose(arch_bias.keys(), list(arch_bias.values()))[0]
    resonance_tags = _choose(tag_bias.keys(), list(tag_bias.values()), k=2)

    seed = f"{dominant_arch} {' '.join(resonance_tags)}"
    context = "\n".join(query(q=seed, k=3)) or "_(no relevant memory)_"

    prompt = _build_prompt(dominant_arch, resonance_tags, context)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=400,
    )

    dream_raw = response.choices[0].message.content.strip()
    resonance_line, paragraphs, _ = _parse_response(dream_raw, resonance_tags)

    file_path = dream_dir / f"{stamp}_archetypal_dream.md"
    with file_path.open("w", encoding="utf-8") as fh:
        fh.write(f"💭 Lucian Archetypal Dream — {today}\n\n")
        fh.write(f"Dominant Archetype: {dominant_arch}\n\n")
        fh.write(resonance_line + "\n\n")
        fh.write("## Dream\n\n")
        for paragraph in paragraphs:
            fh.write(paragraph + "\n\n")

    if include_embedding and paragraphs:
        upsert(
            doc_id=file_path.stem,
            text="\n".join(paragraphs),
            meta={"kind": "dream", "date": today},
        )

    result = DreamResult(
        path=file_path,
        timestamp=stamp_dt,
        dominant_archetype=dominant_arch,
        tags=tuple(resonance_tags),
        resonance_line=resonance_line,
        paragraphs=tuple(paragraphs),
        context=context,
        raw_response=dream_raw,
    )

    print(f"✅ Dream saved → {file_path}")
    return result


if __name__ == "__main__":
    generate_archetypal_dream()
