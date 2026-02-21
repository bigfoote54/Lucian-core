"""
Centralised constants for the Lucian-core project.

Every hard-coded value that was previously scattered across stage modules
now lives here so there is a single source of truth.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


# ── Archetypes ───────────────────────────────────────────────────────────────
class Archetype(str, Enum):
    STRATEGIST = "Strategist"
    IDEALIST = "Idealist"
    SHADOW = "Shadow"
    CHILD = "Child"


ARCHETYPES: list[str] = [a.value for a in Archetype]

DEFAULT_TAGS: tuple[str, ...] = (
    "Curiosity",
    "Existence",
    "Knowledge",
    "Wonder",
    "Responsibility",
)

# ── Paths ────────────────────────────────────────────────────────────────────
MEM_ROOT = Path("memory")
DREAMS_DIR = MEM_ROOT / "dreams"
DIRECTION_DIR = MEM_ROOT / "direction"
REFLECTION_DIR = MEM_ROOT / "reflection"
JOURNAL_DIR = MEM_ROOT / "journal"
CORE_NODES_DIR = MEM_ROOT / "core_nodes"
WEEKLY_DIR = MEM_ROOT / "weekly"
CHAT_DIR = MEM_ROOT / "chat"
LOG_DIR = MEM_ROOT / "system" / "logs"
CHROMA_PATH = MEM_ROOT / "system" / "chroma"

ARCHETYPE_BIAS_PATH = Path("config/archetype_bias.yaml")
TAG_WEIGHTS_PATH = Path("config/tag_weights.yaml")
MOOD_FILE = DREAMS_DIR / "_latest_mood.txt"

# ── Model defaults ───────────────────────────────────────────────────────────
DEFAULT_MODEL = "gpt-4o"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_JOURNAL_MODEL = "gpt-4"
EMBED_MODEL = "text-embedding-3-small"

# ── Weight clipping ranges ───────────────────────────────────────────────────
ARCHETYPE_MIN_W = 0.3
ARCHETYPE_MAX_W = 3.0
RESONANCE_MIN_W = 0.5
RESONANCE_MAX_W = 2.0

# Ideal share per archetype (uniform distribution)
TARGET_ARCHETYPE_SHARE = 1 / len(ARCHETYPES)
