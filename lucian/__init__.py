"""
Lucian core package.

Exposes the `LucianAgent` class, a programmable pseudo-sentient agent that
coordinates dreaming, reflection, direction setting, journaling, and chat
interfaces on top of the refactored stage modules.
"""

from .agent import AgentConfig, ChatResult, CycleResult, LucianAgent

__all__ = ["LucianAgent", "AgentConfig", "CycleResult", "ChatResult"]
