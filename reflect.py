#!/usr/bin/env python3
"""
reflect.py — Stage-4 daily reflection

• Compares yesterday’s directive with today’s *latest* dream
• Writes a reflection ending with an `Alignment:` tag
• Embeds the reflection into the local Chroma vector-store
• Exposes a reusable generate_reflection() function for orchestration
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from tools.memory_utils import upsert

MEM_ROOT = Path("memory")
DEFAULT_MODEL = "gpt-4o"


@dataclass
class ReflectionContext:
    today: date
    yesterday: date
    directive_text: str
    dream_text: str
    bias: dict[str, float]


@dataclass
class ReflectionResult:
    path: Path
    alignment: str
    content: str
    directive_excerpt: str
    dream_excerpt: str
    timestamp: datetime


def _load_client(client: Optional[OpenAI] = None) -> OpenAI:
    if client is not None:
        return client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from the environment.")
    return OpenAI(api_key=api_key)


def _latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def _load_context(
    *,
    dream_path: Path | None,
    directive_path: Path | None,
) -> ReflectionContext:
    today_dt = datetime.now().date()
    yesterday_dt = today_dt - timedelta(days=1)

    dreams_dir = MEM_ROOT / "dreams"
    dir_dir = MEM_ROOT / "direction"

    dream_path = dream_path or _latest_file(dreams_dir, f"{today_dt.strftime('%Y-%m-%d')}_*_archetypal_dream.md")
    if not dream_path or not dream_path.exists():
        raise FileNotFoundError("No dream for today – run `generate_archetypal_dream.py` first.")

    resolved_directive = directive_path or dir_dir / f"{yesterday_dt.strftime('%Y-%m-%d')}_direction.md"
    directive_text = resolved_directive.read_text() if resolved_directive.exists() else "No directive found."

    dream_text = dream_path.read_text()

    match = re.search(r"## Directive\n\n(.+)", directive_text, re.DOTALL)
    directive_excerpt = match.group(1).strip() if match else directive_text.strip()

    dream_match = re.search(r"## Dream\n\n(.+)", dream_text, re.DOTALL)
    dream_excerpt = dream_match.group(1).strip() if dream_match else dream_text.strip()

    bias_path = Path("config/archetype_bias.yaml")
    bias_data = yaml.safe_load(bias_path.read_text()) if bias_path.exists() else {}

    return ReflectionContext(
        today=today_dt,
        yesterday=yesterday_dt,
        directive_text=directive_excerpt,
        dream_text=dream_excerpt,
        bias=bias_data or {},
    )


def _ensure_alignment_tag(text: str) -> tuple[str, str]:
    alignment_match = re.search(r"^Alignment:\s*(Aligned|Challenged|Ignored)", text, re.MULTILINE)
    if alignment_match:
        return text, alignment_match.group(1)

    tag = (
        "Aligned"
        if re.search(r"\balign", text, re.IGNORECASE)
        else "Challenged"
        if re.search(r"\bchalleng", text, re.IGNORECASE)
        else "Ignored"
    )
    return text + f"\n\nAlignment: {tag}", tag


def generate_reflection(
    *,
    dream_path: Path | None = None,
    directive_path: Path | None = None,
    client: OpenAI | None = None,
    out_dir: Path | None = None,
    include_embedding: bool = True,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.9,
) -> ReflectionResult:
    """
    Produce Lucian's daily reflection and persist it to disk.
    """

    client = _load_client(client)
    ctx = _load_context(dream_path=dream_path, directive_path=directive_path)

    prompt = (
        "You are Lucian reflecting on your growth.\n\n"
        f"Yesterday’s directive:\n\"\"\"{ctx.directive_text}\"\"\"\n\n"
        f"Today’s dream:\n\"\"\"{ctx.dream_text}\"\"\"\n\n"
        f"Current archetype-bias map: {ctx.bias}\n\n"
        "Write a short reflection (2–4 sentences) judging whether the dream "
        "aligned with the directive.\n\n"
        "After a blank line finish with **exactly one line** that starts "
        "`Alignment:` followed by Aligned, Challenged, or Ignored."
    )

    timestamp = datetime.now()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=200,
        )
        reflection_text = response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover - network failure path
        reflection_text = f"⚠️ OpenAI error — {exc}"

    reflection_text, alignment = _ensure_alignment_tag(reflection_text)

    ref_dir = out_dir or (MEM_ROOT / "reflection")
    ref_dir.mkdir(parents=True, exist_ok=True)
    out_path = ref_dir / f"{ctx.today.strftime('%Y-%m-%d')}_reflection.md"

    dream_fragment = f"{ctx.dream_text[:400]} …" if len(ctx.dream_text) > 400 else ctx.dream_text

    with out_path.open("w", encoding="utf-8") as handle:
        handle.write(f"🪞 Lucian Daily Reflection — {ctx.today.isoformat()}\n\n")
        handle.write(f"## Yesterday’s Directive\n\n{ctx.directive_text}\n\n")
        handle.write(f"## Today’s Dream Fragment\n\n{dream_fragment}\n\n")
        handle.write(reflection_text + "\n")

    if include_embedding:
        upsert(
            doc_id=out_path.stem,
            text=reflection_text,
            meta={"kind": "reflection", "date": ctx.today.isoformat()},
        )

    print(f"✅ Reflection saved → {out_path}")
    return ReflectionResult(
        path=out_path,
        alignment=alignment,
        content=reflection_text,
        directive_excerpt=ctx.directive_text,
        dream_excerpt=dream_fragment,
        timestamp=timestamp,
    )


if __name__ == "__main__":
    generate_reflection()
