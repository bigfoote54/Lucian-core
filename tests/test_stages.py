import os
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

import adapt_resonance
import adapt_weights
import append_journal
import generate_archetypal_dream as gad
import generate_direction as gd
import generate_output as go
import lucian.utils as utils
import reflect as rf


class DummyChatClient:
    def __init__(self, content: str):
        self._content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._content))],
            usage=SimpleNamespace(total_tokens=kwargs.get("max_tokens", 0)),
        )


@pytest.fixture(autouse=True)
def reset_random(monkeypatch):
    monkeypatch.setattr(utils, "weighted_choice", lambda values, weights, k=1: [list(values)[0]] * k)


def test_generate_archetypal_dream_writes_structured_dream(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(gad, "query", lambda q, k: ["memory fragment"])

    def fake_upsert(doc_id, text, meta):
        calls.append((doc_id, text, meta))

    monkeypatch.setattr(gad, "upsert", fake_upsert)

    timestamp = datetime(2025, 1, 2, 3, 4, 5)
    client = DummyChatClient(
        "Resonance Tag: Curiosity · Wonder\nA mirrored corridor stretches.\nSilver thoughts echo.\nNew roots take hold."
    )

    result = gad.generate_archetypal_dream(timestamp=timestamp, client=client, out_dir=tmp_path, include_embedding=True)

    assert result.path.exists()
    content = result.path.read_text()
    assert "Resonance Tag: Curiosity · Wonder" in content
    assert len(result.paragraphs) == 3
    assert calls and calls[0][0] == result.path.stem


def test_generate_direction_returns_directive(tmp_path, monkeypatch):
    fixed_now = datetime(2025, 1, 3, 9, 0, 0)
    monkeypatch.setattr(gd, "datetime", SimpleNamespace(now=lambda: fixed_now))

    # Patch the module-level constants that reference DREAMS_DIR / DIRECTION_DIR
    import lucian.constants as consts
    monkeypatch.setattr(consts, "DREAMS_DIR", tmp_path / "memory" / "dreams")
    monkeypatch.setattr(consts, "DIRECTION_DIR", tmp_path / "memory" / "direction")
    # The generate_direction module imports these at the top level, so also patch its references
    monkeypatch.setattr(gd, "DREAMS_DIR", tmp_path / "memory" / "dreams")
    monkeypatch.setattr(gd, "DIRECTION_DIR", tmp_path / "memory" / "direction")

    dreams_dir = tmp_path / "memory" / "dreams"
    dreams_dir.mkdir(parents=True)
    direction_dir = tmp_path / "memory" / "direction"
    direction_dir.mkdir(parents=True)

    dream_path = dreams_dir / f"{fixed_now.strftime('%Y-%m-%d')}_01-00-00_archetypal_dream.md"
    dream_path.write_text(
        "💭 Lucian Archetypal Dream — 2025-01-03\n\nResonance Tag: Curiosity · Wonder\n\n## Dream\n\nDream fragment."
    )

    client = DummyChatClient("Follow the quiet curiosity toward a new perspective.")

    result = gd.generate_direction(client=client)

    assert result.path.exists()
    text = result.path.read_text()
    assert "Follow the quiet curiosity" in text
    assert result.resonance_tags
    assert result.path.parent == direction_dir


def test_generate_reflection_inserts_alignment_when_missing(tmp_path, monkeypatch):
    import lucian.constants as consts
    monkeypatch.setattr(consts, "DREAMS_DIR", tmp_path / "memory" / "dreams")
    monkeypatch.setattr(consts, "DIRECTION_DIR", tmp_path / "memory" / "direction")
    monkeypatch.setattr(consts, "REFLECTION_DIR", tmp_path / "memory" / "reflection")
    monkeypatch.setattr(rf, "DREAMS_DIR", tmp_path / "memory" / "dreams")
    monkeypatch.setattr(rf, "DIRECTION_DIR", tmp_path / "memory" / "direction")
    monkeypatch.setattr(rf, "REFLECTION_DIR", tmp_path / "memory" / "reflection")

    dreams_dir = tmp_path / "memory" / "dreams"
    dreams_dir.mkdir(parents=True)
    direction_dir = tmp_path / "memory" / "direction"
    direction_dir.mkdir(parents=True)
    reflection_dir = tmp_path / "memory" / "reflection"
    reflection_dir.mkdir(parents=True)

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    dream_file = dreams_dir / f"{today.strftime('%Y-%m-%d')}_05-00-00_archetypal_dream.md"
    dream_file.write_text("## Dream\n\nA lucid dream fragment.")

    directive_file = direction_dir / f"{yesterday.strftime('%Y-%m-%d')}_direction.md"
    directive_file.write_text("## Directive\n\nStay curious.")

    recorded = []
    monkeypatch.setattr(rf, "upsert", lambda doc_id, text, meta: recorded.append((doc_id, meta)))

    client = DummyChatClient("The dream wrestled the directive but offered no explicit tag.")

    result = rf.generate_reflection(client=client)

    assert result.path.exists()
    output = result.path.read_text()
    assert "Alignment:" in output
    assert recorded and recorded[0][0] == result.path.stem


def test_adapt_archetype_weights_updates_bias_file(tmp_path):
    adapt_weights.weekly_dir = tmp_path / "weekly"
    adapt_weights.weekly_dir.mkdir(parents=True)
    adapt_weights.bias_path = tmp_path / "config" / "archetype_bias.yaml"
    adapt_weights.bias_path.parent.mkdir(parents=True)

    report = adapt_weights.weekly_dir / "2025-01-03_report.md"
    report.write_text(
        "# 📊 Lucian Weekly Report\n\n"
        "* **Strategist**: 5\n"
        "* **Idealist**: 3\n"
        "* **Shadow**: 2\n"
        "* **Child**: 2\n"
    )

    result = adapt_weights.adapt_archetype_weights()

    assert result.updated
    assert adapt_weights.bias_path.exists()
    data = adapt_weights.bias_path.read_text()
    assert "Strategist" in data


def test_adapt_resonance_weights_writes_tag_bias(tmp_path, monkeypatch):
    monkeypatch.setattr(adapt_resonance, "DREAMS_DIR", tmp_path / "memory" / "dreams")
    dreams_dir = tmp_path / "memory" / "dreams"
    dreams_dir.mkdir(parents=True, exist_ok=True)

    for i in range(4):
        dream_file = dreams_dir / f"2025-01-0{i+1}_dream.md"
        dream_file.write_text(f"Resonance Tag: Curiosity · Wonder{i}")
        os.utime(dream_file, None)

    adapt_resonance.TAGS_PATH = tmp_path / "config" / "tag_weights.yaml"
    adapt_resonance.TAGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    result = adapt_resonance.adapt_resonance_weights()

    assert result.updated
    text = adapt_resonance.TAGS_PATH.read_text()
    assert "Curiosity" in text


def test_run_journal_cycle_persists_entry(tmp_path, monkeypatch):
    append_journal.JOURNAL_DIR = tmp_path / "journal"
    append_journal.MOOD_FILE = tmp_path / "dreams" / "_latest_mood.txt"
    append_journal.MOOD_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = "Mood: Serene · Reflective\nI drifted through the archive."
    monkeypatch.setattr(append_journal, "generate_journal_entry", lambda client=None, model=None: entry)

    result = append_journal.run_journal_cycle()

    assert result.path and result.path.exists()
    assert append_journal.MOOD_FILE.read_text() == entry.splitlines()[0]
    journal_text = result.path.read_text()
    assert "I drifted through the archive." in journal_text


def test_generate_daily_output_combines_latest_docs(tmp_path):
    dream_path = tmp_path / "dream.md"
    dream_path.write_text(
        "# Dream Doc\nResonance: Strong\nResonance Tag: Curiosity\n\n## Dream\n\nA threading of possibilities."
    )

    direction_path = tmp_path / "direction.md"
    direction_path.write_text("## Directive\n\nMove gently toward the unknown.")

    out_file = tmp_path / "lucian_output.md"
    result = go.generate_daily_output(dream_path=dream_path, direction_path=direction_path, out_path=out_file)

    assert result.path == out_file
    text = out_file.read_text()
    assert "Resonance Tag: Curiosity" in text
    assert "Move gently toward the unknown." in text
