"""Tests for error paths — stage failures, missing files, cycle resilience."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from lucian.agent import AgentConfig, LucianAgent, SelfEvolveOutcome
from lucian.exceptions import APIKeyMissing, StageError, StageFileNotFound

import adapt_weights
import adapt_resonance
import generate_archetypal_dream as gad


class StubClient:
    def __init__(self, reply: str = "stub"):
        self._reply = reply
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._reply))],
            usage=SimpleNamespace(total_tokens=0),
        )


# ── Agent creation ──────────────────────────────────────────────────────────

def test_agent_raises_on_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(APIKeyMissing):
        LucianAgent()


# ── run_daily_cycle resilience ──────────────────────────────────────────────

def test_cycle_collects_dream_error(tmp_path):
    config = AgentConfig(chat_log_dir=tmp_path / "chat")
    agent = LucianAgent(config=config, client=StubClient())

    agent.dream = lambda **kw: (_ for _ in ()).throw(RuntimeError("API down"))
    agent.reflect = lambda **kw: None
    agent.direction = lambda **kw: None
    agent.self_evolve = lambda apply=True: SelfEvolveOutcome(None, None)
    agent.journal = lambda **kw: None
    agent.daily_output = lambda **kw: None

    result = agent.run_daily_cycle(include_core_node=False)
    assert result.dream is None
    assert any("dream:" in e for e in result.errors)


def test_cycle_continues_after_reflection_failure(tmp_path):
    config = AgentConfig(chat_log_dir=tmp_path / "chat")
    agent = LucianAgent(config=config, client=StubClient())

    agent.dream = lambda **kw: SimpleNamespace(path=Path("/fake/dream.md"))
    agent.reflect = lambda **kw: (_ for _ in ()).throw(StageFileNotFound("no directive"))
    agent.direction = lambda **kw: SimpleNamespace(path=Path("/fake/dir.md"))
    agent.self_evolve = lambda apply=True: SelfEvolveOutcome(None, None)
    agent.journal = lambda **kw: None
    agent.daily_output = lambda **kw: None

    result = agent.run_daily_cycle()
    assert result.reflection is None
    assert result.direction is not None
    assert any("reflection:" in e for e in result.errors)


def test_cycle_with_all_stages_failing(tmp_path):
    config = AgentConfig(chat_log_dir=tmp_path / "chat")
    agent = LucianAgent(config=config, client=StubClient())

    def explode(**kw):
        raise RuntimeError("boom")

    agent.dream = explode
    agent.reflect = explode
    agent.direction = explode
    agent.self_evolve = lambda apply=True: SelfEvolveOutcome(None, None, errors=["adapt: boom"])
    agent.journal = explode
    agent.daily_output = explode
    agent.core_node = explode

    result = agent.run_daily_cycle(include_core_node=True)
    assert result.dream is None
    assert result.reflection is None
    assert result.direction is None
    assert result.journal is None
    assert result.output is None
    assert result.core_node is None
    assert len(result.errors) >= 6  # dream + reflect + direction + adapt + journal + output + core_node


# ── adapt_weights error paths ──────────────────────────────────────────────

def test_adapt_weights_raises_on_missing_reports(tmp_path):
    adapt_weights.weekly_dir = tmp_path / "empty_weekly"
    adapt_weights.weekly_dir.mkdir()
    with pytest.raises(StageFileNotFound):
        adapt_weights.adapt_archetype_weights()


def test_adapt_weights_raises_on_insufficient_dreams(tmp_path):
    adapt_weights.weekly_dir = tmp_path / "weekly"
    adapt_weights.weekly_dir.mkdir()
    report = adapt_weights.weekly_dir / "2025-01-01_report.md"
    report.write_text(
        "* **Strategist**: 1\n* **Idealist**: 0\n* **Shadow**: 0\n* **Child**: 0\n"
    )
    adapt_weights.bias_path = tmp_path / "bias.yaml"
    with pytest.raises(StageError, match="Fewer than 4"):
        adapt_weights.adapt_archetype_weights()


# ── adapt_resonance error paths ────────────────────────────────────────────

def test_adapt_resonance_raises_on_too_few_dreams(tmp_path, monkeypatch):
    monkeypatch.setattr(adapt_resonance, "DREAMS_DIR", tmp_path / "dreams")
    (tmp_path / "dreams").mkdir()
    # Only 1 dream file — fewer than the minimum 4
    (tmp_path / "dreams" / "only_one.md").write_text("Resonance Tag: Curiosity")

    with pytest.raises(StageError, match="Fewer than 4"):
        adapt_resonance.adapt_resonance_weights()


# ── generate_archetypal_dream parse edge cases ─────────────────────────────

def test_dream_parse_response_without_resonance_tag():
    from generate_archetypal_dream import _parse_response

    raw = "First paragraph.\nSecond paragraph.\nThird paragraph."
    resonance, paras, _ = _parse_response(raw, ("Curiosity", "Wonder"))
    assert resonance == "Resonance Tag: Curiosity · Wonder"  # fallback
    assert len(paras) == 3


def test_dream_parse_response_with_extra_resonance_lines():
    from generate_archetypal_dream import _parse_response

    raw = "Resonance Tag: Joy\nBody line.\nResonance tag: duplicate\nSecond body."
    resonance, paras, _ = _parse_response(raw, ("Fallback",))
    assert "Joy" in resonance
    assert len(paras) == 2  # duplicate line is skipped


# ── reflect alignment detection ─────────────────────────────────────────────

def test_ensure_alignment_appends_tag_when_missing():
    from reflect import _ensure_alignment_tag

    text = "The dream wrestled with the directive."
    result, tag = _ensure_alignment_tag(text)
    assert "Alignment:" in result
    assert tag in ("Aligned", "Challenged", "Ignored")


def test_ensure_alignment_preserves_existing_tag():
    from reflect import _ensure_alignment_tag

    text = "Some reflection.\n\nAlignment: Challenged"
    result, tag = _ensure_alignment_tag(text)
    assert tag == "Challenged"
    assert result == text  # unchanged


def test_ensure_alignment_detects_align_keyword():
    from reflect import _ensure_alignment_tag

    text = "The dream was well aligned with the directive."
    _, tag = _ensure_alignment_tag(text)
    assert tag == "Aligned"


def test_ensure_alignment_detects_challenge_keyword():
    from reflect import _ensure_alignment_tag

    text = "The dream challenged every expectation."
    _, tag = _ensure_alignment_tag(text)
    assert tag == "Challenged"
