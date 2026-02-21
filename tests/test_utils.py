"""Tests for lucian.utils — shared helper functions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lucian.exceptions import APIKeyMissing
from lucian.utils import latest_file, load_client, load_weights, weighted_choice


# ── load_client ─────────────────────────────────────────────────────────────

class FakeOpenAI:
    pass


def test_load_client_returns_existing_client():
    existing = FakeOpenAI()
    assert load_client(existing) is existing


def test_load_client_raises_when_no_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(APIKeyMissing):
        load_client(None)


# ── latest_file ─────────────────────────────────────────────────────────────

def test_latest_file_returns_none_for_empty_dir(tmp_path):
    assert latest_file(tmp_path, "*.md") is None


def test_latest_file_returns_last_sorted(tmp_path):
    (tmp_path / "a_first.md").write_text("1")
    (tmp_path / "b_second.md").write_text("2")
    (tmp_path / "c_third.md").write_text("3")
    result = latest_file(tmp_path, "*.md")
    assert result is not None
    assert result.name == "c_third.md"


def test_latest_file_respects_pattern(tmp_path):
    (tmp_path / "dream.md").write_text("d")
    (tmp_path / "notes.txt").write_text("n")
    assert latest_file(tmp_path, "*.txt").name == "notes.txt"
    assert latest_file(tmp_path, "*.yaml") is None


# ── load_weights ────────────────────────────────────────────────────────────

def test_load_weights_returns_defaults_when_file_missing(tmp_path):
    defaults = {"A": 1.0, "B": 2.0}
    result = load_weights(tmp_path / "nonexistent.yaml", defaults)
    assert result == {"A": 1.0, "B": 2.0}
    # Must not mutate the input dict
    assert defaults == {"A": 1.0, "B": 2.0}


def test_load_weights_merges_from_yaml(tmp_path):
    path = tmp_path / "weights.yaml"
    path.write_text(yaml.safe_dump({"A": 3.5, "C": 0.7}))
    result = load_weights(path, {"A": 1.0, "B": 2.0})
    assert result == {"A": 3.5, "B": 2.0, "C": 0.7}


def test_load_weights_ignores_non_dict_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("just a string")
    result = load_weights(path, {"X": 1.0})
    assert result == {"X": 1.0}


def test_load_weights_does_not_mutate_defaults(tmp_path):
    path = tmp_path / "w.yaml"
    path.write_text(yaml.safe_dump({"A": 9.9}))
    defaults = {"A": 1.0}
    load_weights(path, defaults)
    assert defaults == {"A": 1.0}


# ── weighted_choice ─────────────────────────────────────────────────────────

def test_weighted_choice_returns_empty_for_empty_pool():
    assert weighted_choice([], [], k=3) == []


def test_weighted_choice_returns_k_items():
    result = weighted_choice(["a", "b"], [1.0, 1.0], k=5)
    assert len(result) == 5
    assert all(item in ("a", "b") for item in result)


def test_weighted_choice_single_item():
    result = weighted_choice(["only"], [1.0])
    assert result == ["only"]
