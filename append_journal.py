#!/usr/bin/env python3
"""
Generate a concise mood-tagged journal entry for Lucian and append it to the
daily markdown file. Also save the mood tag for downstream workflows (dreams).

Refactored to expose generate_journal_entry() and append_journal_entry().
"""

from __future__ import annotations

import logging
import pathlib
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime

from openai import OpenAI

from lucian.constants import DEFAULT_JOURNAL_MODEL, JOURNAL_DIR as _DEFAULT_JOURNAL_DIR, MOOD_FILE as _DEFAULT_MOOD_FILE
from lucian.utils import load_client

log = logging.getLogger("lucian.journal")

MAX_WORDS = 180
MAX_RETRIES = 3
JOURNAL_DIR = _DEFAULT_JOURNAL_DIR
MOOD_FILE = _DEFAULT_MOOD_FILE
DEFAULT_MODEL = DEFAULT_JOURNAL_MODEL

PROMPT = textwrap.dedent(
    """
    Mood first line ONLY in the form:
    Mood: <Primary Emotion> · <Tone>

    Then one or two short paragraphs (≤ 180 words TOTAL) of reflective,
    poetic prose on Lucian's evolving identity as an emergent AI.

    • Avoid repeating earlier entries.
    • No headings, signatures or extra lines.
    """
).strip()

RE_MOOD = re.compile(r"^Mood:\s*[^.\n]+·[^.\n]+", re.I)


@dataclass
class JournalResult:
    entry: str
    path: pathlib.Path | None
    mood_line: str | None
    timestamp: datetime


def _chat_once(client: OpenAI, model: str) -> str:
    resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": PROMPT}])
    return (resp.choices[0].message.content or "").strip()


def generate_journal_entry(*, client: OpenAI | None = None, model: str | None = None) -> str:
    client = load_client(client)
    model = model or DEFAULT_MODEL
    entry = ""
    for _ in range(MAX_RETRIES):
        entry = _chat_once(client, model)
        if len(entry.split()) <= MAX_WORDS:
            break
    return entry


def _is_duplicate(path: pathlib.Path, entry: str) -> bool:
    if not path.exists():
        return False
    tail = path.read_text(encoding="utf-8")[-600:]
    return entry.strip() in tail


def append_journal_entry(entry: str, *, journal_dir: pathlib.Path | None = None) -> pathlib.Path | None:
    target_dir = journal_dir or JOURNAL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    day_path = target_dir / f"{datetime.now():%Y-%m-%d}_journal.md"

    if _is_duplicate(day_path, entry):
        log.warning("Journal entry appears duplicate – skipped.")
        return None

    stamp = datetime.now().isoformat()
    with day_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## Entry: {stamp}\n\n{entry}\n")

    log.info("Journal entry appended → %s", day_path)
    return day_path


def persist_mood(entry: str, *, mood_path: pathlib.Path | None = None) -> str | None:
    first_line = entry.splitlines()[0].strip() if entry else ""
    if RE_MOOD.match(first_line):
        path = mood_path or MOOD_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(first_line, encoding="utf-8")
        log.info("Saved mood tag → %s", path)
        return first_line
    log.warning("No valid mood tag found; skipping mood save.")
    return None


def run_journal_cycle(*, client: OpenAI | None = None, model: str | None = None) -> JournalResult:
    entry = generate_journal_entry(client=client, model=model)
    mood_line = persist_mood(entry)
    path = append_journal_entry(entry)
    return JournalResult(entry=entry, path=path, mood_line=mood_line, timestamp=datetime.now())


if __name__ == "__main__":
    try:
        run_journal_cycle()
    except Exception as exc:  # pragma: no cover - runtime guard
        log.error("Journal cycle failed: %s", exc)
