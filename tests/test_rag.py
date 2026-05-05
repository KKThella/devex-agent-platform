"""Tests for RAG retriever (uses in-memory ChromaDB — no disk)."""
from agent_platform.rag.knowledge_base import KNOWLEDGE_BASE


def test_knowledge_base_has_entries():
    assert len(KNOWLEDGE_BASE) > 10


def test_knowledge_base_structure():
    for doc in KNOWLEDGE_BASE:
        assert "text" in doc
        assert "category" in doc
        assert "tool" in doc
        assert len(doc["text"]) > 10


def test_knowledge_base_categories():
    categories = {doc["category"] for doc in KNOWLEDGE_BASE}
    expected = {"observability", "testing", "framework", "database", "infra", "security"}
    assert expected.issubset(categories)
