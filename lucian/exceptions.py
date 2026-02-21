"""
Custom exception hierarchy for Lucian-core.

All domain-specific errors inherit from ``LucianError`` so callers can
catch the whole family with a single except clause when needed.
"""

from __future__ import annotations


class LucianError(Exception):
    """Base exception for every Lucian-specific error."""


class ConfigError(LucianError):
    """Raised when configuration is missing, invalid, or unparseable."""


class APIKeyMissing(ConfigError):
    """OPENAI_API_KEY is not set in the environment."""

    def __init__(self) -> None:
        super().__init__("OPENAI_API_KEY is missing from the environment.")


class StageFileNotFound(LucianError):
    """A required stage artefact (dream, directive, report, …) is missing."""


class StageError(LucianError):
    """A lifecycle stage failed for a non-file reason (e.g. insufficient data)."""


class MemoryError(LucianError):
    """Raised when the vector-memory layer encounters an unrecoverable problem."""
