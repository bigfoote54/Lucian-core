"""Shared fixtures for Lucian-core tests."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


class DummyChatClient:
    """Fake OpenAI client that returns a canned reply for any chat completion."""

    def __init__(self, content: str = "stub response"):
        self._content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))],
            usage=SimpleNamespace(total_tokens=kwargs.get("max_tokens", 0)),
        )


@pytest.fixture()
def dummy_client():
    """Return a factory that builds a DummyChatClient with a given reply."""
    return DummyChatClient


@pytest.fixture()
def patch_memory(monkeypatch):
    """Neuter the ChromaDB calls so tests never hit a real vector store."""
    import tools.memory_utils as mu

    monkeypatch.setattr(mu, "embed", lambda text: [0.0] * 8)
    monkeypatch.setattr(mu, "upsert", lambda doc_id, text, meta=None: None)
    monkeypatch.setattr(mu, "query", lambda q, k=3, **kw: [])
