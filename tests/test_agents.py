"""Tests for agent logic (mocked LLM — no API key needed)."""
import json
from unittest.mock import patch
from agent_platform.agents.retrieval_agent import RetrievalAgent, Candidate
from agent_platform.agents.ranking_agent import RankingAgent


MOCK_RETRIEVAL_RESPONSE = json.dumps({
    "candidates": [
        {"name": "pytest", "category": "testing", "relevance_score": 95,
         "why_relevant": "Standard Python testing framework", "source": "knowledge_base"},
        {"name": "pytest-asyncio", "category": "testing", "relevance_score": 88,
         "why_relevant": "Required for async Python tests", "source": "knowledge_base"},
        {"name": "Hypothesis", "category": "testing", "relevance_score": 75,
         "why_relevant": "Property-based testing", "source": "knowledge_base"},
        {"name": "Locust", "category": "testing", "relevance_score": 65,
         "why_relevant": "Load testing", "source": "llm_training"},
        {"name": "Testcontainers", "category": "testing", "relevance_score": 60,
         "why_relevant": "Integration tests with real services", "source": "knowledge_base"},
        {"name": "unittest", "category": "testing", "relevance_score": 40,
         "why_relevant": "Built-in, but less powerful", "source": "llm_training"},
    ],
    "query_intent": "Find best testing framework for async Python API"
})

MOCK_RANKING_RESPONSE = json.dumps({
    "recommendation": {
        "name": "pytest",
        "confidence": 95,
        "reasoning": "pytest is the de facto standard for Python. With pytest-asyncio it handles async perfectly.",
        "tradeoffs": "Slightly more setup than unittest but pays off immediately.",
        "getting_started": "pip install pytest pytest-asyncio"
    },
    "alternatives": [
        {"name": "pytest-asyncio", "rank": 2, "when_to_choose": "Use alongside pytest, not instead of it."}
    ],
    "avoid": "unittest — too verbose for modern Python projects"
})


@patch("agent_platform.llm.client.call_claude")
def test_retrieval_agent_returns_candidates(mock_claude):
    mock_claude.return_value = (MOCK_RETRIEVAL_RESPONSE, 450.0)
    agent = RetrievalAgent(rag_retriever=None)
    result = agent.run("best testing framework for FastAPI")
    assert len(result.candidates) == 6
    assert result.candidates[0].name == "pytest"
    assert result.candidates[0].relevance_score == 95
    assert result.query_intent == "Find best testing framework for async Python API"


@patch("agent_platform.llm.client.call_claude")
def test_ranking_agent_returns_recommendation(mock_claude):
    mock_claude.return_value = (MOCK_RANKING_RESPONSE, 380.0)

    from agent_platform.agents.retrieval_agent import RetrievalResult
    mock_retrieval = RetrievalResult(
        candidates=[
            Candidate("pytest", "testing", 95, "Standard", "knowledge_base"),
        ],
        query_intent="Find testing framework",
        latency_ms=450.0,
    )
    agent = RankingAgent()
    result = agent.run(mock_retrieval, context={"stack": ["FastAPI"]})
    assert result.recommendation.name == "pytest"
    assert result.recommendation.confidence == 95
    assert "pip install" in result.recommendation.getting_started
