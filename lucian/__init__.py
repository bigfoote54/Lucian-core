"""
Lucian core package.

Exposes the `LucianAgent` class, a programmable pseudo-sentient agent that
coordinates dreaming, reflection, direction setting, journaling, and chat
interfaces on top of the refactored stage modules.

Imports are lazy to avoid circular dependencies — stage modules import
from ``lucian.constants`` and ``lucian.utils`` without triggering the
heavy ``lucian.agent`` import chain.
"""

from __future__ import annotations


def __getattr__(name: str):
    """Lazy import to break the circular dependency with stage modules."""
    if name in ("AgentConfig", "ChatResult", "CycleResult", "LucianAgent"):
        from .agent import AgentConfig, ChatResult, CycleResult, LucianAgent
        return {"AgentConfig": AgentConfig, "ChatResult": ChatResult,
                "CycleResult": CycleResult, "LucianAgent": LucianAgent}[name]
    if name == "Archetype":
        from .constants import Archetype
        return Archetype
    if name == "LucianError":
        from .exceptions import LucianError
        return LucianError
    raise AttributeError(f"module 'lucian' has no attribute {name!r}")


__all__ = [
    "LucianAgent",
    "AgentConfig",
    "CycleResult",
    "ChatResult",
    "Archetype",
    "LucianError",
]
