"""Tests for lucian.exceptions — custom exception hierarchy."""

from __future__ import annotations

import pytest

from lucian.exceptions import (
    APIKeyMissing,
    ConfigError,
    LucianError,
    MemoryError,
    StageError,
    StageFileNotFound,
)


def test_hierarchy_lucian_error_is_base():
    assert issubclass(ConfigError, LucianError)
    assert issubclass(StageFileNotFound, LucianError)
    assert issubclass(StageError, LucianError)
    assert issubclass(MemoryError, LucianError)


def test_api_key_missing_is_config_error():
    assert issubclass(APIKeyMissing, ConfigError)


def test_api_key_missing_has_default_message():
    exc = APIKeyMissing()
    assert "OPENAI_API_KEY" in str(exc)


def test_catch_all_lucian_errors():
    """Catching LucianError should catch every domain exception."""
    for cls in (APIKeyMissing, ConfigError, StageFileNotFound, StageError, MemoryError):
        with pytest.raises(LucianError):
            if cls is APIKeyMissing:
                raise cls()
            else:
                raise cls("test")


def test_stage_file_not_found_message():
    exc = StageFileNotFound("Missing dream file")
    assert "Missing dream file" in str(exc)


def test_stage_error_message():
    exc = StageError("Not enough data")
    assert "Not enough data" in str(exc)
