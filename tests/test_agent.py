from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from adapt_resonance import ResonanceUpdateResult
from adapt_weights import WeightUpdateResult
from append_journal import JournalResult
from generate_archetypal_dream import DreamResult
from generate_core_node import CoreNodeResult
from generate_direction import DirectiveResult
from generate_output import DailyOutput
from lucian.agent import AgentConfig, ChatResult, LucianAgent, SelfEvolveOutcome
from reflect import ReflectionResult


class StubClient:
    def __init__(self, reply: str):
        self._reply = reply
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._reply))],
            usage=SimpleNamespace(total_tokens=kwargs.get("max_tokens", 0)),
        )


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stub")
    return path


def test_run_daily_cycle_aggregates_results(tmp_path, monkeypatch):
    config = AgentConfig(chat_log_dir=tmp_path / "chat_logs")
    agent = LucianAgent(config=config, client=StubClient("unused"))

    dream_path = _touch(tmp_path / "dream.md")
    dream_result = DreamResult(
        path=dream_path,
        timestamp=datetime.utcnow(),
        dominant_archetype="Strategist",
        tags=("Curiosity", "Wonder"),
        resonance_line="Resonance Tag: Curiosity · Wonder",
        paragraphs=("p1", "p2", "p3"),
        context="ctx",
        raw_response="raw",
    )

    reflection_result = ReflectionResult(
        path=_touch(tmp_path / "reflection.md"),
        alignment="Aligned",
        content="Reflection text\n\nAlignment: Aligned",
        directive_excerpt="Directive",
        dream_excerpt="Dream fragment",
        timestamp=datetime.utcnow(),
    )

    direction_result = DirectiveResult(
        path=_touch(tmp_path / "direction.md"),
        timestamp=datetime.utcnow(),
        dominant_archetype="Strategist",
        resonance_tags=("Curiosity",),
        directive="Move with curiosity.",
        dream_excerpt="Dream fragment",
    )

    journal_result = JournalResult(
        entry="Mood: Calm · Bright\nEntry body.",
        path=_touch(tmp_path / "journal.md"),
        mood_line="Mood: Calm · Bright",
        timestamp=datetime.utcnow(),
    )

    output_result = DailyOutput(
        path=_touch(tmp_path / "output.md"),
        dream_content="Dream content",
        resonance="Curiosity",
        resonance_tag="Curiosity",
        directive="Directive body",
        timestamp=datetime.utcnow(),
    )

    core_result = CoreNodeResult(
        path=_touch(tmp_path / "core.md"),
        content="Core node",
        timestamp=datetime.utcnow(),
        journal_path=journal_result.path,
        dream_path=dream_result.path,
    )

    def fake_self_evolve(apply=True):
        return SelfEvolveOutcome(
            archetype_weights=WeightUpdateResult(weights={"Strategist": 1.2}, path=tmp_path / "bias.yaml", updated=True, source_report=None),
            resonance_weights=ResonanceUpdateResult(weights={"Curiosity": 1.1}, path=tmp_path / "tags.yaml", updated=True, inspected_files=[]),
            errors=["adapt_resonance: skipped"],
        )

    agent.dream = lambda **kwargs: dream_result
    agent.reflect = lambda **kwargs: reflection_result
    agent.direction = lambda **kwargs: direction_result
    agent.journal = lambda **kwargs: journal_result
    agent.daily_output = lambda **kwargs: output_result
    agent.core_node = lambda **kwargs: core_result
    agent.self_evolve = fake_self_evolve

    cycle = agent.run_daily_cycle(include_core_node=True)

    assert cycle.dream is dream_result
    assert cycle.reflection is reflection_result
    assert cycle.direction is direction_result
    assert cycle.journal is journal_result
    assert cycle.output is output_result
    assert cycle.core_node is core_result
    assert cycle.archetype_weights.weights["Strategist"] == 1.2
    assert cycle.errors and "adapt_resonance: skipped" in cycle.errors


def test_chat_uses_memory_context_and_logs(tmp_path, monkeypatch):
    config = AgentConfig(chat_log_dir=tmp_path / "chat")
    agent = LucianAgent(config=config, client=StubClient("Lucian replies from the archive."))

    monkeypatch.setattr("lucian.agent.query", lambda q, k: ["fragment one", "fragment two"])
    recorded = []
    monkeypatch.setattr("lucian.agent.upsert", lambda doc_id, text, meta: recorded.append((doc_id, meta)))

    result = agent.chat("Tell me today's mood.", user="Tester")

    assert isinstance(result, ChatResult)
    assert "Lucian replies" in result.response
    assert result.memory_context == ("fragment one", "fragment two")
    chat_log = config.chat_log_dir / f"{result.timestamp.date()}_chat.md"
    assert chat_log.exists()
    assert recorded
