"""Tests for episodic and semantic memory."""
import pytest
from agent_platform.memory.episodic import EpisodicMemory


def test_episodic_add_and_retrieve():
    mem = EpisodicMemory()
    mem.add("session1", {"query": "best testing lib", "recommendation": "pytest", "confidence": 90})
    history = mem.get_context("session1")
    assert len(history) == 1
    assert history[0]["recommendation"] == "pytest"


def test_episodic_max_turns():
    mem = EpisodicMemory(max_turns=3)
    for i in range(5):
        mem.add("session1", {"query": f"query {i}", "recommendation": f"tool {i}", "confidence": 80})
    history = mem.get_context("session1")
    assert len(history) == 3
    assert history[-1]["recommendation"] == "tool 4"


def test_episodic_empty_session():
    mem = EpisodicMemory()
    assert mem.get_context("nonexistent") == []
    assert mem.get_last_recommendation("nonexistent") is None


def test_episodic_clear():
    mem = EpisodicMemory()
    mem.add("session1", {"query": "q", "recommendation": "tool", "confidence": 80})
    mem.clear("session1")
    assert mem.get_context("session1") == []


def test_episodic_summary():
    mem = EpisodicMemory()
    mem.add("session1", {"query": "testing lib", "recommendation": "pytest", "confidence": 92})
    summary = mem.summary("session1")
    assert "pytest" in summary
    assert "session1" in summary
